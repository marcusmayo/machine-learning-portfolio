import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

def load_model():
    """Load the trained compliance model"""
    base_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    adapter_path = "./outputs/compliance-tinyllama-lora/final"
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        dtype=torch.float32
    )
    
    model = PeftModel.from_pretrained(base_model, adapter_path)
    return model, tokenizer

def chat():
    """Interactive compliance chatbot"""
    print("🤖 GRC Compliance Chatbot - Ready!")
    print("Ask me about SOC 2, ISO 27001, or HIPAA compliance")
    print("Type 'exit' to quit\n")
    
    model, tokenizer = load_model()
    
    while True:
        question = input("💼 Your compliance question: ")
        
        if question.lower() in ['exit', 'quit', 'bye']:
            print("👋 Thanks for using GRC Compliance LLM!")
            break
        
        if not question.strip():
            continue
            
        prompt = f"Question: {question}\nAnswer:"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_length=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = response.split("Answer:")[-1].strip()
        
        print(f"🎯 Answer: {answer}\n")

if __name__ == "__main__":
    chat()
