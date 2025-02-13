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
login("*******************", add_to_git_credential=True)

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

def generar_respuesta(prompt, max_length=50):
    print("\n[Agente LLM]: Interpretando un momento por favor...")
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    inputs['attention_mask'] = inputs['input_ids'].ne(tokenizer.pad_token_id).long().to(device)
    outputs = model.generate(
        inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        max_length=max_length,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.strip()

# Iniciar chat
def chat():
    while True:
        print("\n[Agente]: Hola, ¿cómo te llamas?")
        user_name = input("[Usuario]: Tu nombre: ").strip()

        # Validar entrada del usuario
        if not user_name:
            print("[Agente]: Por favor, ingrese un nombre válido.")
            continue

        # Buscar el cliente por nombre
        cliente = clientes[clientes['name'].str.contains(user_name, case=False, na=False)]
        
        if cliente.empty:
            print(f"[Agente]: No se encontró un cliente con el nombre {user_name}.")
            continuar = input("[Agente]: ¿Quieres intentar con otro nombre? (si/no): ").strip().lower()
            if continuar != 'si':
                break
            continue

        cliente_info = cliente.iloc[0]
        print(f"[Agente]: Hola {cliente_info['name']}, vamos a verificar tu estado de pago.")

        if cliente_info['predicted_default'] == 0:
            print("[Agente]: Estás al día con tus pagos. ¡Gracias por tu puntualidad!")
            return
        else:
            print(f"[Agente]: Tienes una deuda de ${cliente_info['amount_owed']}.")
            print(f"[Agente]: Debes realizar el pago antes del {cliente_info['last_payment_date']}.")

        while True:
            print(f"[Agente]: {cliente_info['name']}, ¿vas a realizar el pago de ${cliente_info['amount_owed']} antes del {cliente_info['last_payment_date']}? Responde 'sí' o 'no'.")
            respuesta_usuario = input("[Usuario]: Respuesta: ").strip().lower()

            if not respuesta_usuario:
                print("[Agente]: Por favor, ingrese una respuesta válida.")
                continue

            # Generar respuesta usando el modelo
            prompt = f"El usuario ingreso: {respuesta_usuario}. Interpreta si el usuario confirma el pago ('sí') o lo niega ('no')."
            interpretacion = generar_respuesta(prompt)
            confirmacion = 'sí' if 'sí' in interpretacion.lower() else 'no'

            # Guardar confirmación en un nuevo archivo CSV
            confirmaciones = pd.DataFrame([{
                'client_id': cliente_info['client_id'],
                'name': cliente_info['name'],
                'email': cliente_info['email'],
                'phone_number': cliente_info['phone_number'],
                'age': cliente_info['age'],
                'income': cliente_info['income'],
                'payment_history': cliente_info['payment_history'],
                'amount_owed': cliente_info['amount_owed'],
                'communication_preference': cliente_info['communication_preference'],
                'last_payment_date': cliente_info['last_payment_date'],
                'predicted_default': cliente_info['predicted_default'],
                'confirmacion': 'Sí' if confirmacion == 'sí' else 'No'
            }])

            confirmaciones.to_csv('_model.llm.chat.confirmaciones.csv', mode='a', index=False, header=False)
            print("\nTu respuesta ha sido registrada. ¡Gracias!")
            break

        continuar = input("[Agente]: ¿Hay algo más en lo que pueda ayudarte? (sí/no): ").strip().lower()
        if continuar != 'sí':
            break

if __name__ == "__main__":
    chat()