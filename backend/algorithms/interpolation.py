import numpy as np
from PIL import Image
import io
from typing import Tuple


def bilinear_interpolation(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Upsample image using bilinear interpolation
    
    Args:
        img: Input PIL Image
        target_width: Target width
        target_height: Target height
        
    Returns:
        Upsampled PIL Image
    """
    img_array = np.array(img).astype(np.float32)
    src_height, src_width = img_array.shape[:2]
    
    # Create output array
    if len(img_array.shape) == 3:  # Color image
        output = np.zeros((target_height, target_width, img_array.shape[2]), dtype=np.float32)
    else:  # Grayscale
        output = np.zeros((target_height, target_width), dtype=np.float32)
    
    # Calculate scaling factors
    scale_x = src_width / target_width
    scale_y = src_height / target_height
    
    for y in range(target_height):
        for x in range(target_width):
            # Map target coordinates to source coordinates
            src_x = x * scale_x
            src_y = y * scale_y
            
            # Get integer and fractional parts
            x0 = int(np.floor(src_x))
            x1 = min(x0 + 1, src_width - 1)
            y0 = int(np.floor(src_y))
            y1 = min(y0 + 1, src_height - 1)
            
            # Ensure coordinates are within bounds
            x0 = max(0, x0)
            y0 = max(0, y0)
            
            # Get fractional parts
            fx = src_x - x0
            fy = src_y - y0
            
            # Bilinear interpolation
            if len(img_array.shape) == 3:
                c00 = img_array[y0, x0]
                c01 = img_array[y0, x1]
                c10 = img_array[y1, x0]
                c11 = img_array[y1, x1]
                
                c0 = c00 * (1 - fx) + c01 * fx
                c1 = c10 * (1 - fx) + c11 * fx
                output[y, x] = c0 * (1 - fy) + c1 * fy
            else:
                c00 = img_array[y0, x0]
                c01 = img_array[y0, x1]
                c10 = img_array[y1, x0]
                c11 = img_array[y1, x1]
                
                c0 = c00 * (1 - fx) + c01 * fx
                c1 = c10 * (1 - fx) + c11 * fx
                output[y, x] = c0 * (1 - fy) + c1 * fy
    
    return Image.fromarray(output.astype(np.uint8))


def cubic_interpolation_kernel(x: float) -> float:
    """
    Cubic interpolation kernel (Catmull-Rom)
    
    Args:
        x: Distance from the point (should be in [-2, 2])
        
    Returns:
        Kernel value
    """
    x = abs(x)
    if x < 1:
        return 1 - 2 * x**2 + x**3
    elif x < 2:
        return -4 + 8 * x - 5 * x**2 + x**3
    else:
        return 0


def cubic_interpolation(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Upsample image using cubic (Catmull-Rom) interpolation
    
    Args:
        img: Input PIL Image
        target_width: Target width
        target_height: Target height
        
    Returns:
        Upsampled PIL Image
    """
    img_array = np.array(img).astype(np.float32)
    src_height, src_width = img_array.shape[:2]
    
    # Create output array
    if len(img_array.shape) == 3:  # Color image
        output = np.zeros((target_height, target_width, img_array.shape[2]), dtype=np.float32)
    else:  # Grayscale
        output = np.zeros((target_height, target_width), dtype=np.float32)
    
    # Calculate scaling factors
    scale_x = src_width / target_width
    scale_y = src_height / target_height
    
    for y in range(target_height):
        for x in range(target_width):
            # Map target coordinates to source coordinates
            src_x = x * scale_x
            src_y = y * scale_y
            
            # Get integer and fractional parts
            x_int = int(np.floor(src_x))
            y_int = int(np.floor(src_y))
            fx = src_x - x_int
            fy = src_y - y_int
            
            # Cubic interpolation
            if len(img_array.shape) == 3:
                result = np.zeros(img_array.shape[2], dtype=np.float32)
            else:
                result = 0
            
            # Get 4x4 neighborhood
            for j in range(-1, 3):
                for i in range(-1, 3):
                    # Ensure coordinates are within bounds
                    yi = max(0, min(src_height - 1, y_int + j))
                    xi = max(0, min(src_width - 1, x_int + i))
                    
                    # Get kernel values
                    kx = cubic_interpolation_kernel(i - fx)
                    ky = cubic_interpolation_kernel(j - fy)
                    
                    if len(img_array.shape) == 3:
                        result += img_array[yi, xi] * kx * ky
                    else:
                        result += img_array[yi, xi] * kx * ky
            
            output[y, x] = np.clip(result, 0, 255)
    
    return Image.fromarray(output.astype(np.uint8))


def decompress_image(compressed_img: Image.Image, target_width: int, target_height: int, 
                     method: str = 'bilinear') -> Image.Image:
    """
    Decompress (upsample) an image
    
    Args:
        compressed_img: Compressed PIL Image
        target_width: Target width (original width)
        target_height: Target height (original height)
        method: Interpolation method ('bilinear' or 'cubic')
        
    Returns:
        Decompressed PIL Image
    """
    if method == 'cubic':
        return cubic_interpolation(compressed_img, target_width, target_height)
    else:  # Default to bilinear
        return bilinear_interpolation(compressed_img, target_width, target_height)


def calculate_psnr(original: np.ndarray, compressed: np.ndarray) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR)
    
    Args:
        original: Original image array
        compressed: Compressed/decompressed image array
        
    Returns:
        PSNR value in dB
    """
    mse = np.mean((original.astype(np.float32) - compressed.astype(np.float32)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr


def calculate_ssim_channel(original: np.ndarray, compressed: np.ndarray, 
                           c: float = 6.5025) -> float:
    """
    Calculate SSIM for a single channel
    
    Args:
        original: Original channel array
        compressed: Compressed channel array
        c: Constant to avoid division by zero
        
    Returns:
        SSIM value
    """
    mu1 = original.mean()
    mu2 = compressed.mean()
    sigma1_sq = np.var(original)
    sigma2_sq = np.var(compressed)
    sigma12 = np.cov(original.flatten(), compressed.flatten())[0, 1]
    
    numerator = (2 * mu1 * mu2 + c) * (2 * sigma12 + c)
    denominator = (mu1**2 + mu2**2 + c) * (sigma1_sq + sigma2_sq + c)
    
    return numerator / denominator


def calculate_ssim(original: Image.Image, compressed: Image.Image) -> float:
    """
    Calculate Structural Similarity Index (SSIM)
    
    Args:
        original: Original PIL Image
        compressed: Compressed PIL Image
        
    Returns:
        SSIM value (0-1)
    """
    orig_arr = np.array(original).astype(np.float32)
    comp_arr = np.array(compressed).astype(np.float32)
    
    if len(orig_arr.shape) == 3:
        # Calculate SSIM for each channel
        ssim_values = []
        for i in range(orig_arr.shape[2]):
            ssim_values.append(calculate_ssim_channel(orig_arr[:, :, i], comp_arr[:, :, i]))
        return np.mean(ssim_values)
    else:
        return calculate_ssim_channel(orig_arr, comp_arr)
