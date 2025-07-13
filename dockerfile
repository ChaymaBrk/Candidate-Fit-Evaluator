FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for pdfplumber, faiss, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements without downloading models
COPY requirements.txt .

# Install Python packages without dependencies
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Optionally: manually install smaller subset of dependencies
RUN pip install --no-cache-dir fastapi uvicorn numpy pydantic python-dotenv

# Now copy the app
COPY . .

# Expose port and set default command
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
