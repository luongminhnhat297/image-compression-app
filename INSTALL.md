# Image Compression with K-Means - Installation Guide

## Quick Start (Docker)

```bash
git clone https://github.com/luongminhnhat297/image-compression-app.git
cd image-compression-app
docker-compose up --build
# Open http://localhost:3000
```

## Manual Installation

### Backend Setup

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

**Backend runs on:** http://localhost:5000

### Frontend Setup

```bash
cd frontend

# Option 1: Using Python
python -m http.server 3000

# Option 2: Using Node.js
npx serve -s . -l 3000

# Option 3: Using Live Server (VS Code extension)
# Just open the folder and click "Go Live"
```

**Frontend runs on:** http://localhost:3000

## Requirements

- Python 3.8+
- pip (Python package manager)
- Node.js 14+ (for Docker or npx commands)
- Modern web browser

## Troubleshooting

**Backend not starting:**
- Ensure Python 3.8+ is installed
- Check all dependencies: `pip install -r requirements.txt`
- Make sure port 5000 is available

**Frontend not loading:**
- Check console for CORS errors
- Ensure backend is running
- Try disabling browser cache

**Image processing errors:**
- Upload smaller images first to test
- Check file format (PNG, JPG, etc.)
- Review browser console for detailed error messages

## File Structure

```
backend/
├── app.py                 # Main Flask app
├── requirements.txt       # Dependencies
├── Dockerfile            # Docker configuration
└── algorithms/
    ├── kmeans.py         # K-Means algorithm
    └── interpolation.py  # Interpolation methods

frontend/
├── index.html            # Main page
└── script.js             # JavaScript logic
```

**Enjoy using the Image Compression App! 🚀**