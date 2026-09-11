// Configuration
const API_URL = 'http://localhost:5000/api';
let uploadedImage = null;
let compressedImageData = null;
let decompressedImageData = null;
let originalImageData = null;
let currentK = 16;
let currentMethod = 'bilinear';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const kSlider = document.getElementById('kSlider');
const kValue = document.getElementById('kValue');
const compressBtn = document.getElementById('compressBtn');
const decompressBtn = document.getElementById('decompressBtn');
const resetBtn = document.getElementById('resetBtn');
const originalImg = document.getElementById('originalImg');
const compressedImg = document.getElementById('compressedImg');
const decompressedImg = document.getElementById('decompressedImg');
const loadingSpinner = document.getElementById('loadingSpinner');
const loadingText = document.getElementById('loadingText');
const downloadSection = document.getElementById('downloadSection');
const downloadCompressed = document.getElementById('downloadCompressed');
const downloadDecompressed = document.getElementById('downloadDecompressed');
const colorPalette = document.getElementById('colorPalette');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Event Listeners
uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

kSlider.addEventListener('input', (e) => {
    currentK = parseInt(e.target.value);
    kValue.textContent = currentK;
});

document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const value = parseInt(btn.getAttribute('data-value'));
        kSlider.value = value;
        currentK = value;
        kValue.textContent = value;
    });
});

document.querySelectorAll('input[name="method"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentMethod = e.target.value;
    });
});

compressBtn.addEventListener('click', compressImage);
decompressBtn.addEventListener('click', decompressImage);
resetBtn.addEventListener('click', resetApp);

downloadCompressed.addEventListener('click', () => downloadImage(compressedImageData, 'compressed.png'));
downloadDecompressed.addEventListener('click', () => downloadImage(decompressedImageData, 'decompressed.png'));

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        showTab(tabName);
    });
});

// Functions
function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        originalImg.src = e.target.result;
        uploadedImage = file;
        originalImageData = e.target.result;
        compressBtn.disabled = false;
        decompressBtn.disabled = true;
        downloadSection.style.display = 'none';
        resetMetrics();
    };
    reader.readAsDataURL(file);
}

function showLoading(show = true, text = 'Processing...') {
    loadingSpinner.style.display = show ? 'flex' : 'none';
    loadingText.textContent = text;
}

async function compressImage() {
    if (!uploadedImage) {
        alert('Please upload an image first');
        return;
    }

    showLoading(true, 'Compressing image with K-Means...');
    
    try {
        const formData = new FormData();
        formData.append('file', uploadedImage);
        formData.append('k', currentK);

        const response = await fetch(`${API_URL}/compress`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Compression failed');
        }

        const data = await response.json();
        
        // Display compressed image
        compressedImg.src = data.image_base64;
        compressedImageData = data.image_base64;

        // Store metadata for decompression
        window.compressionMetadata = data.compression;
        window.compressedMetadata = data.metadata;

        // Update metrics
        updateMetrics({
            originalSize: data.compression.original_size_kb,
            compressedSize: data.compression.compressed_size_kb,
            compressionRatio: data.compression.compression_ratio,
            k: data.compression.k
        });

        // Display color palette
        displayColorPalette(data.metadata.centroids);

        decompressBtn.disabled = false;
        downloadSection.style.display = 'grid';
        downloadSection.style.gridTemplateColumns = 'repeat(2, 1fr)';

    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

async function decompressImage() {
    if (!compressedImageData) {
        alert('Please compress an image first');
        return;
    }

    showLoading(true, `Decompressing with ${currentMethod} interpolation...`);

    try {
        // Convert base64 to blob
        const base64Data = compressedImageData.split(',')[1];
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'image/png' });

        const formData = new FormData();
        formData.append('file', blob, 'compressed.png');
        formData.append('original_width', window.compressionMetadata.width);
        formData.append('original_height', window.compressionMetadata.height);
        formData.append('method', currentMethod);

        const response = await fetch(`${API_URL}/decompress`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Decompression failed');
        }

        const data = await response.json();
        
        // Display decompressed image
        decompressedImg.src = data.image_base64;
        decompressedImageData = data.image_base64;

        // Get quality metrics
        await getQualityMetrics();

        downloadSection.style.display = 'grid';

    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

async function getQualityMetrics() {
    if (!uploadedImage || !compressedImageData) return;

    showLoading(true, 'Calculating quality metrics...');

    try {
        const formData = new FormData();
        formData.append('file', uploadedImage);
        formData.append('k', currentK);
        formData.append('method', currentMethod);

        const response = await fetch(`${API_URL}/compare`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Metrics calculation failed');
        }

        const data = await response.json();
        
        // Update all metrics
        updateMetrics({
            originalSize: data.compression.original_size_kb,
            compressedSize: data.compression.compressed_size_kb,
            compressionRatio: data.compression.compression_ratio,
            k: data.compression.k,
            psnr: data.quality_metrics.psnr,
            ssim: data.quality_metrics.ssim,
            mse: data.quality_metrics.mse
        });

    } catch (error) {
        console.error('Error calculating metrics:', error);
    } finally {
        showLoading(false);
    }
}

function updateMetrics(metrics) {
    if (metrics.originalSize !== undefined) {
        document.getElementById('originalSizeValue').textContent = `${metrics.originalSize} KB`;
    }
    if (metrics.compressedSize !== undefined) {
        document.getElementById('compressedSizeValue').textContent = `${metrics.compressedSize} KB`;
    }
    if (metrics.compressionRatio !== undefined) {
        document.getElementById('compressionRatioValue').textContent = `${metrics.compressionRatio}%`;
    }
    if (metrics.psnr !== undefined) {
        document.getElementById('psnrValue').textContent = metrics.psnr;
    }
    if (metrics.ssim !== undefined) {
        document.getElementById('ssimValue').textContent = metrics.ssim;
    }
    if (metrics.mse !== undefined) {
        document.getElementById('mseValue').textContent = metrics.mse;
    }
}

function resetMetrics() {
    document.getElementById('originalSizeValue').textContent = '-';
    document.getElementById('compressedSizeValue').textContent = '-';
    document.getElementById('compressionRatioValue').textContent = '-';
    document.getElementById('psnrValue').textContent = '-';
    document.getElementById('ssimValue').textContent = '-';
    document.getElementById('mseValue').textContent = '-';
    colorPalette.innerHTML = '';
}

function displayColorPalette(centroids) {
    colorPalette.innerHTML = '';
    
    if (!Array.isArray(centroids) || centroids.length === 0) {
        return;
    }

    centroids.forEach((color, index) => {
        const colorBox = document.createElement('div');
        colorBox.className = 'color-box';
        
        let rgbColor;
        if (Array.isArray(color)) {
            rgbColor = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
        } else {
            rgbColor = `rgb(${color}, ${color}, ${color})`;
        }
        
        colorBox.style.backgroundColor = rgbColor;
        colorBox.title = rgbColor;
        
        colorPalette.appendChild(colorBox);
    });
}

function showTab(tabName) {
    // Hide all tabs
    tabContents.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    event.target.closest('.tab-btn').classList.add('active');
}

function downloadImage(imageData, filename) {
    if (!imageData) {
        alert('No image to download');
        return;
    }

    const link = document.createElement('a');
    link.href = imageData;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function resetApp() {
    // Reset all state
    uploadedImage = null;
    compressedImageData = null;
    decompressedImageData = null;
    originalImageData = null;
    
    // Reset UI
    fileInput.value = '';
    kSlider.value = 16;
    currentK = 16;
    kValue.textContent = '16';
    
    originalImg.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23f3f4f6" width="400" height="400"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%2399a3a4"%3ENo image loaded%3C/text%3E%3C/svg%3E';
    compressedImg.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23f3f4f6" width="400" height="400"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%2399a3a4"%3ECompress to see result%3C/text%3E%3C/svg%3E';
    decompressedImg.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23f3f4f6" width="400" height="400"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%2399a3a4"%3EDecompress to see result%3C/text%3E%3C/svg%3E';
    
    compressBtn.disabled = true;
    decompressBtn.disabled = true;
    downloadSection.style.display = 'none';
    
    resetMetrics();
    colorPalette.innerHTML = '';
    
    // Switch to preview tab
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelector('[data-tab="preview"]').classList.add('active');
    document.getElementById('preview').classList.add('active');
}

// Initialize
console.log('Image Compression App initialized');
console.log(`API URL: ${API_URL}`);
