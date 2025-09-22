#!/usr/bin/env python3
"""
Fixed model loading for transformers 4.35.0
Resolves TypeError: __init__() got an unexpected keyword argument 'dtype'
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

def load_trained_model(base_model_path="outputs/TinyLlama-1.1B-Chat-v1.0", 
                      adapter_path="outputs/compliance-tinyllama-lora/final"):
    """Load the base model and LoRA adapter with correct parameters"""
    
    print("Loading base model and tokenizer...")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load base model with correct parameters for transformers 4.35.0
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float32,  # Use torch_dtype instead of dtype
        device_map="cpu",           # Force CPU for consistency
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print(f"Base model loaded. Model type: {type(base_model)}")
    
    # Load LoRA adapter if it exists
    if os.path.exists(adapter_path):
        print(f"Loading LoRA adapter from {adapter_path}...")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        print("LoRA adapter loaded successfully!")
    else:
        print(f"No adapter found at {adapter_path}, using base model only")
        model = base_model
    
    return model, tokenizer

def test_compliance_questions():
    """Test the model with compliance questions"""
    
    model, tokenizer = load_trained_model()
    
    # Test questions
    questions = [
        "What does SOC 2 CC6.1 cover?",
        "Which ISO 27001 control covers access reviews?", 
        "Do we need encryption at rest for HIPAA?"
    ]
    
    print("\n" + "="*60)
    print("TESTING COMPLIANCE MODEL")
    print("="*60)
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        print("-" * 40)
        
        # Format the prompt properly
        prompt = f"<|system|>\nYou are a compliance expert. Answer questions about SOC 2, ISO 27001, and HIPAA controls.</s>\n<|user|>\n{question}</s>\n<|assistant|>\n"
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the assistant's response
        if "<|assistant|>" in response:
            answer = response.split("<|assistant|>")[-1].strip()
        else:
            answer = response[len(prompt):].strip()
            
        print(f"Answer: {answer}")
        print()

if __name__ == "__main__":
    test_compliance_questions()
