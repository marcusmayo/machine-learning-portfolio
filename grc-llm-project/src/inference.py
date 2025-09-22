import torch
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import os

def model_fn(model_dir):
    """Load model for SageMaker inference"""
    
    base_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        dtype=torch.float32
    )
    
    # Load LoRA adapter
    adapter_path = os.path.join(model_dir, "model")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    
    return {"model": model, "tokenizer": tokenizer}

def input_fn(request_body, request_content_type):
    """Parse input for inference"""
    
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        return input_data
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model_dict):
    """Generate compliance answer"""
    
    model = model_dict["model"]
    tokenizer = model_dict["tokenizer"]
    
    question = input_data.get("question", "")
    max_length = input_data.get("max_length", 200)
    temperature = input_data.get("temperature", 0.7)
    
    prompt = f"Question: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = response.split("Answer:")[-1].strip()
    
    return {"answer": answer}

def output_fn(prediction, accept):
    """Format output response"""
    
    if accept == "application/json":
        return json.dumps(prediction), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
