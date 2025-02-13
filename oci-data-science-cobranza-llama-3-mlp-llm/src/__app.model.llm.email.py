from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import pandas as pd
import gc
import warnings

# Redirigir advertencias a un archivo para evitar que se muestren en la consola
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# Limpiar memoria GPU
torch.cuda.empty_cache()
gc.collect()

# Autenticar usando tu token de Hugging Face
from huggingface_hub import login
login("****************************", add_to_git_credential=True)

# Nombre del modelo en Hugging Face
model_name = "gradientai/Llama-3-8B-Instruct-Gradient-1048k"

# Verificar si CUDA está disponible y usar GPU si es posible
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Cargar el modelo y el tokenizador desde Hugging Face
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

# Configurar pad_token_id si no está presente
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# Leer el archivo CSV de clientes morosos
clientes = pd.read_csv('___model.customers.classification.csv')

# Filtrar los clientes que desean ser notificados por correo electrónico
morosos = clientes[clientes['communication_preference'] == 'email']

# Generar el mensaje plantilla solo una vez
prompt = (
    "Genera un mensaje en español amigable y conciso de cobranza para un cliente llamado {{name}} "
    "que debe ${{amount_owed}} y recordarle su fecha de pago que es el {{last_payment_date}}. "
    "El mensaje debe ser profesional y respetuoso, sin instrucciones adicionales."
)
inputs = tokenizer(prompt, return_tensors="pt").to(device)

# Añadir attention_mask para evitar advertencias
inputs['attention_mask'] = inputs['input_ids'].ne(tokenizer.pad_token_id).long().to(device)

print("\n[LLM]: Generando cuerpo del correo electronico un momento por favor...\n")

outputs = model.generate(
    inputs['input_ids'],
    attention_mask=inputs['attention_mask'],
    max_length=200,
    num_return_sequences=1,
    pad_token_id=tokenizer.eos_token_id  # Configurar pad_token_id explícitamente
)
message_template = tokenizer.decode(outputs[0], skip_special_tokens=True)

# Filtrar solo el cuerpo del mensaje
start_idx = message_template.find("Hola")
if start_idx != -1:
    message_template = message_template[start_idx:]

# Generar mensajes personalizados para los clientes morosos en español
mensajes = []
for index, row in morosos.iterrows():
    message = message_template.replace("{{name}}", row['name'])
    message = message.replace("{{amount_owed}}", f"${row['amount_owed']}")
    message = message.replace("{{last_payment_date}}", row['last_payment_date'])
    mensajes.append({'client_id': row['client_id'], 'name': row['name'], 'mensaje': message})

# Convertir la lista de mensajes a un DataFrame y guardar en un CSV
mensajes_df = pd.DataFrame(mensajes)
mensajes_df.to_csv('__model.llm.email.csv', index=False)

print("\n[LLM]: Se generaron los siguientes mensajes...\n")

print(mensajes_df)