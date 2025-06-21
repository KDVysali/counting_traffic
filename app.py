from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
from ultralytics import YOLO
from collections import defaultdict
import os
import uuid
import requests

app = Flask(__name__)
CORS(app)

# === Model Download (if not already downloaded) ===
MODEL_PATH = 'yolo11l.pt'
if not os.path.exists(MODEL_PATH):
    print("Downloading YOLO model...")
    url = 'https://drive.google.com/uc?export=download&id=1U3KpDbjaWHwINnJG9cK9zllWGq2ZWy3o'
    response = requests.get(url)
    with open(MODEL_PATH, 'wb') as f:
        f.write(response.content)
    print("Model downloaded successfully.")

# === Load YOLO model ===
model = YOLO(MODEL_PATH)
class_list = model.names

# === API Route ===
@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    video = request.files['video']
    filename = f"{uuid.uuid4().hex}.mp4"
    video.save(filename)

    cap = cv2.VideoCapture(filename)
    if not cap.isOpened():
        return jsonify({"error": "Failed to open video"}), 500

    class_counts = defaultdict(int)
    crossed_ids = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(frame, persist=True, classes=[1, 2, 3, 5, 6, 7])
        if results and results[0].boxes.data is not None:
            boxes = results[0].boxes.xyxy.cpu()
            class_indices = results[0].boxes.cls.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist() if results[0].boxes.id is not None else []

            frame_height = frame.shape[0]
            line_y_red = int(0.6 * frame_height)

            for box, track_id, class_idx in zip(boxes, track_ids, class_indices):
                x1, y1, x2, y2 = map(int, box)
                cy = (y1 + y2) // 2
                class_name = class_list[class_idx]
                if cy > line_y_red and track_id not in crossed_ids:
                    crossed_ids.add(track_id)
                    class_counts[class_name] += 1

    cap.release()
    os.remove(filename)
    return jsonify(dict(class_counts))

# === Default route to test if API is running ===
@app.route('/')
def index():
    return "✅ Traffic counting API is running. Use POST /process_video"

# === Run the app on the correct host/port ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
