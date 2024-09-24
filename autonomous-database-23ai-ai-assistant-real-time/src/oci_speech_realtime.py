import os
import asyncio
import pyaudio
from oci.config import from_file
from oci.ai_speech_realtime import RealtimeClient, RealtimeClientListener, RealtimeParameters
from dotenv import load_dotenv

# Configuración global
SAMPLE_RATE        = 16000
FORMAT             = pyaudio.paInt16
CHANNELS           = 1
BUFFER_DURATION_MS = 96
FRAMES_PER_BUFFER  = int(SAMPLE_RATE * BUFFER_DURATION_MS / 1000)

# Variables de estado global
client     = None
listener   = None
stream     = None
audio_task = None  # Nuevo: Referencia para la tarea de send_audio

def audio_callback(in_data, frame_count, time_info, status):
    """Callback de PyAudio para manejar datos de audio entrantes."""
    if hasattr(audio_callback, 'queue'):
        audio_callback.queue.put_nowait(in_data)
    return (None, pyaudio.paContinue)

def configure_audio_stream():
    """Configura y devuelve el flujo de audio de PyAudio."""
    global stream
    p = pyaudio.PyAudio()
    stream = p.open(
        format            = FORMAT,
        channels          = CHANNELS,
        rate              = SAMPLE_RATE,
        input             = True,
        frames_per_buffer = FRAMES_PER_BUFFER,
        stream_callback   = audio_callback,
    )
    return stream

class MyListener(RealtimeClientListener):
    """Listener personalizado para manejar eventos de transcripción en tiempo real."""

    def __init__(self, display_text_callback):
        super().__init__()
        self.display_text_callback = display_text_callback

    def on_result(self, result):
        if result["transcriptions"][0]["isFinal"]:
            transcription = result["transcriptions"][0]["transcription"]
            self.display_text_callback(transcription)
        else:
            print(f"Received partial results: {result['transcriptions'][0]['transcription']}")

    def on_ack_message(self, ackmessage):
        print(f"ACK message received: {ackmessage}")

    def on_connect(self):
        print("Connected successfully.")

    def on_connect_message(self, connectmessage):
        print(f"Connect message received: {connectmessage}")

    def on_network_event(self, event):
        print(f"Network event: {event}")

    def on_error(self, error):
        print(f"Error in transcription: {error}")

async def send_audio(queue):
    """Envía datos de audio de la cola al cliente en tiempo real."""
    while True:
        data = await queue.get()
        await client.send_data(data)

async def start_transcription(display_text_callback):
    """Inicia la transcripción de audio en tiempo real."""
    global client, listener, stream, audio_task

    try:
        print("Preparando listener para transcripción...")
        listener = MyListener(display_text_callback)

        print("Configurando parámetros de transcripción...")
        realtime_speech_parameters = RealtimeParameters(
            language_code                   = os.getenv('CON_SPE_LANGUAGE_CODE'),
            model_domain                    = RealtimeParameters.MODEL_DOMAIN_GENERIC,
            partial_silence_threshold_in_ms = 0,
            final_silence_threshold_in_ms   = 2000,
            stabilize_partial_results       = RealtimeParameters.STABILIZE_PARTIAL_RESULTS_NONE,
        )

        print("Creando cliente RealtimeClient...")
        config = from_file()
        client = RealtimeClient(
            config           = config,
            realtime_speech_parameters = realtime_speech_parameters,
            listener         = listener,
            service_endpoint = os.getenv('CON_REALTIME_SPEECH_URL'),
            compartment_id   = os.getenv('COMPARTMENT_ID'),
        )

        print("Cliente creado, iniciando conexión...")
        stream = configure_audio_stream()
        stream.start_stream()

        # Crear una nueva cola para cada transcripción
        audio_callback.queue = asyncio.Queue()

        loop = asyncio.get_running_loop()
        audio_task = loop.create_task(send_audio(audio_callback.queue))

        await client.connect()

    except Exception as e:
        print(f"Ocurrió un error en start_transcription: {e}")

def stop_transcription():
    """Detiene la transcripción de audio y cierra los recursos."""
    global client, stream, audio_task
    if stream and not stream.is_stopped():
        stream.stop_stream()
        stream.close()
        print("Stream de audio cerrado.")
    if client:
        client.close()
        print("Cliente de transcripción cerrado.")
    if audio_task:
        audio_task.cancel()
        print("Tarea de envío de audio cancelada.")

# conda env remove --name stt -y
# conda create -n stt python=3.10 -y
# conda activate stt
# pip install --upgrade pip
# pip install --force-reinstall -r requirements.txt
# python app.py
# allow any-user to manage ai-service-speech-realtime-family in tenancy