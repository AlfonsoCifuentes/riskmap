#!/usr/bin/env python3
"""
Script de prueba para el sistema de detección satelital.
Genera imágenes de ejemplo y las procesa con el sistema.
"""

import cv2
import numpy as np
import os
import json
from pathlib import Path

def create_sample_images():
    """Crear imágenes satelitales de ejemplo para pruebas"""
    cache_dir = Path("data/satellite_images")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear imagen urbana simulada
    urban_img = np.random.randint(50, 150, (512, 512, 3), dtype=np.uint8)
    # Añadir algunas estructuras urbanas simuladas
    cv2.rectangle(urban_img, (100, 100), (200, 200), (80, 80, 80), -1)
    cv2.rectangle(urban_img, (250, 150), (350, 250), (90, 90, 90), -1)
    cv2.rectangle(urban_img, (50, 300), (150, 400), (70, 70, 70), -1)
    
    urban_path = cache_dir / "urban_sample_40.7128_-74.0060_2025-08-01.png"
    cv2.imwrite(str(urban_path), urban_img)
    print(f"Imagen urbana creada: {urban_path}")
    
    # Crear imagen rural/natural simulada
    rural_img = np.random.randint(80, 180, (512, 512, 3), dtype=np.uint8)
    # Añadir vegetación (verde)
    rural_img[:, :, 1] = np.random.randint(120, 200, (512, 512))  # Canal verde
    # Añadir agua (azul)
    cv2.circle(rural_img, (300, 300), 80, (180, 120, 60), -1)
    
    rural_path = cache_dir / "rural_sample_35.6762_139.6503_2025-08-01.png"
    cv2.imwrite(str(rural_path), rural_img)
    print(f"Imagen rural creada: {rural_path}")
    
    # Crear imagen de conflicto simulada
    conflict_img = np.random.randint(60, 120, (512, 512, 3), dtype=np.uint8)
    # Simular humo (gris)
    cv2.circle(conflict_img, (200, 200), 60, (90, 90, 90), -1)
    cv2.circle(conflict_img, (180, 180), 40, (70, 70, 70), -1)
    # Simular vehículos (rectángulos pequeños)
    cv2.rectangle(conflict_img, (350, 350), (370, 380), (40, 40, 40), -1)
    cv2.rectangle(conflict_img, (380, 340), (400, 370), (45, 45, 45), -1)
    
    conflict_path = cache_dir / "conflict_sample_33.3152_44.3661_2025-08-01.png"
    cv2.imwrite(str(conflict_path), conflict_img)
    print(f"Imagen de conflicto creada: {conflict_path}")
    
    return [urban_path, rural_path, conflict_path]

def analyze_sample_images(image_paths):
    """Analizar las imágenes de ejemplo y generar resultados"""
    results = []
    
    for img_path in image_paths:
        # Extraer coordenadas del nombre del archivo
        parts = img_path.stem.split('_')
        lat = float(parts[2])
        lon = float(parts[3])
        
        # Leer imagen
        img = cv2.imread(str(img_path))
        if img is None:
            continue
            
        # Análisis básico de la imagen
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_intensity = float(np.mean(gray))
        std_intensity = float(np.std(gray))
        
        # Detección de características simples
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # Clasificación de riesgo basada en características
        risk_score = 0.0
        detected_objects = []
        
        if mean_intensity < 100:  # Imagen oscura - posible humo/conflicto
            risk_score += 0.3
            detected_objects.append({"class": "smoke", "confidence": 0.7, "x": 200, "y": 200})
            
        if edge_density > 0.1:  # Muchas estructuras - área urbana
            risk_score += 0.2
            detected_objects.append({"class": "urban_area", "confidence": 0.8, "x": 150, "y": 150})
            
        if std_intensity > 30:  # Mucha variación - posibles vehículos/estructuras
            risk_score += 0.1
            detected_objects.append({"class": "vehicles", "confidence": 0.6, "x": 360, "y": 360})
        
        risk_score = min(1.0, risk_score)
        
        result = {
            "image_path": str(img_path),
            "lat": lat,
            "lon": lon,
            "mean_intensity": mean_intensity,
            "edge_density": edge_density,
            "risk_score": risk_score,
            "detected_objects": detected_objects,
            "analysis_summary": f"Analyzed {img_path.name}: Risk level {'HIGH' if risk_score > 0.5 else 'MEDIUM' if risk_score > 0.2 else 'LOW'}"
        }
        
        results.append(result)
        print(f"Análisis completado para {img_path.name}: Risk={risk_score:.2f}")
    
    return results

def save_results_csv(results):
    """Guardar resultados en CSV"""
    import csv
    
    csv_path = Path("data/satellite_images/sample_detections.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["image_path", "lat", "lon", "mean_intensity", "edge_density", "risk_score", "detected_objects_count", "analysis_summary"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = result.copy()
            row["detected_objects_count"] = len(result["detected_objects"])
            del row["detected_objects"]  # Simplificar para CSV
            writer.writerow(row)
    
    print(f"Resultados guardados en: {csv_path}")
    return csv_path

def main():
    """Función principal de prueba"""
    print("=== Sistema de Detección Satelital - Pruebas ===")
    print("1. Creando imágenes de ejemplo...")
    image_paths = create_sample_images()
    
    print("\n2. Analizando imágenes...")
    results = analyze_sample_images(image_paths)
    
    print("\n3. Guardando resultados...")
    csv_path = save_results_csv(results)
    
    print("\n4. Resumen de resultados:")
    for result in results:
        print(f"  - {result['analysis_summary']}")
    
    print(f"\n✅ Prueba completada. {len(results)} imágenes procesadas.")
    print(f"📊 Resultados disponibles en: {csv_path}")
    
    # Guardar también en JSON para APIs
    json_path = Path("data/satellite_images/sample_detections.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"🔗 Datos JSON disponibles en: {json_path}")

if __name__ == "__main__":
    main()
