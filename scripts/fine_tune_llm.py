import os
import argparse
from typing import Dict, Any

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model,
    TaskType,
)
import wandb

class EthicsDataset(Dataset):
    def __init__(self, data, tokenizer, max_length):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        prompt = f"Scenario: {item['scenario']}\nQuestion: {item['question']}\nAnswer:"
        text = f"{prompt} {item['answer']}"
        
        encodings = self.tokenizer(text, truncation=True, max_length=self.max_length, padding="max_length")
        encodings["labels"] = encodings["input_ids"].copy()
        
        return encodings

def load_ethics_dataset(data_path: str):
    return load_dataset("json", data_files=data_path)

def prepare_datasets(dataset, tokenizer, max_length, train_split=0.8):
    train_size = int(len(dataset) * train_split)
    train_dataset = EthicsDataset(dataset[:train_size], tokenizer, max_length)
    val_dataset = EthicsDataset(dataset[train_size:], tokenizer, max_length)
    return train_dataset, val_dataset

def create_peft_config(model):
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"]
    )
    return peft_config

def fine_tune_model(
    model_name: str,
    dataset_path: str,
    output_dir: str,
    max_length: int = 512,
    batch_size: int = 4,
    num_epochs: int = 3,
    learning_rate: float = 2e-5,
    weight_decay: float = 0.01,
    warmup_steps: int = 500,
    save_steps: int = 500,
    logging_steps: int = 100,
):
    # Initialize wandb
    wandb.init(project="ethosnet_llm_finetuning", config=locals())

    # Load model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Create and apply LoRA config
    peft_config = create_peft_config(model)
    model = get_peft_model(model, peft_config)

    # Load and prepare dataset
    dataset = load_ethics_dataset(dataset_path)
    train_dataset, val_dataset = prepare_datasets(dataset['train'], tokenizer, max_length)

    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        evaluation_strategy="steps",
        eval_steps=save_steps,
        logging_steps=logging_steps,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        fp16=True,
        bf16=False,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_steps=warmup_steps,
        save_steps=save_steps,
        save_total_limit=3,
        report_to="wandb",
    )

    # Set up trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    # Fine-tune the model
    trainer.train()

    # Save the fine-tuned model
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # End wandb run
    wandb.finish()

def evaluate_model(model_path: str, test_dataset_path: str):
    # Load fine-tuned model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    # Load test dataset
    test_dataset = load_ethics_dataset(test_dataset_path)
    test_dataset = EthicsDataset(test_dataset['train'], tokenizer, max_length=512)

    # Set up evaluation trainer
    eval_args = TrainingArguments(
        output_dir="./eval_results",
        do_train=False,
        do_eval=True,
        per_device_eval_batch_size=4,
        report_to="wandb",
    )

    eval_trainer = Trainer(
        model=model,
        args=eval_args,
        eval_dataset=test_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    # Evaluate the model
    eval_results = eval_trainer.evaluate()
    
    print("Evaluation Results:", eval_results)
    wandb.log({"eval_perplexity": eval_results["eval_perplexity"]})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune an LLM for EthosNet")
    parser.add_argument("--model", type=str, default="EleutherAI/gpt-neo-1.3B", help="Base model to fine-tune")
    parser.add_argument("--dataset", type=str, required=True, help="Path to the dataset JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for fine-tuned model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate for training")
    args = parser.parse_args()

    fine_tune_model(
        model_name=args.model,
        dataset_path=args.dataset,
        output_dir=args.output,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )

    evaluate_model(args.output, args.dataset)