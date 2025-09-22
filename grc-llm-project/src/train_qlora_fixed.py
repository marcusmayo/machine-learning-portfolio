import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
import json

def setup_model_and_tokenizer():
    """Setup TinyLlama model and tokenizer for CPU training"""
    
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model for CPU training
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.float32,  # Fixed: use dtype instead of torch_dtype
        device_map=None,      # Don't use auto device mapping for CPU
        low_cpu_mem_usage=True
    )
    
    return model, tokenizer

def setup_lora_config():
    """Setup LoRA configuration for CPU training"""
    
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]  # More target modules
    )
    
    return lora_config

def prepare_dataset(tokenizer, max_length=256):  # Shorter length for CPU
    """Prepare compliance dataset for training"""
    
    def format_instruction(sample):
        instruction = sample['instruction']
        output = sample['output']
        prompt = f"Question: {instruction}\nAnswer: {output}{tokenizer.eos_token}"
        return {"text": prompt}
    
    # Load datasets
    train_dataset = load_dataset('json', data_files='data/compliance_train.jsonl', split='train')
    eval_dataset = load_dataset('json', data_files='data/compliance_eval.jsonl', split='train')
    
    # Format datasets
    train_dataset = train_dataset.map(format_instruction, remove_columns=train_dataset.column_names)
    eval_dataset = eval_dataset.map(format_instruction, remove_columns=eval_dataset.column_names)
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=max_length,
            return_overflowing_tokens=False,
        )
    
    train_dataset = train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    eval_dataset = eval_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    
    return train_dataset, eval_dataset

def train_compliance_model():
    """Train TinyLlama with LoRA on compliance data (CPU optimized)"""
    
    print("🔧 Setting up model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer()
    
    print("🔧 Setting up LoRA configuration...")
    lora_config = setup_lora_config()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    print("🔧 Preparing datasets...")
    train_dataset, eval_dataset = prepare_dataset(tokenizer)
    
    print(f"📊 Training samples: {len(train_dataset)}")
    print(f"📊 Evaluation samples: {len(eval_dataset)}")
    
    # CPU-optimized training arguments
    training_args = TrainingArguments(
        output_dir="./outputs/compliance-tinyllama-lora",
        overwrite_output_dir=True,
        num_train_epochs=2,  # Reduced for faster training
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=2,
        warmup_steps=5,
        logging_steps=2,
        eval_steps=10,
        save_steps=20,
        eval_strategy="steps",  # Fixed: use eval_strategy instead of evaluation_strategy
        save_strategy="steps",
        load_best_model_at_end=False,  # Disable to avoid issues
        fp16=False,
        bf16=False,
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        logging_dir="./logs",
        report_to=[],  # Empty list instead of None
        run_name="compliance-tinyllama-lora",
        optim="adamw_torch",  # Use standard optimizer
        lr_scheduler_type="linear",
        learning_rate=2e-4
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    print("🚀 Starting training...")
    trainer.train()
    
    print("💾 Saving model...")
    trainer.save_model("./outputs/compliance-tinyllama-lora/final")
    tokenizer.save_pretrained("./outputs/compliance-tinyllama-lora/final")
    
    # Save training info
    training_info = {
        "model": "TinyLlama-1.1B-Chat-v1.0",
        "method": "LoRA (CPU optimized)",
        "dataset": "GRC Compliance Q&A",
        "samples": len(train_dataset),
        "epochs": 2,
        "lora_r": 8,
        "lora_alpha": 32,
        "status": "completed"
    }
    
    with open("./outputs/compliance-tinyllama-lora/training_info.json", "w") as f:
        json.dump(training_info, f, indent=2)
    
    print("✅ Training completed!")
    print("📁 Model saved to: ./outputs/compliance-tinyllama-lora/final")
    
    return model, tokenizer

if __name__ == "__main__":
    train_compliance_model()
