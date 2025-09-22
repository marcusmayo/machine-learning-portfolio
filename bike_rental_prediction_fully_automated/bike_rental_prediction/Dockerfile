FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch flask numpy scikit-learn pandas

# Copy application files
COPY app/ ./app/
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/

# Expose port
EXPOSE 1234

# Run the Flask app instead of MLflow
CMD ["python", "app/serve.py"]
