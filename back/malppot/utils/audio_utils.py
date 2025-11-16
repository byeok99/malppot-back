from fastapi import UploadFile
from pydub import AudioSegment
import tempfile, shutil, os

async def convert_upload_to_wav(audio: UploadFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
        shutil.copyfileobj(audio.file, temp_webm)
        webm_path = temp_webm.name
    wav_path = webm_path.replace(".webm", ".wav")

    try:
        sound = AudioSegment.from_file(webm_path, format="webm")
        sound = sound.set_channels(1).set_frame_rate(16000)
        sound.export(wav_path, format="wav")
    except Exception as e:
        os.remove(webm_path)
        raise Exception(f"Audio conversion failed: {e}")
    finally:
        os.remove(webm_path)

    return wav_path