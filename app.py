from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ Enable CORS for your frontend
CORS(app, origins=['https://counting-traffic-frontend.vercel.app'])

@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400

    video = request.files['video']
    
    # TODO: Insert your actual video-processing logic here.
    return jsonify({'message': f'Video "{video.filename}" received successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
