from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import logging

logger = logging.getLogger(__name__)

# Global cache for the model and processor
_processor = None
_model = None

def get_model_and_processor():
    """Lazily load the model and processor on first use."""
    global _processor, _model
    if _processor is None or _model is None:
        logger.info("Loading BLIP Large model for the first time...")
        try:
            # Automatically uses CPU if no GPU is available
            _processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            _model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
            logger.info("BLIP Large model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load BLIP model: {e}")
            raise
    return _processor, _model

def clean_caption(caption, prompt):
    """Cleans and formats the caption properly."""
    # Remove the prompt if present
    clean_text = caption.replace(prompt, "").strip()
    
    # Capitalize the first letter
    if clean_text:
        clean_text = clean_text[0].upper() + clean_text[1:]
        
    # Ensure it ends with punctuation
    if clean_text and clean_text[-1] not in ['.', '!', '?']:
        clean_text += '.'
        
    return clean_text

def generate_caption(image_path):
    """
    Reads an image and generates a detailed description using BLIP Large.
    Loads the model lazily to improve startup time.
    """
    try:
        processor, model = get_model_and_processor()
        
        raw_image = Image.open(image_path).convert('RGB')
        
        # A prompt to encourage the model to be descriptive
        prompt = "a photograph of"
        
        inputs = processor(raw_image, text=prompt, return_tensors="pt")
        
        # Generation parameters tuned for better, longer captions
        out = model.generate(
            **inputs, 
            max_new_tokens=200, 
            min_length=40,
            num_beams=7, # Increased beam search for better quality
            repetition_penalty=1.8, # Increased penalty to avoid repeating phrases
            length_penalty=1.2, # Encourage slightly longer descriptions
            do_sample=True,
            top_p=0.9
        )
        
        caption = processor.decode(out[0], skip_special_tokens=True)
        return clean_caption(caption, prompt)
        
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return None
