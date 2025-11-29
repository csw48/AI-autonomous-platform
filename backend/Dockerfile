# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Tesseract language data
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-slk \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for Tesseract language data (en -> eng)
# Tesseract expects 'en' but Debian packages it as 'eng'
RUN ln -sf /usr/share/tesseract-ocr/5/tessdata/eng.traineddata \
           /usr/share/tesseract-ocr/5/tessdata/en.traineddata

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
