# Use lightweight base image
FROM python:3.9-slim-bullseye

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y torch && \
    pip install --no-cache-dir torch==1.13.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Copy application code
COPY . .

# Cleanup build dependencies
RUN apt-get purge -y --auto-remove build-essential && \
    rm -rf /root/.cache/pip

# Set environment variables
ENV PYTHONUNBUFFERED=1


# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]