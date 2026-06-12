import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

# Global variable to cache the Groq client
_client = None
_client_initialized = False

def get_groq_client():
    """
    Lazily initializes and returns the Groq client.
    Safely handles missing API keys by returning None.
    """
    global _client, _client_initialized
    
    if _client_initialized:
        return _client
        
    _client_initialized = True
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY environment variable is not set. LLM enhancement will be disabled.")
        return None
        
    try:
        # The client will automatically use the GROQ_API_KEY environment variable.
        _client = Groq()
        logger.info("Groq client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        _client = None
        
    return _client

def enhance_caption(base_caption):
    """
    Enhances a raw image caption using Groq's LLM to make it more natural, 
    descriptive, and optimized for a visually impaired user.
    """
    client = get_groq_client()
    
    if not client:
        logger.info("Skipping LLM enhancement due to missing Groq client. Returning base caption.")
        return base_caption
        
    prompt = f"""
    You are an expert accessibility assistant for visually impaired users. 
    Your task is to take a raw, AI-generated image caption and enhance it into a clear, 
    natural, and highly descriptive sentence or short paragraph.
    
    Raw Caption: "{base_caption}"
    
    Instructions:
    1. Remove filler words (like "a photograph of", "image shows").
    2. Remove repeated phrases or redundancies.
    3. Keep only useful visual details. Describe objects, people, colors, actions, environment, and visible emotions.
    4. Make it sound completely natural when spoken aloud by a Text-To-Speech engine.
    5. Be concise but highly descriptive.
    6. Return ONLY the final enhanced caption text. Do not include any explanations, greetings, or quotation marks.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful, professional AI assistant designed to describe images for the blind."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200,
            top_p=0.9,
        )
        
        enhanced_text = response.choices[0].message.content.strip()
        
        # Remove any surrounding quotes if the LLM accidentally added them
        if enhanced_text.startswith('"') and enhanced_text.endswith('"'):
            enhanced_text = enhanced_text[1:-1]
            
        return enhanced_text
        
    except Exception as e:
        logger.error(f"Error communicating with Groq API: {e}")
        # Fallback to the original caption if the API fails
        return base_caption
