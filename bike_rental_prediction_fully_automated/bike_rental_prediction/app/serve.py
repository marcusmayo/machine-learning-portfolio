#!/usr/bin/env python3
from flask import Flask, request, jsonify
import torch
import torch.nn as nn
import numpy as np
import os
import json

app = Flask(__name__)

class BikeRentalModel(nn.Module):
    def __init__(self, input_size=53):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        return self.net(x)

# Initialize model
model = None

def load_model():
    """Load or initialize the model"""
    global model
    model = BikeRentalModel(53)
    
    model_path = "/app/models/latest_model.pt"
    if os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location='cpu')
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Could not load model weights: {e}")
    else:
        print(f"No model found at {model_path}, using randomly initialized model")
    
    model.eval()
    return model

# Load model on startup
model = load_model()

# IMPORTANT: Define root endpoint FIRST
@app.route('/', methods=['GET'])
def root():
    """Root endpoint - MUST be defined"""
    return jsonify({
        "message": "Bike Rental Prediction API",
        "version": "1.0",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /predict": "Make prediction"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/predict', methods=['POST'])
def predict():
    """Prediction endpoint"""
    try:
        if model is None:
            return jsonify({"error": "Model not loaded"}), 500
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get features
        features = data.get('features')
        if features is None:
            return jsonify({"error": "No features provided"}), 400
        
        # Convert to numpy array
        features = np.array(features, dtype=np.float32)
        
        # Validate feature count
        if len(features) != 53:
            return jsonify({
                "error": f"Expected 53 features, got {len(features)}"
            }), 400
        
        # Make prediction
        with torch.no_grad():
            input_tensor = torch.tensor(features).reshape(1, -1)
            prediction = model(input_tensor)
            prediction_value = float(prediction.item())
        
        return jsonify({
            "prediction": prediction_value,
            "status": "success"
        })
    
    except Exception as e:
        print(f"Error in predict: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# Add a catch-all for debugging
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "message": "Available endpoints: /, /health, /predict",
        "status": 404
    }), 404

if __name__ == '__main__':
    print(f"Starting Bike Rental Prediction API...")
    print(f"Model loaded: {model is not None}")
    print("Available endpoints:")
    print("  GET  / - API information")
    print("  GET  /health - Health check")
    print("  POST /predict - Make prediction")
    app.run(host='0.0.0.0', port=1234, debug=False)
