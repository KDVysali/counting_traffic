from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

# Enable CORS for your frontend (or use "*" for public access)
CORS(app, origins=["https://counting-traffic-frontend.vercel.app"], supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return jsonify({"status": "Backend is running."}), 200

@app.route('/process_video', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files:
            logging.warning("No video file found in request")
            return jsonify({'error': 'No video file uploaded'}), 400

        video = request.files['video']

        if video.filename == '':
            logging.warning("Empty filename")
            return jsonify({'error': 'Empty video file name'}), 400

        # Optional: Save video to disk
        save_path = os.path.join("uploads", video.filename)
        os.makedirs("uploads", exist_ok=True)
        video.save(save_path)
        logging.info(f"Video saved at {save_path}")

        # TODO: Add actual processing logic here
        # For now, return success response
        return jsonify({
            'message': 'Video received successfully',
            'filename': video.filename
        }), 200

    except Exception as e:
        logging.exception("Error during video processing")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
