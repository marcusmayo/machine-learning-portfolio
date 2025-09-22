FROM python:3.9-slim

WORKDIR /app

# Copy application files
COPY . .

# Install dependencies including OpenAI
RUN pip install --no-cache-dir streamlit==1.29.0 numpy python-dotenv openai

# Copy .env file if it exists
COPY .env* ./

# Run enhanced app with proper settings
CMD ["streamlit", "run", "app/enhanced_app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--browser.serverAddress=localhost", \
     "--browser.gatherUsageStats=false", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
