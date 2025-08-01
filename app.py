from flask import Flask, request, jsonify, send_file
from pathlib import Path
import os
import csv
import requests
import cv2
import numpy as np
from ultralytics import YOLO
import torch
from src.vision_analysis.satellite_analysis import SatelliteImageAnalyzer

# Configurar torch para permitir la carga del modelo YOLO
torch.serialization.add_safe_globals([
    "ultralytics.nn.tasks.DetectionModel",
    "ultralytics.nn.modules",
    "torch.nn.modules.conv.Conv2d",
    "torch.nn.modules.batchnorm.BatchNorm2d",
    "torch.nn.modules.activation.SiLU"
])

# Configuración inicial
app = Flask(__name__)
CACHE_DIR = Path("data/satellite_images")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\yolov8n.pt"

try:
    model = YOLO(MODEL_PATH)
    print("Modelo YOLO cargado exitosamente")
except Exception as e:
    print(f"Error cargando modelo YOLO: {e}")
    print("Usando modelo demo por defecto")
    model = None

config = {
    'satellite.cache_dir': 'data/satellite_images',
    'api_keys.sentinel': os.getenv('SENTINEL_API_KEY', 'DEMO_KEY')
}
analyzer = SatelliteImageAnalyzer(config)

@app.route('/get_image', methods=['GET'])
def get_image():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    date = request.args.get('date')

    api_key = config['api_keys.sentinel']
    url = (
        f"https://services.sentinel-hub.com/ogc/wms/{api_key}?SERVICE=WMS&REQUEST=GetMap&LAYERS=TRUE_COLOR"
        f"&WIDTH=512&HEIGHT=512&BBOX={lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}&FORMAT=image/png&TIME={date}"
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        file_name = f"sentinel_{lat}_{lon}_{date}.png"
        file_path = CACHE_DIR / file_name
        with open(file_path, 'wb') as f:
            f.write(resp.content)
        return jsonify({"image_path": str(file_path)})
    else:
        return jsonify({"error": f"Error downloading image: {resp.status_code}"}), 400

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    date = data.get('date')

    try:
        results = analyzer.analyze_satellite_image(lat, lon, date)
        csv_path = CACHE_DIR / "detections.csv"
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["image_path", "mean_intensity", "risk_score"])
            writer.writeheader()
            writer.writerow(results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/download_csv', methods=['GET'])
def download_csv():
    csv_path = CACHE_DIR / "detections.csv"
    if csv_path.exists():
        return send_file(csv_path, as_attachment=True)
    else:
        return jsonify({"error": "No CSV file found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
