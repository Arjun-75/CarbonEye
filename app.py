from flask import Flask, request, render_template, jsonify, send_file
import os
import cv2
from ultralytics import YOLO
import numpy as np
import supervision as sv
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

MODEL = YOLO("yolov8x.pt")
selected_classes = [2, 3, 5, 7]
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files or 'distance' not in request.form:
        return "Invalid input: Missing video or distance", 400

    video = request.files['video']
    distance = request.form['distance']

    if not video.filename:
        return "No video file selected", 400

    try:
        distance = float(distance)
        if distance <= 0:
            raise ValueError("Distance must be positive.")
    except ValueError as ve:
        return f"Invalid input for distance: {ve}", 400

    filename = secure_filename(video.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    video.save(filepath)

    processed_filename = f"processed_{filename}"
    processed_filepath = os.path.join(RESULT_FOLDER, processed_filename)

    # Process video
    try:
        number_of_vehicles_detected = process_with_yolo(filepath, processed_filepath)
    except Exception as e:
        return f"Error during video processing: {e}", 500

    # Calculate CO2 emissions
    co2_emissions_factor = 0.610
    fuel_efficiency = 11.0
    co2_emissions = (number_of_vehicles_detected * (distance / fuel_efficiency) * co2_emissions_factor)

    return jsonify({
        "number_of_vehicles_detected": number_of_vehicles_detected,
        "distance": distance,
        "co2_emissions": co2_emissions,
        "processed_video": f"/download/{processed_filename}"
    })

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(RESULT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

def process_with_yolo(source_path, target_path):
    video_info = sv.VideoInfo.from_video_path(source_path)
    frame_width = video_info.width
    frame_height = video_info.height

    line_start = sv.Point(0, frame_height // 2)
    line_end = sv.Point(frame_width - 1, frame_height // 2)
    line_zone = sv.LineZone(start=line_start, end=line_end)
    byte_tracker = sv.ByteTrack()

    box_annotator = sv.BoxAnnotator()
    trace_annotator = sv.TraceAnnotator(thickness=4, trace_length=50)
    line_zone_annotator = sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=2)

    def callback(frame: np.ndarray, index: int) -> np.ndarray:
        results = MODEL(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[np.isin(detections.class_id, selected_classes)]
        detections = byte_tracker.update_with_detections(detections)
        annotated_frame = trace_annotator.annotate(
            scene=frame.copy(), detections=detections
        )
        annotated_frame = box_annotator.annotate(
            scene=annotated_frame, detections=detections
        )
        line_zone.trigger(detections)
        return line_zone_annotator.annotate(annotated_frame, line_counter=line_zone)

    sv.process_video(source_path, target_path, callback=callback)
    total_count = line_zone.out_count + line_zone.in_count
    return total_count 

if __name__ == "__main__":
    app.run(debug=True)
