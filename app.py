import os
import tempfile
import shutil
from collections import defaultdict

import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO

# -----------------------------------------------------------------------------
# App & CORS setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
# Only allow your Vercel frontend
CORS(app, origins=[os.environ.get("CORS_ALLOWED_ORIGINS", "https://counting-traffic-frontend.vercel.app")])

# -----------------------------------------------------------------------------
# Load model once at startup
# -----------------------------------------------------------------------------
MODEL_PATH = os.environ.get("YOLO_WEIGHTS", "yolo11l.pt")
model = YOLO(MODEL_PATH)
class_list = model.names  # e.g. {0: 'person', 1: 'bicycle', ...}

# -----------------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": True})

# -----------------------------------------------------------------------------
# Main endpoint: upload a video, process, and return counts
# -----------------------------------------------------------------------------
@app.route("/count", methods=["POST"])
def count_vehicles():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided."}), 400

    # Save incoming video to a temp directory
    video_file = request.files["video"]
    tmpdir = tempfile.mkdtemp()
    input_path = os.path.join(tmpdir, video_file.filename)
    video_file.save(input_path)

    try:
        # Open video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return jsonify({"error": f"Cannot open video {video_file.filename}"}), 400

        # Get properties
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps    = cap.get(cv2.CAP_PROP_FPS) or 10.0

        # Prepare output writer (optional—only if you want to save annotated video)
        fourcc      = cv2.VideoWriter_fourcc(*"mp4v")
        output_path = os.path.join(tmpdir, "output.mp4")
        out_writer  = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Counting logic
        class_counts = defaultdict(int)
        crossed_ids  = set()
        # Process each frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Run YOLO tracking on specified classes (vehicles)
            results = model.track(frame, persist=True, classes=[1,2,3,5,6,7])

            if results and results[0].boxes.data is not None:
                annotated = results[0].plot()
                fh, fw = annotated.shape[:2]
                line_y = int(0.6 * fh)
                # draw counting line
                cv2.line(annotated, (0, line_y), (fw-1, line_y), (0,0,255), 3)

                boxes       = results[0].boxes.xyxy.cpu().numpy()
                cls_idxs    = results[0].boxes.cls.int().cpu().tolist()
                track_ids   = (results[0].boxes.id.int().cpu().tolist()
                               if results[0].boxes.id is not None else [])

                for (x1, y1, x2, y2), tid, ci in zip(boxes, track_ids, cls_idxs):
                    cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                    if cy > line_y and tid not in crossed_ids:
                        crossed_ids.add(tid)
                        class_counts[class_list[ci]] += 1

                # overlay counts
                y0 = 30
                for name, cnt in class_counts.items():
                    cv2.putText(annotated, f"{name}: {cnt}", (10, y0),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                    y0 += 30

                out_writer.write(annotated)
            else:
                out_writer.write(frame)

        cap.release()
        out_writer.release()

        # Return the JSON counts
        return jsonify({"counts": dict(class_counts)})

    finally:
        # Clean up temp directory
        shutil.rmtree(tmpdir, ignore_errors=True)

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
