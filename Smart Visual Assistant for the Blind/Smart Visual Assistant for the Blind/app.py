from flask import Flask, render_template, request, jsonify, url_for
import os
import uuid
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from werkzeug.utils import secure_filename
from model import generate_caption
from tts import generate_audio
from llm_enhancer import enhance_caption

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Safely manage paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
app.config['UPLOAD_FOLDER'] = os.path.join(STATIC_DIR, 'uploads')
app.config['AUDIO_FOLDER'] = os.path.join(STATIC_DIR, 'audio')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure directories exist safely on startup
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Validate request
    if 'image' not in request.files:
        return jsonify({'error': 'No file part in the request. Please upload an image.'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected. Please choose an image to upload.'}), 400
        
    # 2. Process file securely
    if file and file.filename and allowed_file(file.filename):
        filepath = None
        try:
            # Secure the filename to avoid directory traversal or conflicts
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower()
            if not ext:
                ext = 'jpg' # fallback
            
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            file.save(filepath)
            
            # 3. Generate initial visual understanding (BLIP Large)
            base_caption = generate_caption(filepath)
            
            if not base_caption:
                raise ValueError("Failed to generate a valid caption for the image.")
                
            # 4. Enhance the caption using Groq LLM
            logger.info("Enhancing caption with LLM...")
            final_caption = enhance_caption(base_caption)
            
            # 5. Generate audio (non-fatal if fails, just warn the user)
            audio_url = None
            audio_filename = generate_audio(final_caption, app.config['AUDIO_FOLDER'])
            
            if audio_filename:
                audio_url = url_for('static', filename=f'audio/{audio_filename}')
            else:
                logger.warning("Caption generated successfully, but audio generation failed.")
                
            image_url = url_for('static', filename=f'uploads/{filename}')
            
            # 6. Cleanup (Optional: uncomment to delete uploaded images after processing to save space)
            # if os.path.exists(filepath):
            #     os.remove(filepath)
            
            return jsonify({
                'success': True,
                'caption': final_caption,
                'audio_url': audio_url,
                'image_url': image_url,
                'audio_warning': audio_url is None
            })
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return jsonify({'error': 'An unexpected error occurred during analysis. Please try again.'}), 500
            
    return jsonify({'error': 'Unsupported file format. Please upload PNG, JPG, JPEG, or WEBP.'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
