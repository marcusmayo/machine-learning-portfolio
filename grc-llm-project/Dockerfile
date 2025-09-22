FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch CPU version specifically
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy application files
COPY app/ ./app/
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Copy the working inference script (use the correct file name)
COPY src/test_compliance_model.py ./inference_engine.py

# Create outputs directory
RUN mkdir -p outputs

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["streamlit", "run", "app/streamlit_cloud_app.py", "--server.port=8501", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
