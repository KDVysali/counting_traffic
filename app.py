import os
import uuid
import cv2
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from collections import defaultdict
from ultralytics import YOLO

app = Flask(__name__, static_folder="static")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ✅ Allow ONLY your Vercel frontend domain (for production)
CORS(app, origins=["https://counting-traffic-frontend.vercel.app"], supports_credentials=True)

# === Download YOLO model if not already ===
MODEL_PATH = 'yolo11l.pt'
MODEL_URL = 'https://huggingface.co/DarleVysali/yolo-model/resolve/main/yolo11l.pt'

if not os.path.exists(MODEL_PATH):
    print("Downloading YOLO model from Hugging Face...")
    response = requests.get(MODEL_URL)
    if response.status_code != 200:
        raise Exception("❌ Failed to download model. Check URL or permissions.")
    with open(MODEL_PATH, 'wb') as f:
        f.write(response.content)
    print("✅ Model downloaded successfully.")

# === Load model ===
model = YOLO(MODEL_PATH)
class_list = model.names

@app.route('/')
def index():
    return "✅ Traffic counting API is running. Use POST /process_video"

@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    video = request.files['video']
    input_filename = f"{uuid.uuid4().hex}.mp4"
    video.save(input_filename)

    cap = cv2.VideoCapture(input_filename)
    if not cap.isOpened():
        return jsonify({"error": "Failed to open video"}), 500

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_filename = f"processed_{input_filename}"
    output_path = os.path.join("static", output_filename)
    os.makedirs("static", exist_ok=True)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    class_counts = defaultdict(int)
    crossed_ids = set()
    vehicle_log = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        results = model.track(frame, persist=True, classes=[1, 2, 3, 5, 6, 7])
        if results and results[0].boxes.data is not None:
            boxes = results[0].boxes.xyxy.cpu()
            class_indices = results[0].boxes.cls.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist() if results[0].boxes.id is not None else []

            line_y_red = int(0.6 * height)

            for box, track_id, class_idx in zip(boxes, track_ids, class_indices):
                x1, y1, x2, y2 = map(int, box)
                cy = (y1 + y2) // 2
                class_name = class_list[class_idx]

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{class_name} {track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                if cy > line_y_red and track_id not in crossed_ids:
                    crossed_ids.add(track_id)
                    class_counts[class_name] += 1
                    timestamp = round(frame_count / fps, 2)
                    vehicle_log.append({
                        "id": track_id,
                        "type": class_name,
                        "timestamp": timestamp
                    })

        out.write(frame)

    cap.release()
    out.release()
    os.remove(input_filename)

    return jsonify({
        "summary": dict(class_counts),
        "vehicles": vehicle_log,
        "video_url": f"https://{request.host}/static/{output_filename}"
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
