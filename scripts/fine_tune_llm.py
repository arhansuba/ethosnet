import os
import argparse
import json
from typing import List, Dict, Any
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import load_dataset
from tqdm import tqdm
import wandb
from sklearn.model_selection import train_test_split

# Configuration
DEFAULT_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
DEFAULT_DATASET_PATH = "ethosnet_ethics_dataset.jsonl"
DEFAULT_OUTPUT_DIR = "./fine_tuned_model"
MAX_LENGTH = 512

class EthicsDataset(Dataset):
    def __init__(self, data: List[Dict[str, str]], tokenizer, max_length: int):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        prompt = f"Scenario: {item['scenario']}\nQuestion: {item['question']}\nAnswer:"
        text = f"{prompt} {item['answer']}"
        
        encodings = self.tokenizer(text, truncation=True, padding="max_length", max_length=self.max_length)
        
        return {
            "input_ids": torch.tensor(encodings["input_ids"]),
            "attention_mask": torch.tensor(encodings["attention_mask"]),
            "labels": torch.tensor(encodings["input_ids"])
        }

def load_ethics_dataset(file_path: str) -> List[Dict[str, str]]:
    """Load the ethics dataset from a JSONL file."""
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def prepare_datasets(data: List[Dict[str, str]], tokenizer, max_length: int):
    """Prepare train and validation datasets."""
    train_data, val_data = train_test_split(data, test_size=0.1, random_state=42)
    return (
        EthicsDataset(train_data, tokenizer, max_length),
        EthicsDataset(val_data, tokenizer, max_length)
    )

def fine_tune_model(
    model_name: str,
    dataset_path: str,
    output_dir: str,
    batch_size: int = 4,
    num_epochs: int = 3,
    learning_rate: float = 2e-5,
    weight_decay: float = 0.01,
    max_grad_norm: float = 1.0,
    warmup_steps: int = 500,
):
    """Fine-tune the LLM on the ethics dataset."""
    
    # Initialize wandb for experiment tracking
    wandb.init(project="ethosnet-llm-fine-tuning", name=f"fine-tune-{model_name.split('/')[-1]}")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # Prepare datasets
    data = load_ethics_dataset(dataset_path)
    train_dataset, val_dataset = prepare_datasets(data, tokenizer, MAX_LENGTH)
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=warmup_steps,
        weight_decay=weight_decay,
        logging_dir='./logs',
        logging_steps=100,
        evaluation_strategy="steps",
        eval_steps=500,
        save_steps=1000,
        learning_rate=learning_rate,
        max_grad_norm=max_grad_norm,
        report_to="wandb",
    )
    
    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    
    # Start fine-tuning
    print("Starting fine-tuning process...")
    trainer.train()
    
    # Save the fine-tuned model
    print(f"Saving fine-tuned model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # End wandb run
    wandb.finish()

def evaluate_model(model_path: str, test_data_path: str):
    """Evaluate the fine-tuned model on a test dataset."""
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    
    test_data = load_ethics_dataset(test_data_path)
    correct = 0
    total = len(test_data)
    
    model.eval()
    with torch.no_grad():
        for item in tqdm(test_data, desc="Evaluating"):
            prompt = f"Scenario: {item['scenario']}\nQuestion: {item['question']}\nAnswer:"
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)
            outputs = model.generate(**inputs, max_new_tokens=50)
            generated_answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if item['answer'].lower() in generated_answer.lower():
                correct += 1
    
    accuracy = correct / total
    print(f"Model Accuracy: {accuracy:.2f}")
    return accuracy

def main():
    parser = argparse.ArgumentParser(description="Fine-tune LLM for EthosNet")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Base model to fine-tune")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_PATH, help="Path to the ethics dataset")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Output directory for fine-tuned model")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for training")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--test-data", help="Path to test dataset for evaluation")
    args = parser.parse_args()

    fine_tune_model(
        model_name=args.model,
        dataset_path=args.dataset,
        output_dir=args.output,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        learning_rate=args.learning_rate
    )

    if args.test_data:
        evaluate_model(args.output, args.test_data)

if __name__ == "__main__":
    main()