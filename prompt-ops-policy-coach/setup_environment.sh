#!/bin/bash
# Policy Coach Pro - Environment Setup Script

echo "🚀 Setting up Policy Coach Pro environment..."

# Check if we're in the right directory
if [[ ! -f "app/enhanced_app.py" ]]; then
    echo "❌ Error: Not in project directory or missing app files"
    echo "Run this script from ~/prompt-ops-policy-coach/"
    exit 1
fi

# Install required packages
echo "📦 Installing Python packages..."
pip install --user streamlit==1.29.0 numpy python-dotenv openai

# Verify installations
echo "🔍 Verifying installations..."
python -c "import streamlit, numpy, openai; print('✅ All packages installed successfully!')" || {
    echo "❌ Package installation failed"
    exit 1
}

# Check data files
echo "📊 Checking data files..."
if [[ -f "index/faiss/chunks.json" ]]; then
    echo "✅ Index files found"
else
    echo "⚠️  Index files missing. Running indexer..."
    python src/build_index_ultra_simple.py
fi

# Check .env file
if [[ -f ".env" ]]; then
    echo "✅ Environment file found"
else
    echo "⚠️  .env file missing. Creating template..."
    echo "# Add your OpenAI API key here" > .env
    echo "# OPENAI_API_KEY=sk-your-key-here" >> .env
    echo "📝 Edit .env file to add your OpenAI API key"
fi

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "🚀 To start the app:"
echo "   Streamlit: streamlit run app/enhanced_app.py --server.port 8501"
echo "   Docker:    docker run -d -p 8080:8080 --name policy-app policy-coach-production"
echo ""
