
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def model_fn(model_dir):
    """Load the model and tokenizer"""
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            device_map="auto" if torch.cuda.is_available() else None
        )
        return {"model": model, "tokenizer": tokenizer}
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def input_fn(request_body, request_content_type):
    """Parse input data"""
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        return input_data
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model_dict):
    """Generate prediction"""
    try:
        model = model_dict["model"]
        tokenizer = model_dict["tokenizer"]
        
        # Extract inputs and parameters
        inputs = input_data.get("inputs", "")
        parameters = input_data.get("parameters", {})
        
        # Default parameters
        max_new_tokens = parameters.get("max_new_tokens", 100)
        temperature = parameters.get("temperature", 0.7)
        do_sample = parameters.get("do_sample", True)
        
        # Tokenize input
        input_ids = tokenizer.encode(inputs, return_tensors="pt")
        
        # Generate response
        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        return {
            "generated_text": generated_text,
            "input_length": len(input_ids[0]),
            "output_length": len(output_ids[0])
        }
    
    except Exception as e:
        print(f"Error in prediction: {e}")
        return {"error": str(e), "generated_text": "Sorry, I encountered an error generating a response."}

def output_fn(prediction, accept):
    """Format the output"""
    if accept == "application/json":
        return json.dumps(prediction), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
