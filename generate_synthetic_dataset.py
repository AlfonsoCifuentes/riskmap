"""
Generador de imágenes satelitales sintéticas para entrenamiento
Crea múltiples imágenes con diferentes características para entrenar el modelo de daños
"""

import cv2
import numpy as np
import json
import csv
from pathlib import Path
from datetime import datetime
import random

def create_synthetic_satellite_image(image_type, width=256, height=256):
    """
    Crea una imagen satelital sintética según el tipo especificado
    """
    # Base canvas
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    if image_type == 'no-damage':
        # Imagen clara con estructuras regulares
        # Fondo claro (edificios/carreteras)
        img.fill(180)
        
        # Añadir estructuras regulares (edificios)
        for i in range(5):
            x = random.randint(20, width-40)
            y = random.randint(20, height-40)
            w = random.randint(15, 30)
            h = random.randint(15, 30)
            cv2.rectangle(img, (x, y), (x+w, y+h), (200, 200, 200), -1)
            cv2.rectangle(img, (x, y), (x+w, y+h), (150, 150, 150), 1)
        
        # Líneas de carreteras
        cv2.line(img, (0, height//2), (width, height//2), (120, 120, 120), 3)
        cv2.line(img, (width//2, 0), (width//2, height), (120, 120, 120), 3)
        
    elif image_type == 'minor-damage':
        # Imagen con daños menores
        img.fill(160)
        
        # Estructuras parcialmente dañadas
        for i in range(4):
            x = random.randint(20, width-40)
            y = random.randint(20, height-40)
            w = random.randint(15, 30)
            h = random.randint(15, 30)
            # Edificio con daño parcial
            cv2.rectangle(img, (x, y), (x+w, y+h), (170, 160, 150), -1)
            # Grietas/daños
            cv2.line(img, (x, y+h//2), (x+w, y+h//2), (100, 100, 100), 1)
        
        # Carreteras con grietas
        cv2.line(img, (0, height//2), (width, height//2), (100, 100, 100), 4)
        for i in range(3):
            x = random.randint(0, width)
            cv2.circle(img, (x, height//2), 3, (80, 80, 80), -1)
    
    elif image_type == 'major-damage':
        # Imagen con daños mayores
        img.fill(120)
        
        # Estructuras muy dañadas
        for i in range(3):
            x = random.randint(20, width-40)
            y = random.randint(20, height-40)
            w = random.randint(20, 40)
            h = random.randint(20, 40)
            # Edificio colapsado parcialmente
            cv2.rectangle(img, (x, y), (x+w//2, y+h), (100, 90, 80), -1)
            cv2.rectangle(img, (x+w//2, y+h//2), (x+w, y+h), (90, 80, 70), -1)
        
        # Escombros
        for i in range(8):
            x = random.randint(0, width)
            y = random.randint(0, height)
            cv2.circle(img, (x, y), random.randint(2, 6), (70, 70, 70), -1)
    
    elif image_type == 'destroyed':
        # Imagen completamente destruida
        img.fill(60)
        
        # Solo escombros y áreas oscuras
        for i in range(15):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(5, 15)
            cv2.circle(img, (x, y), size, (random.randint(40, 80), random.randint(40, 80), random.randint(40, 80)), -1)
        
        # Áreas quemadas/destruidas
        for i in range(3):
            x = random.randint(20, width-60)
            y = random.randint(20, height-60)
            w = random.randint(30, 50)
            h = random.randint(30, 50)
            cv2.rectangle(img, (x, y), (x+w, y+h), (40, 40, 40), -1)
    
    # Añadir ruido realista
    noise = np.random.normal(0, 10, img.shape)
    img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    return img

def generate_training_dataset(num_per_class=20):
    """
    Genera un dataset sintético para entrenamiento
    """
    damage_types = ['no-damage', 'minor-damage', 'major-damage', 'destroyed']
    output_dir = Path('data/satellite_images')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🛰️ Generating synthetic satellite dataset...")
    print(f"Creating {num_per_class} images per class ({len(damage_types)} classes)")
    
    all_results = []
    
    for damage_type in damage_types:
        print(f"Creating {damage_type} images...")
        
        for i in range(num_per_class):
            # Generate image
            img = create_synthetic_satellite_image(damage_type)
            
            # Create filename
            lat = random.uniform(-90, 90)
            lon = random.uniform(-180, 180)
            filename = f"synthetic_{damage_type}_{i:03d}_{lat:.4f}_{lon:.4f}_2025-08-01.png"
            filepath = output_dir / filename
            
            # Save image
            cv2.imwrite(str(filepath), img)
            
            # Create metadata
            result = {
                'image_path': str(filepath),
                'filename': filename,
                'damage_class': damage_type,
                'coordinates': {'lat': lat, 'lon': lon},
                'synthetic': True,
                'created_date': datetime.now().isoformat()
            }
            
            all_results.append(result)
    
    # Save metadata
    metadata_path = output_dir / 'synthetic_dataset_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Create CSV for easy loading
    csv_path = output_dir / 'synthetic_dataset.csv'
    with open(csv_path, 'w', newline='') as f:
        fieldnames = ['filename', 'damage_class', 'lat', 'lon', 'image_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in all_results:
            writer.writerow({
                'filename': result['filename'],
                'damage_class': result['damage_class'],
                'lat': result['coordinates']['lat'],
                'lon': result['coordinates']['lon'],
                'image_path': result['image_path']
            })
    
    print(f"✅ Generated {len(all_results)} synthetic satellite images")
    print(f"📁 Images saved to: {output_dir}")
    print(f"📋 Metadata saved to: {metadata_path}")
    print(f"📊 CSV saved to: {csv_path}")
    
    return all_results

if __name__ == "__main__":
    # Generate synthetic dataset
    results = generate_training_dataset(num_per_class=15)
    
    print(f"\n🎯 Dataset Summary:")
    damage_counts = {}
    for result in results:
        damage_class = result['damage_class']
        damage_counts[damage_class] = damage_counts.get(damage_class, 0) + 1
    
    for damage_class, count in damage_counts.items():
        print(f"  - {damage_class}: {count} images")
    
    print(f"\nTotal images: {len(results)}")
    print("Ready for training! 🚀")
