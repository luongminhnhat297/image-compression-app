import numpy as np
from typing import Tuple, List
import io
from PIL import Image


class KMeans:
    """
    K-Means clustering algorithm implemented from scratch
    for image color quantization and compression
    """
    
    def __init__(self, k: int = 16, max_iterations: int = 100, random_state: int = 42):
        """
        Initialize K-Means clustering
        
        Args:
            k: Number of clusters (colors)
            max_iterations: Maximum number of iterations
            random_state: Random seed for reproducibility
        """
        self.k = k
        self.max_iterations = max_iterations
        self.random_state = random_state
        self.centroids = None
        self.labels = None
        self.inertia_history = []
        
    def initialize_centroids(self, data: np.ndarray) -> np.ndarray:
        """
        Initialize centroids using k-means++ algorithm
        
        Args:
            data: Input data of shape (n_samples, n_features)
            
        Returns:
            Initial centroids of shape (k, n_features)
        """
        np.random.seed(self.random_state)
        
        # Choose first centroid randomly
        n_samples = data.shape[0]
        first_idx = np.random.randint(n_samples)
        centroids = [data[first_idx]]
        
        # Choose remaining k-1 centroids
        for _ in range(self.k - 1):
            # Calculate distances from each point to nearest centroid
            distances = np.array([
                min([np.linalg.norm(x - c) for c in centroids])
                for x in data
            ])
            
            # Choose next centroid with probability proportional to distance squared
            probabilities = distances ** 2
            probabilities /= probabilities.sum()
            
            cumulative_probs = np.cumsum(probabilities)
            r = np.random.rand()
            next_idx = np.searchsorted(cumulative_probs, r)
            centroids.append(data[next_idx])
        
        return np.array(centroids)
    
    def assign_clusters(self, data: np.ndarray, centroids: np.ndarray) -> np.ndarray:
        """
        Assign each data point to the nearest centroid
        
        Args:
            data: Input data of shape (n_samples, n_features)
            centroids: Centroids of shape (k, n_features)
            
        Returns:
            Cluster labels of shape (n_samples,)
        """
        # Calculate distances to all centroids
        distances = np.zeros((data.shape[0], self.k))
        for i, centroid in enumerate(centroids):
            distances[:, i] = np.linalg.norm(data - centroid, axis=1)
        
        # Assign to nearest centroid
        labels = np.argmin(distances, axis=1)
        return labels
    
    def update_centroids(self, data: np.ndarray, labels: np.ndarray) -> np.ndarray:
        """
        Update centroids as the mean of assigned points
        
        Args:
            data: Input data of shape (n_samples, n_features)
            labels: Cluster labels of shape (n_samples,)
            
        Returns:
            Updated centroids of shape (k, n_features)
        """
        new_centroids = np.zeros((self.k, data.shape[1]))
        for i in range(self.k):
            cluster_points = data[labels == i]
            if len(cluster_points) > 0:
                new_centroids[i] = cluster_points.mean(axis=0)
            else:
                # If cluster is empty, reinitialize randomly
                new_centroids[i] = data[np.random.randint(len(data))]
        
        return new_centroids
    
    def calculate_inertia(self, data: np.ndarray, labels: np.ndarray, centroids: np.ndarray) -> float:
        """
        Calculate sum of squared distances from points to their centroids
        
        Args:
            data: Input data
            labels: Cluster labels
            centroids: Centroids
            
        Returns:
            Inertia value
        """
        inertia = 0
        for i in range(self.k):
            cluster_points = data[labels == i]
            if len(cluster_points) > 0:
                inertia += np.sum((cluster_points - centroids[i]) ** 2)
        return inertia
    
    def fit(self, data: np.ndarray) -> 'KMeans':
        """
        Fit K-Means on the data
        
        Args:
            data: Input data of shape (n_samples, n_features)
            
        Returns:
            Self
        """
        # Initialize centroids
        self.centroids = self.initialize_centroids(data)
        
        # Iterate until convergence
        for iteration in range(self.max_iterations):
            # Assign clusters
            labels = self.assign_clusters(data, self.centroids)
            
            # Update centroids
            new_centroids = self.update_centroids(data, labels)
            
            # Calculate inertia
            inertia = self.calculate_inertia(data, labels, new_centroids)
            self.inertia_history.append(inertia)
            
            # Check for convergence
            if np.allclose(self.centroids, new_centroids):
                self.centroids = new_centroids
                self.labels = labels
                break
            
            self.centroids = new_centroids
        
        self.labels = labels
        return self
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for new data
        
        Args:
            data: Input data
            
        Returns:
            Cluster labels
        """
        return self.assign_clusters(data, self.centroids)
    
    def transform(self, data: np.ndarray) -> np.ndarray:
        """
        Transform data to centroid values
        
        Args:
            data: Input data
            
        Returns:
            Data transformed to centroids
        """
        labels = self.predict(data)
        return self.centroids[labels]


def compress_image(image_path: str, k: int = 16) -> Tuple[Image.Image, np.ndarray, np.ndarray]:
    """
    Compress an image using K-Means color quantization
    
    Args:
        image_path: Path to the image file or file-like object
        k: Number of colors to compress to
        
    Returns:
        Tuple of (compressed_image, original_data, centroids)
    """
    # Load image
    if isinstance(image_path, str):
        img = Image.open(image_path)
    else:
        img = Image.open(io.BytesIO(image_path))
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Store original shape
    original_shape = img.size  # (width, height)
    
    # Convert image to numpy array
    img_array = np.array(img)
    n_pixels = img_array.shape[0] * img_array.shape[1]
    
    # Reshape to (n_pixels, 3) for RGB
    pixels = img_array.reshape(-1, 3).astype(np.float32)
    
    # Apply K-Means
    kmeans = KMeans(k=k, max_iterations=100, random_state=42)
    kmeans.fit(pixels)
    
    # Get cluster labels and centroids
    labels = kmeans.labels
    centroids = kmeans.centroids.astype(np.uint8)
    
    # Create compressed image by mapping pixels to nearest centroid
    compressed_pixels = centroids[labels]
    compressed_img_array = compressed_pixels.reshape(img_array.shape)
    compressed_img = Image.fromarray(compressed_img_array.astype('uint8'))
    
    return compressed_img, img, centroids


def save_compressed_data(image: Image.Image, centroids: np.ndarray, output_path: str = None) -> Tuple[bytes, dict]:
    """
    Save compressed image and metadata
    
    Args:
        image: Compressed PIL Image
        centroids: Color centroids
        output_path: Optional path to save
        
    Returns:
        Tuple of (image_bytes, metadata_dict)
    """
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    image_bytes = img_byte_arr.getvalue()
    
    # Metadata
    metadata = {
        'k': len(centroids),
        'size': len(image_bytes),
        'width': image.width,
        'height': image.height,
        'centroids': centroids.tolist()
    }
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
    
    return image_bytes, metadata
