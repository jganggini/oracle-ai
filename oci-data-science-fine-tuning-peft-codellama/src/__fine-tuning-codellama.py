# 1. Instalar las bibliotecas necesarias
# !pip install accelerate peft bitsandbytes transformers trl pandas datasets

# 2. Importar los módulos necesarios
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig
from trl import SFTTrainer
import os

# advertencia del sistema de caché de huggingface_hub 
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 3. Cargar el dataset desde un archivo CSV
file_path = "___dataset_plsql.csv"
data = pd.read_csv(file_path)

# Convertir el DataFrame de pandas a un Dataset de Hugging Face
dataset = Dataset.from_pandas(data)

# 4. Configurar la cuantización de 4 bits
compute_dtype = getattr(torch, "float16")

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=False,
)

# 5. Cargar el modelo y el tokenizador
base_model = "meta-llama/CodeLlama-7b-hf"

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=quant_config,
    device_map={"": 0}
)
model.config.use_cache = False
model.config.pretraining_tp = 1

tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# 6. Configurar los parámetros de PEFT
peft_params = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=64,
    bias="none",
    task_type="CAUSAL_LM",
)

# 7. Configurar los parámetros de entrenamiento
training_params = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=1,
    optim="paged_adamw_32bit",
    save_steps=25,
    logging_steps=25,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=False,
    bf16=False,
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="constant",
    report_to="tensorboard"
)

# 8. Entrenar el modelo
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_params,
    dataset_text_field="text",  # Usando la columna correcta "text"
    max_seq_length=1024,
    tokenizer=tokenizer,
    args=training_params,
    packing=False,
)

trainer.train()

# 9. Guardar el modelo y el tokenizador
new_model = "CodeLlama-2-7b-chat-plsql"
trainer.model.save_pretrained(new_model)
trainer.tokenizer.save_pretrained(new_model)