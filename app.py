from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import os, uuid, logging, requests, cv2
from ultralytics import YOLO
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # ⚠️ Enable CORS for all routes and origins

logging.basicConfig(level=logging.INFO)

# Download and load model (your existing code)
MODEL_PATH = 'yolo11l.pt'
MODEL_URL = 'https://huggingface.co/DarleVysali/yolo-model/resolve/main/yolo11l.pt'
if not os.path.exists(MODEL_PATH):
    logging.info("Downloading YOLO model...")
    resp = requests.get(MODEL_URL)
    resp.raise_for_status()
    with open(MODEL_PATH, 'wb') as f:
        f.write(resp.content)
    logging.info("Model downloaded.")
model = YOLO(MODEL_PATH)
class_list = model.names

@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    return jsonify({"status": "Backend is running."}), 200

@app.route('/process_video', methods=['POST', 'OPTIONS'])
@cross_origin()  # Allow CORS on this route
def process_video():
    if request.method == 'OPTIONS':
        # Flask-CORS handles preflight automatically, but safe to respond
        return make_response(('OK', 204, {}))

    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'Empty file name'}), 400

    save_path = os.path.join("uploads", video.filename)
    os.makedirs("uploads", exist_ok=True)
    video.save(save_path)
    logging.info(f"Saved video to {save_path}")

    # (Your processing logic here)

    return jsonify({'message': 'Video processed', 'filename': video.filename}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
