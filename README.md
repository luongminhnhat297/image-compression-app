# Image Compression with K-Means

A web application for compressing and decompressing images using the K-Means clustering algorithm. This project demonstrates image color quantization and interpolation techniques.

## Features

✨ **Core Features:**
- **K-Means Compression**: Reduce colors using K-Means clustering algorithm (implemented from scratch)
- **Multiple Decompression Methods**: 
  - Bilinear Interpolation (fast)
  - Cubic Interpolation (better quality)
- **Quality Metrics**: PSNR, SSIM, MSE calculation
- **Color Palette Visualization**: See the colors selected by K-Means
- **Compression Statistics**: File size reduction, compression ratio
- **Drag & Drop Upload**: Easy image upload interface
- **Multiple Format Support**: PNG, JPG, JPEG, BMP, GIF, WebP

🎨 **UI Features:**
- Beautiful, responsive design using Tailwind CSS
- Real-time preview of compression results
- Multiple tabs: Preview, Metrics, Color Palette
- Quick presets (Low, Medium, High quality)
- Download compressed/decompressed images

## Project Structure

```
image-compression-app/
├── backend/
│   ├── app.py                    # Flask backend application
│   ├── requirements.txt          # Python dependencies
│   └── algorithms/
│       ├── __init__.py
│       ├── kmeans.py            # K-Means implementation
│       └── interpolation.py      # Upsampling algorithms
├── frontend/
│   ├── index.html               # Main HTML file
│   └── script.js                # Frontend logic
├── docker-compose.yml           # Docker configuration
└── README.md                    # This file
```

## Installation & Setup

### Option 1: Using Docker (Recommended)

Prerequisites:
- Docker and Docker Compose installed

**Steps:**

```bash
# Clone the repository
git clone https://github.com/luongminhnhat297/image-compression-app.git
cd image-compression-app

# Start the application
docker-compose up --build

# Open browser and go to http://localhost:3000
```

### Option 2: Manual Setup

**Backend:**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
```

Server will start at `http://localhost:5000`

**Frontend:**

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Start a simple HTTP server
# Using Python 3:
python -m http.server 3000

# Or using Node.js (if installed):
npx serve -s . -l 3000
```

Open browser and go to `http://localhost:3000`

## Usage

1. **Upload Image**: Click or drag-drop an image to the upload area
2. **Select Compression Level**: 
   - Use the slider or preset buttons (Low/Medium/High)
   - Low = 8 colors, Medium = 16 colors, High = 64 colors
3. **Compress**: Click "Compress Image" to apply K-Means
4. **View Results**: 
   - Preview tab shows before/after images
   - Metrics tab shows compression statistics
   - Palette tab displays selected colors
5. **Decompress**: Choose interpolation method and click "Decompress Image"
6. **Download**: Download the compressed or decompressed image

## API Endpoints

### POST `/api/compress`
Compress an image using K-Means

**Request:**
```
Form Data:
- file: Image file
- k: Number of colors (2-256, default: 16)
```

**Response:**
```json
{
  "success": true,
  "compression": {
    "k": 16,
    "original_size_kb": 245.5,
    "compressed_size_kb": 45.2,
    "compression_ratio": 81.6,
    "width": 800,
    "height": 600
  },
  "image_base64": "data:image/png;base64,...",
  "metadata": {
    "k": 16,
    "centroids": [[255, 0, 0], [0, 255, 0], ...]
  }
}
```

### POST `/api/decompress`
Decompress a compressed image

**Request:**
```
Form Data:
- file: Compressed image file
- original_width: Original image width
- original_height: Original image height
- method: 'bilinear' or 'cubic'
```

**Response:**
```json
{
  "success": true,
  "decompression": {
    "method": "bilinear",
    "width": 800,
    "height": 600,
    "size_kb": 245.5
  },
  "image_base64": "data:image/png;base64,..."
}
```

### POST `/api/compare`
Compare original and decompressed images with quality metrics

**Request:**
```
Form Data:
- file: Original image file
- k: Number of colors
- method: Decompression method
```

**Response:**
```json
{
  "success": true,
  "compression": {...},
  "decompression": {...},
  "quality_metrics": {
    "psnr": 28.45,
    "ssim": 0.8921,
    "mse": 45.23
  },
  "images": {
    "original": "data:image/png;base64,...",
    "compressed": "data:image/png;base64,...",
    "decompressed": "data:image/png;base64,..."
  }
}
```

## Algorithm Details

### K-Means Clustering
- **K-Means++ Initialization**: Improved initial centroid selection
- **Euclidean Distance**: Distance metric for color space
- **Convergence**: Stops when centroids no longer change or max iterations reached
- **Time Complexity**: O(k × n × i) where k=clusters, n=pixels, i=iterations

### Bilinear Interpolation
- **Formula**: f(x,y) = (1-fx)(1-fy)f00 + fx(1-fy)f10 + (1-fx)fy f01 + fx·fy f11
- **Speed**: Fast, suitable for real-time processing
- **Quality**: Good for 2x upsampling

### Cubic Interpolation (Catmull-Rom)
- **Formula**: Uses 4×4 neighborhood instead of 2×2
- **Speed**: Slower but higher quality
- **Quality**: Better results for larger upsampling ratios

## Quality Metrics

- **PSNR (Peak Signal-to-Noise Ratio)**: Higher is better (typical: 20-40 dB)
- **SSIM (Structural Similarity Index)**: Measures perceived quality (0-1, higher is better)
- **MSE (Mean Squared Error)**: Average squared difference between pixels (lower is better)

## Performance Tips

1. **Use Bilinear for Speed**: If processing time matters more than quality
2. **Use Cubic for Quality**: If output image quality is more important
3. **Adjust K Value**: 
   - Low K (2-8): Extreme compression, blocky artifacts
   - Medium K (16-32): Good balance
   - High K (64+): Better quality, larger file size

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)

## Technologies Used

**Backend:**
- Flask 2.3.3
- NumPy 1.24.3
- Pillow 10.0.0 (Image processing)
- Flask-CORS (Cross-origin requests)

**Frontend:**
- HTML5
- Vanilla JavaScript (ES6+)
- Tailwind CSS 3
- Font Awesome 6 (Icons)

## Troubleshooting

### CORS Error
If you get CORS errors, make sure:
1. Backend is running on http://localhost:5000
2. Frontend is making requests to correct API_URL
3. Check `frontend/script.js` line with `const API_URL = ...`

### Image not uploading
- Check file size (max 50MB)
- Verify file is a valid image
- Check browser console for errors

### Slow processing
- Use Bilinear interpolation instead of Cubic
- Try lower K value for faster compression
- Reduce image size before uploading

## Educational Value

This project is ideal for:
- Learning K-Means clustering algorithm
- Understanding image compression techniques
- Studying interpolation methods
- Image processing fundamentals
- Web application development

## License

This project is open source and available under the MIT License.

## Author

Developed for the AI Internship course on image processing and machine learning.

## Support

For issues or questions, please create an issue in the GitHub repository.

---

**Happy Compressing! 🎨📸**
