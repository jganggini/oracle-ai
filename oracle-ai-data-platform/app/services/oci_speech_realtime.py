import asyncio
import pyaudio
import os
import logging
from dotenv import load_dotenv
from oci.config import from_file
from oci_ai_speech_realtime import RealtimeSpeechClient, RealtimeSpeechClientListener
from oci.ai_speech.models import RealtimeParameters

import streamlit as st

language_map = {
    "esa" : "es-ES",
    "ptb" : "pt-BR",
    "gb"  : "en-GB"
}

# Load environment variables
load_dotenv()

# Set audio parameters
SAMPLE_RATE = 16000  # Can be 8000 as well
FORMAT = pyaudio.paInt16
CHANNELS = 1
BUFFER_DURATION_MS = 96

# Calculate the number of frames per buffer
FRAMES_PER_BUFFER = int(SAMPLE_RATE * BUFFER_DURATION_MS / 1000)

# Set realtime/customization parameters
# Duration until which the session is active. To run forever, set this to -1
SESSION_DURATION = -1  # seconds

# Realtime Speech Parameters
def get_realtime_parameters(customizations, compartment_id, language_code):
    realtime_speech_parameters: RealtimeParameters = RealtimeParameters()
    realtime_speech_parameters.language_code =language_code
    realtime_speech_parameters.model_domain = RealtimeParameters.MODEL_DOMAIN_GENERIC
    realtime_speech_parameters.partial_silence_threshold_in_ms = 0
    realtime_speech_parameters.final_silence_threshold_in_ms = 2000
    realtime_speech_parameters.encoding = (
        f"audio/raw;rate={SAMPLE_RATE}"  # Default=16000 Hz
    )
    realtime_speech_parameters.should_ignore_invalid_customizations = False
    realtime_speech_parameters.stabilize_partial_results = (
        RealtimeParameters.STABILIZE_PARTIAL_RESULTS_NONE
    )
    realtime_speech_parameters.punctuation = RealtimeParameters.PUNCTUATION_NONE

    # Skip this if you don't want to use customizations
    for customization_id in customizations:
        realtime_speech_parameters.customizations = [
            {
                "compartmentId": compartment_id,
                "customizationId": customization_id,
            }
        ]

    return realtime_speech_parameters

# Listener
class MyListener(RealtimeSpeechClientListener):
    def __init__(self, display_transcription_final, display_transcription_partial):
        super().__init__()
        self.display_transcription_final = display_transcription_final
        self.display_transcription_partial = display_transcription_partial
    
    def on_result(self, result):
        if result["transcriptions"][0]["isFinal"]:
            transcription = result['transcriptions'][0]['transcription']
            #print(f"Received final results: {transcription}")
            self.display_transcription_final(transcription)
        else:
            transcription = result['transcriptions'][0]['transcription']
            #print(f"Received partial results: {transcription}")
            self.display_transcription_partial(transcription)

    def on_ack_message(self, ackmessage):
        return super().on_ack_message(ackmessage)

    def on_connect(self):
        return super().on_connect()

    def on_connect_message(self, connectmessage):
        return super().on_connect_message(connectmessage)

    def on_network_event(self, ackmessage):
        return super().on_network_event(ackmessage)

    def on_error(self, error_message):
        return super().on_error(error_message)

    def on_close(self, error_code, error_message):
        print(f"Closed due to error code {error_code}:{error_message}")

# Session lifecycle
async def start_realtime_session(display_transcription_final, display_transcription_partial, language):
    # Map language to code
    language = language_map.get(language)

    customizations=[]
    compartment_id   = os.getenv("CON_COMPARTMENT_ID")
    language_code    = language
    service_endpoint = os.getenv("CON_SPEECH_SERVICE_ENDPOINT")

    print("Preparando listener para transcripción...")
    listener = MyListener(display_transcription_final, display_transcription_partial)

    def message_callback(message):
        print(f"Received message: {message}")

    config = from_file()

    queue = asyncio.Queue()

    # Audio callback
    def audio_callback(in_data, frame_count, time_info, status):
        queue.put_nowait(in_data)
        return (None, pyaudio.paContinue)

    # PyAudio setup
    p = pyaudio.PyAudio()

    # Open the stream
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER,
        stream_callback=audio_callback,
    )
    stream.start_stream()
    
    # Send audio in loop
    async def send_audio(client, stream):
        i = 0
        while not client.close_flag:
            data = await queue.get()

            # Send it over the websocket
            await client.send_data(data)
            i += 1

        if stream.is_active():
            stream.close()

    # Build parameters and client
    realtime_speech_parameters = get_realtime_parameters(
        customizations = customizations,
        compartment_id = compartment_id,
        language_code  = language_code
    )

    client = RealtimeSpeechClient(
        config                     = config,
        realtime_speech_parameters = realtime_speech_parameters,
        listener                   = listener,
        service_endpoint           = service_endpoint,
        compartment_id             = compartment_id
    )

    st.session_state.speech_client = client  # Store in session for per-user control
    
    # Start tasks and connect
    asyncio.create_task(send_audio(client, stream))

    await client.connect()

def stop_realtime_session():
    client = st.session_state.get("speech_client")
    if client:
        client.close()
        st.session_state.speech_client = None