from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

# Enable CORS for your frontend
CORS(app, origins=["https://counting-traffic-frontend.vercel.app"], supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return jsonify({"status": "Backend is running."}), 200

# Handle OPTIONS preflight request manually
@app.route('/process_video', methods=['OPTIONS'])
def process_video_options():
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = 'https://counting-traffic-frontend.vercel.app'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

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

        # Save video to disk
        save_path = os.path.join("uploads", video.filename)
        os.makedirs("uploads", exist_ok=True)
        video.save(save_path)
        logging.info(f"Video saved at {save_path}")

        # Dummy processing for now
        response = jsonify({
            'message': 'Video received successfully',
            'filename': video.filename
        })

        # Set CORS headers manually in POST response
        response.headers['Access-Control-Allow-Origin'] = 'https://counting-traffic-frontend.vercel.app'
        return response, 200

    except Exception as e:
        logging.exception("Error during video processing")
        response = jsonify({'error': 'Internal server error', 'details': str(e)})
        response.headers['Access-Control-Allow-Origin'] = 'https://counting-traffic-frontend.vercel.app'
        return response, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
