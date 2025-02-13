import os
import wave
from dotenv import load_dotenv
import groq
from fastapi import HTTPException

# Cargar las variables de entorno
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Verificar que la API Key esté configurada
if not api_key:
    raise ValueError("API_KEY no encontrada en el entorno. Verifica tu archivo .env.")

# Inicializar cliente Groq
client = groq.Groq(api_key=api_key)

# Directorio temporal para chunks
CHUNK_DIR = "audio/chunks"
os.makedirs(CHUNK_DIR, exist_ok=True)


def transcribir_audio_groq(file_path):
    """Transcribe un archivo de audio usando la API de Groq Whisper."""
    try:
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="json",
                language="es",
                temperature=0.0
            )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la transcripción: {str(e)}")


def dividir_audio(file_path, duracion_chunk_segundos=60):
    """Divide un archivo de audio en partes si supera 25MB."""
    try:
        with wave.open(file_path, 'rb') as wav:
            frame_rate = wav.getframerate()
            n_frames = wav.getnframes()
            n_channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            total_segundos = n_frames / frame_rate
            
            num_chunks = int(total_segundos / duracion_chunk_segundos)
            chunk_frame_count = frame_rate * duracion_chunk_segundos
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            chunk_paths = []
            
            for i in range(num_chunks + 1):
                start_frame = i * chunk_frame_count
                end_frame = min((i + 1) * chunk_frame_count, n_frames)

                wav.setpos(start_frame)
                chunk_data = wav.readframes(end_frame - start_frame)
                
                chunk_file_path = os.path.join(CHUNK_DIR, f"{base_name}_part_{i}.wav")
                with wave.open(chunk_file_path, 'wb') as chunk_wav:
                    chunk_wav.setnchannels(n_channels)
                    chunk_wav.setsampwidth(sample_width)
                    chunk_wav.setframerate(frame_rate)
                    chunk_wav.writeframes(chunk_data)
                
                chunk_paths.append(chunk_file_path)

            return chunk_paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al dividir el audio: {str(e)}")


def procesar_archivo_audio(file_path, duracion_chunk_segundos=60):
    """Procesa un archivo de audio, dividiéndolo si es necesario y transcribiéndolo."""
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)  # Convertir a MB
        transcripcion_completa = ""

        if file_size_mb > 25:
            chunk_paths = dividir_audio(file_path, duracion_chunk_segundos)
            for chunk_path in chunk_paths:
                transcripcion = transcribir_audio_groq(chunk_path)
                transcripcion_completa += transcripcion + "\n"
                os.remove(chunk_path)  # Limpiar los chunks después de procesar
        else:
            transcripcion_completa = transcribir_audio_groq(file_path)

        return transcripcion_completa.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el audio: {str(e)}")
