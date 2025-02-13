from fastapi import FastAPI, File, UploadFile
from transcription import procesar_archivo_audio
import shutil
import os

app = FastAPI()


@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    """
    API endpoint para transcribir un archivo de audio.
    
    Args:
        file (UploadFile): Archivo de audio subido por el usuario.
    
    Returns:
        dict: JSON con la transcripción.
    """
    try:
        file_path = f"audio/temp_{file.filename}"
        os.makedirs("audio", exist_ok=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        transcription = procesar_archivo_audio(file_path)
        os.remove(file_path)  # Limpiar archivo después de transcribir

        return {"transcription": transcription}
    except Exception as e:
        return {"error": str(e)}
