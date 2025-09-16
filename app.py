from flask import Flask, request, jsonify, send_file, send_from_directory
from pathlib import Path
import os
import csv
import json
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
app = Flask(__name__, static_folder='.', static_url_path='')
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

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

@app.route('/images')
def list_images():
    """Listar las imágenes disponibles para la galería"""
    try:
        images = []
        for img_file in CACHE_DIR.glob("*.png"):
            images.append({
                'filename': img_file.name,
                'path': f'data/satellite_images/{img_file.name}',
                'size': img_file.stat().st_size
            })
        return jsonify(images)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/damage_analysis', methods=['POST'])
def damage_analysis():
    """Endpoint para análisis de daños usando xView2"""
    try:
        # Check if we have an image file
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "No image file selected"}), 400
                
            # Save temporary file
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, "temp_image.png")
            file.save(temp_path)
            
            # Analyze the image directly
            damage_result = analyzer.analyze_damage(temp_path)
            
            # Clean up
            os.remove(temp_path)
            os.rmdir(temp_dir)
            
            return jsonify({
                "success": True,
                "damage_analysis": damage_result,
                "image_analyzed": True
            })
            
        # If no file, check for coordinates (original behavior)
        data = request.json
        if not data:
            return jsonify({"error": "No image file or coordinates provided"}), 400
            
        lat = data.get('lat')
        lon = data.get('lon')
        date = data.get('date')
        
        if not all([lat, lon, date]):
            return jsonify({"error": "Missing required parameters: lat, lon, date"}), 400
        
        # Realizar análisis completo incluyendo evaluación de daños
        results = analyzer.analyze_satellite_image(lat, lon, date)
        
        # Guardar resultados extendidos
        csv_path = CACHE_DIR / "damage_analysis.csv"
        
        # Preparar datos para CSV
        flat_results = {
            'image_path': results['image_path'],
            'lat': results['coordinates']['lat'],
            'lon': results['coordinates']['lon'],
            'date': results['coordinates']['date'],
            'mean_intensity': results['basic_analysis']['mean_intensity'],
            'std_intensity': results['basic_analysis']['std_intensity'],
            'edge_density': results['basic_analysis']['edge_density'],
            'basic_risk_score': results['basic_analysis']['risk_score'],
            'combined_risk_level': results['combined_risk_level'],
            'timestamp': results['timestamp']
        }
        
        # Agregar datos de análisis de daños si están disponibles
        if results['damage_analysis']:
            damage = results['damage_analysis']
            flat_results.update({
                'damage_class': damage.get('damage_class', 'unknown'),
                'damage_confidence': damage.get('confidence', 0.0),
                'damage_risk_level': damage.get('risk_level', 'unknown')
            })
        
        # Guardar en CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=flat_results.keys())
            writer.writeheader()
            writer.writerow(flat_results)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train_damage_model', methods=['POST'])
def train_damage_model():
    """Endpoint para entrenar el modelo de evaluación de daños"""
    try:
        success = analyzer.train_damage_model()
        if success:
            return jsonify({
                "success": True,
                "message": "Damage model training completed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Training failed"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/damage_model_info', methods=['GET'])
def damage_model_info():
    """Obtiene información sobre el modelo de evaluación de daños"""
    try:
        info = analyzer.get_damage_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/batch_damage_analysis', methods=['POST'])
def batch_damage_analysis():
    """Análisis de daños en lote para múltiples coordenadas"""
    data = request.json
    locations = data.get('locations', [])
    
    if not locations:
        return jsonify({"error": "No locations provided"}), 400
    
    results = []
    errors = []
    
    for i, location in enumerate(locations):
        try:
            lat = location.get('lat')
            lon = location.get('lon')
            date = location.get('date')
            
            if not all([lat, lon, date]):
                errors.append({
                    "index": i,
                    "error": "Missing required parameters: lat, lon, date"
                })
                continue
            
            result = analyzer.analyze_satellite_image(lat, lon, date)
            result['location_index'] = i
            results.append(result)
            
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e)
            })
    
    return jsonify({
        "results": results,
        "errors": errors,
        "total_processed": len(results),
        "total_errors": len(errors)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
