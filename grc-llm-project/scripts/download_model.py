#!/usr/bin/env python3
"""
GRC Compliance LLM - Model Download Script
Run this script to download the base model and setup the project
"""

import os
import sys
from pathlib import Path

def setup_model():
    """Download and setup the GRC Compliance LLM model"""
    
    print("Setting up GRC Compliance LLM...")
    print("=" * 40)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except ImportError:
        print("Installing required packages...")
        os.system("pip install transformers torch peft accelerate")
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    
    # Create output directory
    output_dir = Path("outputs/compliance-tinyllama-lora/final")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download base model
    print("Downloading TinyLlama base model...")
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        # Save locally
        tokenizer.save_pretrained(output_dir)
        model.save_pretrained(output_dir)
        
        print(f"Model saved to: {output_dir}")
        print("Setup complete! You can now run:")
        print("  streamlit run app/streamlit_compliance_app_improved.py")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("Please ensure you have internet connection and try again.")

if __name__ == "__main__":
    setup_model()
