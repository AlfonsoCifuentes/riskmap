"""
Simplified xView2 damage classifier using traditional computer vision
Clasificador simplificado de daños usando OpenCV y técnicas tradicionales
"""

import os
import cv2
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

logger = logging.getLogger(__name__)

class SimpleDamageClassifier:
    """
    Clasificador de daños simplificado usando características tradicionales de CV
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Damage classes
        self.damage_classes = {
            0: 'no-damage',
            1: 'minor-damage', 
            2: 'major-damage',
            3: 'destroyed'
        }
        
        # Models
        self.classifier = None
        self.scaler = None
        
        # Paths
        self.model_dir = Path(self.config.get('model_dir', 'models/simple_damage'))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_path = self.model_dir / 'damage_classifier.pkl'
        self.scaler_path = self.model_dir / 'feature_scaler.pkl'
        
        logger.info("Simple Damage Classifier initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'model_dir': 'models/simple_damage',
            'cache_dir': 'data/satellite_images',
            'random_seed': 42
        }
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae características de una imagen para clasificación de daños
        """
        features = []
        
        # Convert to different color spaces
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 1. Intensity features
        features.extend([
            np.mean(gray),           # Mean intensity
            np.std(gray),            # Standard deviation
            np.min(gray),            # Min intensity
            np.max(gray),            # Max intensity
            np.median(gray)          # Median intensity
        ])
        
        # 2. Texture features (using Local Binary Pattern approximation)
        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        features.extend([
            np.mean(gradient_magnitude),
            np.std(gradient_magnitude),
            np.max(gradient_magnitude)
        ])
        
        # 3. Edge features
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Count edge segments
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        edge_segments = len(contours)
        
        features.extend([
            edge_density,
            edge_segments,
            np.mean([cv2.contourArea(c) for c in contours]) if contours else 0
        ])
        
        # 4. Color features
        # Mean and std in each channel
        for channel in range(3):
            features.extend([
                np.mean(image[:, :, channel]),
                np.std(image[:, :, channel])
            ])
        
        # HSV features
        features.extend([
            np.mean(hsv[:, :, 0]),  # Hue
            np.mean(hsv[:, :, 1]),  # Saturation
            np.mean(hsv[:, :, 2])   # Value
        ])
        
        # 5. Structural features
        # Line detection using HoughLines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
        line_count = len(lines) if lines is not None else 0
        features.append(line_count)
        
        # Corner detection
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)
        corner_count = len(corners) if corners is not None else 0
        features.append(corner_count)
        
        # 6. Histogram features
        hist_gray = cv2.calcHist([gray], [0], None, [16], [0, 256])
        hist_features = hist_gray.flatten() / (gray.shape[0] * gray.shape[1])
        features.extend(hist_features)
        
        return np.array(features, dtype=np.float32)
    
    def simulate_damage_labels(self, features_list: List[np.ndarray]) -> np.ndarray:
        """
        Simula etiquetas de daño basadas en características de imagen
        """
        labels = []
        
        for features in features_list:
            # Extract key features for heuristic classification
            mean_intensity = features[0]
            std_intensity = features[1]
            edge_density = features[8]
            line_count = features[-2]
            corner_count = features[-1]
            
            # Heuristic rules for damage classification
            if mean_intensity < 60 and std_intensity < 15 and edge_density < 0.02:
                # Very dark, low variation, few edges -> destroyed
                label = 3
            elif mean_intensity < 100 and (edge_density < 0.05 or line_count < 5):
                # Dark with few structural elements -> major damage
                label = 2
            elif std_intensity < 20 or corner_count < 10:
                # Low variation or few corners -> minor damage
                label = 1
            else:
                # Normal characteristics -> no damage
                label = 0
            
            labels.append(label)
        
        return np.array(labels)
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara datos de entrenamiento desde imágenes satelitales
        """
        cache_dir = Path(self.config['cache_dir'])
        
        # Try to load synthetic dataset with labels first
        csv_path = cache_dir / 'synthetic_dataset.csv'
        if csv_path.exists():
            return self._load_labeled_dataset(csv_path)
        
        # Fallback to regular satellite images
        image_files = list(cache_dir.glob('*.png'))
        image_files.extend(list(cache_dir.glob('*.jpg')))
        
        if not image_files:
            logger.error("No satellite images found for training")
            return None, None
        
        logger.info(f"Processing {len(image_files)} images for training...")
        
        features_list = []
        
        for img_path in image_files:
            try:
                # Load and resize image
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                # Resize to standard size
                img = cv2.resize(img, (256, 256))
                
                # Extract features
                features = self.extract_features(img)
                features_list.append(features)
                
            except Exception as e:
                logger.warning(f"Error processing {img_path}: {e}")
                continue
        
        if not features_list:
            logger.error("No features extracted from images")
            return None, None
        
        # Convert to arrays
        X = np.array(features_list)
        
        # Generate labels using heuristics
        y = self.simulate_damage_labels(features_list)
        
        logger.info(f"Prepared {len(X)} samples with {X.shape[1]} features")
        logger.info(f"Label distribution: {np.bincount(y)}")
        
        return X, y
    
    def _load_labeled_dataset(self, csv_path: Path) -> Tuple[np.ndarray, np.ndarray]:
        """
        Carga dataset etiquetado desde CSV
        """
        import pandas as pd
        
        df = pd.read_csv(csv_path)
        logger.info(f"Loading labeled dataset with {len(df)} samples")
        
        # Create reverse mapping for damage classes
        class_to_label = {v: k for k, v in self.damage_classes.items()}
        
        features_list = []
        labels = []
        
        for _, row in df.iterrows():
            try:
                img_path = row['image_path']
                damage_class = row['damage_class']
                
                # Load and process image
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                img = cv2.resize(img, (256, 256))
                features = self.extract_features(img)
                
                # Get label
                label = class_to_label.get(damage_class, 0)
                
                features_list.append(features)
                labels.append(label)
                
            except Exception as e:
                logger.warning(f"Error processing {row['image_path']}: {e}")
                continue
        
        if not features_list:
            logger.error("No features extracted from labeled dataset")
            return None, None
        
        X = np.array(features_list)
        y = np.array(labels)
        
        logger.info(f"Loaded {len(X)} labeled samples with {X.shape[1]} features")
        logger.info(f"Label distribution: {np.bincount(y)}")
        
        return X, y
    
    def train(self) -> bool:
        """
        Entrena el clasificador de daños
        """
        logger.info("Starting damage classifier training...")
        
        # Prepare data
        X, y = self.prepare_training_data()
        
        if X is None or y is None:
            logger.error("No training data available")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train classifier
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Training completed. Accuracy: {accuracy:.4f}")
        
        # Print detailed results
        unique_classes = np.unique(y_test)
        class_names = [self.damage_classes[i] for i in unique_classes]
        
        report = classification_report(
            y_test, y_pred,
            labels=unique_classes,
            target_names=class_names,
            output_dict=True,
            zero_division=0
        )
        
        logger.info("Classification Report:")
        for class_name, metrics in report.items():
            if isinstance(metrics, dict) and 'f1-score' in metrics:
                logger.info(f"  {class_name}: F1={metrics['f1-score']:.3f}, "
                          f"Precision={metrics['precision']:.3f}, "
                          f"Recall={metrics['recall']:.3f}")
        
        # Save model and scaler
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.classifier, f)
        
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save training info
        training_info = {
            'accuracy': float(accuracy),
            'classification_report': report,
            'feature_count': int(X.shape[1]),
            'training_samples': int(len(X_train)),
            'test_samples': int(len(X_test)),
            'training_date': datetime.now().isoformat()
        }
        
        info_path = self.model_dir / 'training_info.json'
        with open(info_path, 'w') as f:
            json.dump(training_info, f, indent=2)
        
        logger.info(f"Model saved to {self.model_path}")
        return True
    
    def load_model(self) -> bool:
        """
        Carga un modelo previamente entrenado
        """
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.classifier = pickle.load(f)
                
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                logger.info("Model loaded successfully")
                return True
            else:
                logger.warning("No trained model found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Predice el nivel de daño en una imagen
        """
        if self.classifier is None or self.scaler is None:
            if not self.load_model():
                raise ValueError("No trained model available")
        
        try:
            # Load and preprocess image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            img = cv2.resize(img, (256, 256))
            
            # Extract features
            features = self.extract_features(img)
            features_scaled = self.scaler.transform([features])
            
            # Predict
            prediction = self.classifier.predict(features_scaled)[0]
            probabilities = self.classifier.predict_proba(features_scaled)[0]
            
            result = {
                'damage_class': self.damage_classes[prediction],
                'confidence': float(probabilities[prediction]),
                'all_probabilities': {
                    self.damage_classes[i]: float(prob) 
                    for i, prob in enumerate(probabilities)
                },
                'risk_level': self._get_risk_level(prediction),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting damage: {e}")
            return {
                'error': str(e),
                'damage_class': 'unknown',
                'confidence': 0.0
            }
    
    def _get_risk_level(self, damage_class: int) -> str:
        """Convierte clase de daño a nivel de riesgo"""
        risk_mapping = {
            0: 'low',      # no-damage
            1: 'medium',   # minor-damage
            2: 'high',     # major-damage
            3: 'critical'  # destroyed
        }
        return risk_mapping.get(damage_class, 'unknown')
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtiene información del modelo"""
        info = {
            'model_exists': self.model_path.exists(),
            'model_path': str(self.model_path),
            'damage_classes': self.damage_classes,
            'model_type': 'RandomForestClassifier'
        }
        
        # Add training info if available
        info_path = self.model_dir / 'training_info.json'
        if info_path.exists():
            try:
                with open(info_path, 'r') as f:
                    training_info = json.load(f)
                info['training_info'] = training_info
            except:
                pass
        
        return info


def main():
    """Función principal para entrenamiento"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'model_dir': 'models/simple_damage',
        'cache_dir': 'data/satellite_images'
    }
    
    # Initialize classifier
    classifier = SimpleDamageClassifier(config)
    
    print("🛰️ Starting Simple Damage Assessment Training...")
    
    # Train model
    try:
        success = classifier.train()
        
        if success:
            print("✅ Training completed successfully!")
            
            # Test prediction on sample image
            cache_dir = Path(config['cache_dir'])
            sample_images = list(cache_dir.glob('*.png'))
            
            if sample_images:
                sample_img = sample_images[0]
                result = classifier.predict(str(sample_img))
                
                print(f"\n📊 Sample prediction for {sample_img.name}:")
                print(f"   Damage class: {result['damage_class']}")
                print(f"   Confidence: {result['confidence']:.2%}")
                print(f"   Risk level: {result['risk_level']}")
        else:
            print("❌ Training failed!")
    
    except Exception as e:
        print(f"❌ Error during training: {e}")


if __name__ == "__main__":
    main()
