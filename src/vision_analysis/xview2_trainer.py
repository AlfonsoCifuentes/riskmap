"""
xView2 Integration for Satellite Damage Assessment
Integración del modelo xView2 para evaluación de daños en imágenes satelitales
"""

import os
import sys
import logging
import json
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pickle

# Add model path to sys.path
model_path = Path(__file__).parent.parent.parent / "models" / "xView2_baseline-master"
sys.path.append(str(model_path))

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

# Import from our existing satellite analysis
from .satellite_analysis import SatelliteImageAnalyzer

logger = logging.getLogger(__name__)

class XView2DamageClassifier:
    """
    Clasificador de daños usando xView2 integrado con nuestro sistema satelital
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # xView2 damage categories
        self.damage_classes = {
            0: 'no-damage',
            1: 'minor-damage', 
            2: 'major-damage',
            3: 'destroyed'
        }
        
        # Model configuration
        self.model = None
        self.image_size = (128, 128)  # Standard size for damage assessment
        self.num_classes = 4
        
        # Training configuration
        self.batch_size = 32
        self.epochs = 50
        self.learning_rate = 0.001
        
        # Paths
        self.model_dir = Path(self.config.get('model_dir', 'models/xview2_damage'))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.weights_path = self.model_dir / 'xview2_damage_model.h5'
        self.history_path = self.model_dir / 'training_history.json'
        
        logger.info("XView2 Damage Classifier initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'model_dir': 'models/xview2_damage',
            'data_dir': 'data/xview2',
            'cache_dir': 'data/satellite_images',
            'use_gpu': True,
            'random_seed': 42
        }
    
    def build_model(self) -> models.Model:
        """
        Construye el modelo de clasificación de daños basado en ResNet50
        """
        # Base model (ResNet50 pre-trained)
        base_model = ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.image_size, 3)
        )
        
        # Freeze base model initially
        base_model.trainable = False
        
        # Add custom classification head
        model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', 'sparse_categorical_crossentropy']
        )
        
        self.model = model
        logger.info(f"Model built with {model.count_params():,} parameters")
        
        return model
    
    def preprocess_satellite_data(self, satellite_images: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocesa imágenes satelitales para entrenamiento
        """
        X = []
        y = []
        
        logger.info(f"Preprocessing {len(satellite_images)} satellite images...")
        
        for img_path in satellite_images:
            try:
                # Load image
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                    
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, self.image_size)
                img = img.astype(np.float32) / 255.0
                
                # For now, simulate damage labels based on image characteristics
                # In real scenario, you would have labeled xView2 data
                damage_label = self._simulate_damage_label(img)
                
                X.append(img)
                y.append(damage_label)
                
            except Exception as e:
                logger.warning(f"Error processing {img_path}: {e}")
                continue
        
        return np.array(X), np.array(y)
    
    def _simulate_damage_label(self, img: np.ndarray) -> int:
        """
        Simula etiquetas de daño basadas en características de la imagen
        En un escenario real, usarías datos etiquetados de xView2
        """
        # Analyze image characteristics
        gray = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        
        # Calculate features
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)
        edge_density = len(cv2.Canny(gray, 50, 150).nonzero()[0]) / gray.size
        
        # Simple heuristic for damage classification
        if mean_intensity < 50 and std_intensity < 20:
            return 3  # destroyed (very dark, low variance)
        elif mean_intensity < 80 and edge_density < 0.05:
            return 2  # major-damage
        elif edge_density < 0.1:
            return 1  # minor-damage
        else:
            return 0  # no-damage
    
    def load_xview2_dataset(self, data_dir: str = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Carga el dataset xView2 si está disponible
        """
        data_dir = data_dir or self.config.get('data_dir')
        
        if not os.path.exists(data_dir):
            logger.warning(f"xView2 dataset not found at {data_dir}")
            return None, None
        
        # Try to load processed xView2 data
        try:
            # Look for processed CSV files
            train_csv = os.path.join(data_dir, 'train.csv')
            if os.path.exists(train_csv):
                df = pd.read_csv(train_csv)
                
                X = []
                y = df['labels'].values
                
                for uuid in df['uuid']:
                    img_path = os.path.join(data_dir, 'images', uuid)
                    if os.path.exists(img_path):
                        img = cv2.imread(img_path)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = cv2.resize(img, self.image_size)
                        img = img.astype(np.float32) / 255.0
                        X.append(img)
                
                return np.array(X), y
                
        except Exception as e:
            logger.error(f"Error loading xView2 dataset: {e}")
        
        return None, None
    
    def train_model(self, use_satellite_data: bool = True, use_xview2_data: bool = True):
        """
        Entrena el modelo usando datos satelitales y/o xView2
        """
        logger.info("Starting model training...")
        
        # Build model if not exists
        if self.model is None:
            self.build_model()
        
        X_all = []
        y_all = []
        
        # Load xView2 data if available
        if use_xview2_data:
            X_xview2, y_xview2 = self.load_xview2_dataset()
            if X_xview2 is not None:
                X_all.append(X_xview2)
                y_all.append(y_xview2)
                logger.info(f"Loaded {len(X_xview2)} xView2 samples")
        
        # Load satellite data from our system
        if use_satellite_data:
            satellite_images = list(Path(self.config['cache_dir']).glob('*.png'))
            satellite_images.extend(list(Path(self.config['cache_dir']).glob('*.jpg')))
            
            if satellite_images:
                X_sat, y_sat = self.preprocess_satellite_data(satellite_images)
                if len(X_sat) > 0:
                    X_all.append(X_sat)
                    y_all.append(y_sat)
                    logger.info(f"Loaded {len(X_sat)} satellite samples")
        
        if not X_all:
            logger.error("No training data available!")
            return None
        
        # Combine all data
        X = np.vstack(X_all)
        y = np.concatenate(y_all)
        
        logger.info(f"Total training samples: {len(X)}")
        logger.info(f"Class distribution: {np.bincount(y)}")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Calculate class weights for imbalanced data
        class_weights = compute_class_weight(
            'balanced',
            classes=np.unique(y_train),
            y=y_train
        )
        class_weight_dict = dict(enumerate(class_weights))
        
        # Data augmentation
        datagen = ImageDataGenerator(
            rotation_range=20,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            vertical_flip=True,
            zoom_range=0.1,
            shear_range=0.1,
            fill_mode='nearest'
        )
        
        # Callbacks
        callbacks = [
            keras.callbacks.ModelCheckpoint(
                self.weights_path,
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]
        
        # Train model
        history = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=self.batch_size),
            steps_per_epoch=len(X_train) // self.batch_size,
            epochs=self.epochs,
            validation_data=(X_val, y_val),
            class_weight=class_weight_dict,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save training history
        with open(self.history_path, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            history_dict = {}
            for key, values in history.history.items():
                history_dict[key] = [float(v) for v in values]
            json.dump(history_dict, f, indent=2)
        
        # Evaluate model
        val_loss, val_accuracy, _ = self.model.evaluate(X_val, y_val, verbose=0)
        logger.info(f"Validation accuracy: {val_accuracy:.4f}")
        
        # Generate classification report
        y_pred = self.model.predict(X_val)
        y_pred_classes = np.argmax(y_pred, axis=1)
        
        report = classification_report(
            y_val, y_pred_classes,
            target_names=list(self.damage_classes.values()),
            output_dict=True
        )
        
        # Save evaluation results
        eval_results = {
            'validation_accuracy': float(val_accuracy),
            'validation_loss': float(val_loss),
            'classification_report': report,
            'confusion_matrix': confusion_matrix(y_val, y_pred_classes).tolist(),
            'training_date': datetime.now().isoformat()
        }
        
        eval_path = self.model_dir / 'evaluation_results.json'
        with open(eval_path, 'w') as f:
            json.dump(eval_results, f, indent=2)
        
        logger.info("Model training completed!")
        return history
    
    def load_model(self) -> bool:
        """Carga un modelo previamente entrenado"""
        try:
            if self.weights_path.exists():
                if self.model is None:
                    self.build_model()
                self.model.load_weights(self.weights_path)
                logger.info("Model loaded successfully")
                return True
            else:
                logger.warning("No trained model found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_damage(self, image_path: str) -> Dict[str, Any]:
        """
        Predice el nivel de daño en una imagen satelital
        """
        if self.model is None:
            if not self.load_model():
                raise ValueError("No trained model available")
        
        try:
            # Load and preprocess image
            img = cv2.imread(str(image_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, self.image_size)
            img = img.astype(np.float32) / 255.0
            img = np.expand_dims(img, axis=0)
            
            # Predict
            predictions = self.model.predict(img, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            result = {
                'damage_class': self.damage_classes[predicted_class],
                'confidence': confidence,
                'all_probabilities': {
                    self.damage_classes[i]: float(prob) 
                    for i, prob in enumerate(predictions[0])
                },
                'risk_level': self._get_risk_level(predicted_class),
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
            'model_exists': self.weights_path.exists(),
            'model_path': str(self.weights_path),
            'damage_classes': self.damage_classes,
            'image_size': self.image_size,
            'num_classes': self.num_classes
        }
        
        # Add training history if available
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    info['training_history'] = json.load(f)
            except:
                pass
        
        # Add evaluation results if available
        eval_path = self.model_dir / 'evaluation_results.json'
        if eval_path.exists():
            try:
                with open(eval_path, 'r') as f:
                    info['evaluation_results'] = json.load(f)
            except:
                pass
        
        return info


def main():
    """Función principal para entrenamiento del modelo"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'model_dir': 'models/xview2_damage',
        'data_dir': 'models/xView2_baseline-master/data',
        'cache_dir': 'data/satellite_images'
    }
    
    # Initialize trainer
    trainer = XView2DamageClassifier(config)
    
    print("🛰️ Starting xView2 Damage Assessment Training...")
    print(f"Model directory: {trainer.model_dir}")
    print(f"Data directory: {config['data_dir']}")
    
    # Train model
    try:
        history = trainer.train_model(
            use_satellite_data=True,
            use_xview2_data=True
        )
        
        if history:
            print("✅ Training completed successfully!")
            
            # Test prediction on sample image
            sample_images = list(Path(config['cache_dir']).glob('*.png'))
            if sample_images:
                sample_img = sample_images[0]
                result = trainer.predict_damage(str(sample_img))
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
