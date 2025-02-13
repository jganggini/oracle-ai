import warnings
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Silenciar advertencias específicas de FutureWarning y UserWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub.file_download")
warnings.filterwarnings("ignore", category=UserWarning, module="transformers.models.llama.modeling_llama")

# Nombre del modelo
model_name = "CodeLlama-2-7b-chat-plsql"

# Verificar si CUDA está disponible y usar GPU si es posible
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Cargar el modelo y el tokenizador desde Hugging Face
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

# Configurar el pipeline de generación de texto para usar el dispositivo adecuado
pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=200, truncation=True, device=0 if torch.cuda.is_available() else -1)

# Función para generar la respuesta del modelo
def chat_with_model(prompt, history=None):
    if history is None:
        history = []
    
    # Concatenar el historial de la conversación
    input_text = "<s>[INST] " + " [INST] ".join(history + [prompt]) + " [/INST]"
    
    # Generar la respuesta
    result = pipe(input_text)
    
    # Extraer la respuesta generada hasta la etiqueta [INST]
    generated_text = result[0]['generated_text']
    
    # Obtener el texto después de la última etiqueta [/INST]
    response = generated_text.split("[/INST]")[-1].strip()
    
    return response

# Bucle de chat interactivo
history = []
print("\n[Agente]: Hola, ¿Cuál es su consulta?")
while True:
    user_input = input("[User]: ")
    if user_input.lower() == "":
        break
    
    # Obtener la respuesta del modelo
    response = chat_with_model(user_input, history)
    print(f"[Agente]: {response}")
    
    # Actualizar el historial de la conversación
    history.append(user_input)
    history.append(response)