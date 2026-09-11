from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image
import numpy as np
from algorithms.kmeans import compress_image, save_compressed_data
from algorithms.interpolation import decompress_image, calculate_psnr, calculate_ssim

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size_mb(data):
    """Get size of data in MB"""
    return len(data) / (1024 * 1024)


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Image Compression API with K-Means',
        'version': '1.0.0',
        'endpoints': {
            'compress': 'POST /api/compress',
            'decompress': 'POST /api/decompress',
            'health': 'GET /api/health'
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/compress', methods=['POST'])
def compress():
    """
    Compress an image using K-Means color quantization
    
    Expected form data:
        - file: Image file
        - k: Number of colors (default: 16)
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Get k parameter
        k = request.form.get('k', 16, type=int)
        k = max(2, min(256, k))  # Clamp between 2 and 256
        
        # Read file
        file_data = file.read()
        file.seek(0)
        
        # Get original size
        original_img = Image.open(io.BytesIO(file_data))
        if original_img.mode != 'RGB':
            original_img = original_img.convert('RGB')
        original_size = len(file_data)
        
        # Compress image
        compressed_img, _, centroids = compress_image(io.BytesIO(file_data), k=k)
        
        # Save compressed image
        compressed_bytes, metadata = save_compressed_data(compressed_img, centroids)
        compressed_size = len(compressed_bytes)
        
        # Calculate compression ratio
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        # Return results
        return jsonify({
            'success': True,
            'compression': {
                'k': k,
                'original_size_kb': round(original_size / 1024, 2),
                'compressed_size_kb': round(compressed_size / 1024, 2),
                'compression_ratio': round(compression_ratio, 2),
                'width': metadata['width'],
                'height': metadata['height']
            },
            'image_base64': 'data:image/png;base64,' + __import__('base64').b64encode(compressed_bytes).decode(),
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/decompress', methods=['POST'])
def decompress():
    """
    Decompress a compressed image using interpolation
    
    Expected form data:
        - file: Compressed image file
        - original_width: Original image width
        - original_height: Original image height
        - method: Interpolation method ('bilinear' or 'cubic')
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get parameters
        original_width = request.form.get('original_width', type=int)
        original_height = request.form.get('original_height', type=int)
        method = request.form.get('method', 'bilinear')
        
        if not original_width or not original_height:
            return jsonify({'error': 'original_width and original_height required'}), 400
        
        # Read compressed image
        file_data = file.read()
        compressed_img = Image.open(io.BytesIO(file_data))
        
        if compressed_img.mode != 'RGB':
            compressed_img = compressed_img.convert('RGB')
        
        # Decompress using interpolation
        decompressed_img = decompress_image(compressed_img, original_width, original_height, method=method)
        
        # Save to bytes
        output_bytes = io.BytesIO()
        decompressed_img.save(output_bytes, format='PNG')
        output_bytes.seek(0)
        decompressed_bytes = output_bytes.getvalue()
        
        return jsonify({
            'success': True,
            'decompression': {
                'method': method,
                'width': decompressed_img.width,
                'height': decompressed_img.height,
                'size_kb': round(len(decompressed_bytes) / 1024, 2)
            },
            'image_base64': 'data:image/png;base64,' + __import__('base64').b64encode(decompressed_bytes).decode()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare():
    """
    Compare original and decompressed images with quality metrics
    
    Expected form data:
        - file: Original image file
        - k: Number of colors
        - method: Decompression method
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        k = request.form.get('k', 16, type=int)
        k = max(2, min(256, k))
        method = request.form.get('method', 'bilinear')
        
        # Read original image
        file_data = file.read()
        original_img = Image.open(io.BytesIO(file_data))
        if original_img.mode != 'RGB':
            original_img = original_img.convert('RGB')
        
        original_array = np.array(original_img)
        original_width, original_height = original_img.size
        original_size = len(file_data)
        
        # Compress
        compressed_img, _, centroids = compress_image(io.BytesIO(file_data), k=k)
        compressed_bytes, metadata = save_compressed_data(compressed_img, centroids)
        compressed_size = len(compressed_bytes)
        
        # Decompress
        decompressed_img = decompress_image(compressed_img, original_width, original_height, method=method)
        decompressed_array = np.array(decompressed_img)
        
        # Calculate metrics
        psnr = calculate_psnr(original_array, decompressed_array)
        ssim = calculate_ssim(original_img, decompressed_img)
        mse = np.mean((original_array.astype(np.float32) - decompressed_array.astype(np.float32)) ** 2)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        # Convert images to base64
        original_bytes = io.BytesIO()
        original_img.save(original_bytes, format='PNG')
        original_bytes.seek(0)
        original_b64 = __import__('base64').b64encode(original_bytes.getvalue()).decode()
        
        compressed_bytes_img = io.BytesIO()
        compressed_img.save(compressed_bytes_img, format='PNG')
        compressed_bytes_img.seek(0)
        compressed_b64 = __import__('base64').b64encode(compressed_bytes_img.getvalue()).decode()
        
        decompressed_bytes_img = io.BytesIO()
        decompressed_img.save(decompressed_bytes_img, format='PNG')
        decompressed_bytes_img.seek(0)
        decompressed_b64 = __import__('base64').b64encode(decompressed_bytes_img.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'compression': {
                'k': k,
                'original_size_kb': round(original_size / 1024, 2),
                'compressed_size_kb': round(compressed_size / 1024, 2),
                'compression_ratio': round(compression_ratio, 2)
            },
            'decompression': {
                'method': method,
                'width': decompressed_img.width,
                'height': decompressed_img.height
            },
            'quality_metrics': {
                'psnr': round(psnr, 2),
                'ssim': round(ssim, 4),
                'mse': round(mse, 2)
            },
            'images': {
                'original': 'data:image/png;base64,' + original_b64,
                'compressed': 'data:image/png;base64,' + compressed_b64,
                'decompressed': 'data:image/png;base64,' + decompressed_b64
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
