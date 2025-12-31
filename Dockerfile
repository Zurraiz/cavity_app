# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY object_detector.py .
COPY index.html .
COPY best.pt .
COPY segment_best.pt .

# Expose port (Cloud Run will override this with PORT env var)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application with Gunicorn (production-grade WSGI server)
CMD ["gunicorn", "object_detector:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "300"]
