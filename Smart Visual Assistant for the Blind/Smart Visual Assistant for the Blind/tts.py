from gtts import gTTS
import os
import uuid
import logging
import re

logger = logging.getLogger(__name__)

def generate_audio(text, output_dir="static/audio"):
    """
    Converts text to speech and saves it as an MP3 file.
    Limits text length to 1000 characters to prevent crashes.
    Returns the filename of the saved audio.
    """
    try:
        if not text:
            logger.warning("Empty text provided for TTS.")
            return None
            
        # Limit text length safely (max 1000 characters)
        safe_text = text[:1000].strip()
        
        # Sanitize for smoother speech (replace newlines and multiple spaces)
        safe_text = re.sub(r'\s+', ' ', safe_text)
        
        # Ensure directory exists safely
        os.makedirs(output_dir, exist_ok=True)
            
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Generate speech
        tts = gTTS(text=safe_text, lang='en', slow=False)
        tts.save(filepath)
        
        return filename
    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        return None
