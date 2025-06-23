from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import logging

app = Flask(__name__)

# Custom CORS origin checker that allows all *.vercel.app domains
def allow_vercel_origin(origin):
    return origin and origin.endswith(".vercel.app")

CORS(app, origins=allow_vercel_origin, supports_credentials=True)

# Enable logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return jsonify({"status": "Backend is running."}), 200

# === Manual CORS Preflight Handler for /process_video ===
@app.route('/process_video', methods=['OPTIONS'])
def process_video_options():
    origin = request.headers.get('Origin')
    response = make_response()
    if origin and origin.endswith(".vercel.app"):
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# === Video Upload Handler ===
@app.route('/process_video', methods=['POST'])
def process_video():
    try:
        origin = request.headers.get('Origin')
        logging.info(f"Request received from origin: {origin}")
        
        if 'video' not in request.files:
            logging.warning("No video file found in request")
            return jsonify({'error': 'No video file uploaded'}), 400

        video = request.files['video']

        if video.filename == '':
            logging.warning("Empty filename")
            return jsonify({'error': 'Empty video file name'}), 400

        # Save uploaded video
        save_path = os.path.join("uploads", video.filename)
        os.makedirs("uploads", exist_ok=True)
        video.save(save_path)
        logging.info(f"Video saved at {save_path}")

        # Your actual processing logic would go here

        # Build response
        response = jsonify({
            'message': 'Video received successfully',
            'filename': video.filename
        })

        if origin and origin.endswith(".vercel.app"):
            response.headers['Access-Control-Allow-Origin'] = origin

        return response, 200

    except Exception as e:
        logging.exception("Error during video processing")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
