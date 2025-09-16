"""
Computer Vision Analysis Module for Conflict Monitoring
Implements YOLOv8, Segment Anything, and custom models for analyzing
satellite imagery, detecting military assets, damage assessment, and crowd analysis.
"""

import logging
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from ultralytics import YOLO
import torch
from PIL import Image
import requests
from io import BytesIO
import base64
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class ConflictVisionAnalyzer:
    """
    Advanced computer vision analyzer for conflict-related imagery
    Uses YOLOv8 and custom models for detecting military assets, damage, and crowds
    """
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.yolo_model = None
        self.damage_detector = None
        self.crowd_analyzer = None
        self.military_detector = None
        self.model_path = model_path
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all computer vision models"""
        try:
            logger.info("Initializing computer vision models...")
            
            # Load YOLOv8 model
            self.yolo_model = YOLO(self.model_path)
            
            # Initialize custom detectors
            self._initialize_damage_detector()
            self._initialize_crowd_analyzer()
            self._initialize_military_detector()
            
            logger.info("Computer vision models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing CV models: {e}")
            raise
    
    def _initialize_damage_detector(self):
        """Initialize damage detection model"""
        # Custom damage detection classes
        self.damage_classes = {
            'building_damage': ['destroyed_building', 'damaged_building', 'rubble'],
            'infrastructure': ['damaged_road', 'destroyed_bridge', 'crater'],
            'fire_smoke': ['fire', 'smoke', 'explosion'],
            'flooding': ['flood', 'water_damage']
        }
    
    def _initialize_crowd_analyzer(self):
        """Initialize crowd analysis model"""
        self.crowd_classes = {
            'protest': ['crowd', 'demonstration', 'protest'],
            'military': ['soldiers', 'military_formation', 'convoy'],
            'displacement': ['refugees', 'evacuation', 'camp']
        }
    
    def _initialize_military_detector(self):
        """Initialize military asset detection"""
        self.military_classes = {
            'vehicles': ['tank', 'armored_vehicle', 'military_truck', 'helicopter'],
            'installations': ['military_base', 'checkpoint', 'fortification'],
            'weapons': ['artillery', 'missile_launcher', 'aircraft']
        }
    
    def analyze_image(self, image_input: Any, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Comprehensive image analysis for conflict monitoring
        
        Args:
            image_input: Image file path, URL, or base64 string
            analysis_type: Type of analysis ('damage', 'military', 'crowd', 'comprehensive')
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Load and preprocess image
            image = self._load_image(image_input)
            if image is None:
                return {'error': 'Failed to load image'}
            
            results = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'analysis_type': analysis_type,
                    'image_size': image.shape[:2]
                },
                'detections': {},
                'risk_assessment': {},
                'confidence_scores': {}
            }
            
            # Run YOLO detection
            yolo_results = self._run_yolo_detection(image)
            results['detections']['yolo'] = yolo_results
            
            # Specific analysis based on type
            if analysis_type in ['damage', 'comprehensive']:
                damage_results = self._analyze_damage(image, yolo_results)
                results['detections']['damage'] = damage_results
            
            if analysis_type in ['military', 'comprehensive']:
                military_results = self._analyze_military_assets(image, yolo_results)
                results['detections']['military'] = military_results
            
            if analysis_type in ['crowd', 'comprehensive']:
                crowd_results = self._analyze_crowds(image, yolo_results)
                results['detections']['crowd'] = crowd_results
            
            # Calculate overall risk assessment
            results['risk_assessment'] = self._calculate_risk_assessment(results['detections'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {'error': str(e)}
    
    def _load_image(self, image_input: Any) -> Optional[np.ndarray]:
        """Load image from various input types"""
        try:
            if isinstance(image_input, str):
                if image_input.startswith('http'):
                    # URL
                    response = requests.get(image_input)
                    image = Image.open(BytesIO(response.content))
                    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                elif image_input.startswith('data:image'):
                    # Base64
                    header, data = image_input.split(',', 1)
                    image_data = base64.b64decode(data)
                    image = Image.open(BytesIO(image_data))
                    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                else:
                    # File path
                    return cv2.imread(image_input)
            elif isinstance(image_input, np.ndarray):
                return image_input
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return None
    
    def _run_yolo_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Run YOLOv8 object detection"""
        try:
            results = self.yolo_model(image)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = {
                            'class_id': int(box.cls[0]),
                            'class_name': self.yolo_model.names[int(box.cls[0])],
                            'confidence': float(box.conf[0]),
                            'bbox': box.xyxy[0].tolist(),
                            'center': [(box.xyxy[0][0] + box.xyxy[0][2]) / 2, 
                                     (box.xyxy[0][1] + box.xyxy[0][3]) / 2]
                        }
                        detections.append(detection)
            
            return {
                'total_detections': len(detections),
                'detections': detections,
                'classes_detected': list(set([d['class_name'] for d in detections]))
            }
            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            return {}
    
    def _analyze_damage(self, image: np.ndarray, yolo_results: Dict) -> Dict[str, Any]:
        """Analyze damage and destruction in the image"""
        try:
            damage_analysis = {
                'damage_level': 'none',
                'damage_types': [],
                'affected_areas': [],
                'severity_score': 0
            }
            
            # Look for damage-related objects in YOLO results
            damage_indicators = ['fire', 'smoke', 'debris', 'rubble']
            building_damage = 0
            infrastructure_damage = 0
            
            for detection in yolo_results.get('detections', []):
                class_name = detection['class_name'].lower()
                confidence = detection['confidence']
                
                if any(indicator in class_name for indicator in damage_indicators):
                    damage_analysis['damage_types'].append({
                        'type': class_name,
                        'confidence': confidence,
                        'location': detection['bbox']
                    })
                
                if 'building' in class_name or 'house' in class_name:
                    building_damage += 1
                
                if any(infra in class_name for infra in ['road', 'bridge', 'infrastructure']):
                    infrastructure_damage += 1
            
            # Calculate damage level
            total_damage_objects = len(damage_analysis['damage_types'])
            if total_damage_objects == 0:
                damage_analysis['damage_level'] = 'none'
                damage_analysis['severity_score'] = 0
            elif total_damage_objects <= 2:
                damage_analysis['damage_level'] = 'light'
                damage_analysis['severity_score'] = 25
            elif total_damage_objects <= 5:
                damage_analysis['damage_level'] = 'moderate'
                damage_analysis['severity_score'] = 50
            elif total_damage_objects <= 10:
                damage_analysis['damage_level'] = 'heavy'
                damage_analysis['severity_score'] = 75
            else:
                damage_analysis['damage_level'] = 'severe'
                damage_analysis['severity_score'] = 100
            
            # Additional image analysis for damage patterns
            damage_analysis.update(self._analyze_damage_patterns(image))
            
            return damage_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing damage: {e}")
            return {}
    
    def _analyze_damage_patterns(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze damage patterns using image processing techniques"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges (useful for finding destroyed structures)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Analyze color distribution (fires, smoke often have distinct colors)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Fire/explosion detection (red-orange hues)
            fire_mask = cv2.inRange(hsv, (0, 50, 50), (20, 255, 255))
            fire_percentage = np.sum(fire_mask > 0) / fire_mask.size * 100
            
            # Smoke detection (gray areas)
            smoke_mask = cv2.inRange(hsv, (0, 0, 50), (180, 50, 200))
            smoke_percentage = np.sum(smoke_mask > 0) / smoke_mask.size * 100
            
            return {
                'edge_density': float(edge_density),
                'fire_percentage': float(fire_percentage),
                'smoke_percentage': float(smoke_percentage),
                'structural_integrity': 'compromised' if edge_density > 0.1 else 'intact'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing damage patterns: {e}")
            return {}
    
    def _analyze_military_assets(self, image: np.ndarray, yolo_results: Dict) -> Dict[str, Any]:
        """Analyze military assets and equipment in the image"""
        try:
            military_analysis = {
                'military_presence': False,
                'asset_types': [],
                'threat_level': 'low',
                'asset_count': 0
            }
            
            # Military-related object classes
            military_objects = ['truck', 'car', 'motorcycle', 'airplane', 'helicopter']
            potential_military = []
            
            for detection in yolo_results.get('detections', []):
                class_name = detection['class_name'].lower()
                confidence = detection['confidence']
                
                if class_name in military_objects:
                    potential_military.append({
                        'type': class_name,
                        'confidence': confidence,
                        'location': detection['bbox']
                    })
            
            # Analyze formations and patterns
            if len(potential_military) > 0:
                military_analysis['military_presence'] = True
                military_analysis['asset_types'] = potential_military
                military_analysis['asset_count'] = len(potential_military)
                
                # Determine threat level based on asset count and types
                if military_analysis['asset_count'] >= 10:
                    military_analysis['threat_level'] = 'high'
                elif military_analysis['asset_count'] >= 5:
                    military_analysis['threat_level'] = 'medium'
                else:
                    military_analysis['threat_level'] = 'low'
            
            # Additional analysis for military formations
            military_analysis.update(self._analyze_military_formations(potential_military))
            
            return military_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing military assets: {e}")
            return {}
    
    def _analyze_military_formations(self, military_objects: List[Dict]) -> Dict[str, Any]:
        """Analyze military formations and patterns"""
        try:
            if len(military_objects) < 2:
                return {'formation_detected': False}
            
            # Extract positions
            positions = []
            for obj in military_objects:
                bbox = obj['location']
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                positions.append([center_x, center_y])
            
            positions = np.array(positions)
            
            # Analyze clustering
            from sklearn.cluster import DBSCAN
            clustering = DBSCAN(eps=100, min_samples=2).fit(positions)
            n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            
            return {
                'formation_detected': n_clusters > 0,
                'cluster_count': n_clusters,
                'formation_type': 'convoy' if n_clusters == 1 else 'distributed'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing formations: {e}")
            return {'formation_detected': False}
    
    def _analyze_crowds(self, image: np.ndarray, yolo_results: Dict) -> Dict[str, Any]:
        """Analyze crowds and gatherings in the image"""
        try:
            crowd_analysis = {
                'crowd_detected': False,
                'crowd_size': 0,
                'crowd_density': 'low',
                'gathering_type': 'unknown'
            }
            
            # Count people in the image
            people_count = 0
            people_locations = []
            
            for detection in yolo_results.get('detections', []):
                if detection['class_name'].lower() == 'person':
                    people_count += 1
                    people_locations.append(detection['center'])
            
            crowd_analysis['crowd_size'] = people_count
            
            if people_count > 10:
                crowd_analysis['crowd_detected'] = True
                
                # Analyze crowd density
                if people_count > 100:
                    crowd_analysis['crowd_density'] = 'very_high'
                elif people_count > 50:
                    crowd_analysis['crowd_density'] = 'high'
                elif people_count > 20:
                    crowd_analysis['crowd_density'] = 'medium'
                else:
                    crowd_analysis['crowd_density'] = 'low'
                
                # Analyze gathering patterns
                crowd_analysis.update(self._analyze_gathering_patterns(people_locations))
            
            return crowd_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing crowds: {e}")
            return {}
    
    def _analyze_gathering_patterns(self, people_locations: List[List[float]]) -> Dict[str, Any]:
        """Analyze patterns in crowd gatherings"""
        try:
            if len(people_locations) < 10:
                return {'pattern': 'sparse'}
            
            positions = np.array(people_locations)
            
            # Calculate density
            from scipy.spatial.distance import pdist
            distances = pdist(positions)
            avg_distance = np.mean(distances)
            
            # Determine pattern type
            if avg_distance < 50:
                pattern = 'dense_gathering'
                gathering_type = 'protest_or_demonstration'
            elif avg_distance < 100:
                pattern = 'moderate_gathering'
                gathering_type = 'public_event'
            else:
                pattern = 'dispersed'
                gathering_type = 'normal_activity'
            
            return {
                'pattern': pattern,
                'gathering_type': gathering_type,
                'average_distance': float(avg_distance)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing gathering patterns: {e}")
            return {'pattern': 'unknown'}
    
    def _calculate_risk_assessment(self, detections: Dict) -> Dict[str, Any]:
        """Calculate overall risk assessment based on all detections"""
        try:
            risk_factors = []
            total_risk_score = 0
            
            # Damage assessment contribution
            if 'damage' in detections:
                damage_score = detections['damage'].get('severity_score', 0)
                total_risk_score += damage_score * 0.4  # 40% weight
                if damage_score > 50:
                    risk_factors.append('significant_damage_detected')
            
            # Military presence contribution
            if 'military' in detections:
                military_presence = detections['military'].get('military_presence', False)
                asset_count = detections['military'].get('asset_count', 0)
                if military_presence:
                    military_score = min(asset_count * 10, 100)
                    total_risk_score += military_score * 0.3  # 30% weight
                    risk_factors.append('military_assets_detected')
            
            # Crowd analysis contribution
            if 'crowd' in detections:
                crowd_detected = detections['crowd'].get('crowd_detected', False)
                crowd_size = detections['crowd'].get('crowd_size', 0)
                if crowd_detected:
                    crowd_score = min(crowd_size * 2, 100)
                    total_risk_score += crowd_score * 0.3  # 30% weight
                    risk_factors.append('large_gathering_detected')
            
            # Determine risk level
            if total_risk_score >= 80:
                risk_level = 'critical'
            elif total_risk_score >= 60:
                risk_level = 'high'
            elif total_risk_score >= 40:
                risk_level = 'medium'
            elif total_risk_score >= 20:
                risk_level = 'low'
            else:
                risk_level = 'minimal'
            
            return {
                'overall_risk_score': min(total_risk_score, 100),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk assessment: {e}")
            return {'overall_risk_score': 0, 'risk_level': 'unknown'}
    
    def analyze_satellite_imagery(self, image_input: Any, coordinates: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Specialized analysis for satellite imagery
        
        Args:
            image_input: Satellite image input
            coordinates: Optional GPS coordinates (lat, lon)
            
        Returns:
            Satellite imagery analysis results
        """
        try:
            # Load image
            image = self._load_image(image_input)
            if image is None:
                return {'error': 'Failed to load satellite image'}
            
            # Run comprehensive analysis
            base_analysis = self.analyze_image(image, 'comprehensive')
            
            # Add satellite-specific analysis
            satellite_analysis = {
                'image_type': 'satellite',
                'coordinates': coordinates,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Terrain and infrastructure analysis
            terrain_analysis = self._analyze_terrain(image)
            satellite_analysis['terrain'] = terrain_analysis
            
            # Change detection (if historical data available)
            # This would require comparison with previous images
            satellite_analysis['change_detection'] = {
                'available': False,
                'note': 'Requires historical imagery for comparison'
            }
            
            # Combine with base analysis
            base_analysis.update(satellite_analysis)
            
            return base_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing satellite imagery: {e}")
            return {'error': str(e)}
    
    def _analyze_terrain(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze terrain features in satellite imagery"""
        try:
            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Vegetation detection (green areas)
            vegetation_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
            vegetation_percentage = np.sum(vegetation_mask > 0) / vegetation_mask.size * 100
            
            # Water detection (blue areas)
            water_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
            water_percentage = np.sum(water_mask > 0) / water_mask.size * 100
            
            # Urban areas (gray/white areas)
            urban_mask = cv2.inRange(hsv, (0, 0, 100), (180, 30, 255))
            urban_percentage = np.sum(urban_mask > 0) / urban_mask.size * 100
            
            return {
                'vegetation_percentage': float(vegetation_percentage),
                'water_percentage': float(water_percentage),
                'urban_percentage': float(urban_percentage),
                'terrain_type': self._classify_terrain_type(vegetation_percentage, water_percentage, urban_percentage)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing terrain: {e}")
            return {}
    
    def _classify_terrain_type(self, vegetation: float, water: float, urban: float) -> str:
        """Classify terrain type based on percentages"""
        if urban > 30:
            return 'urban'
        elif water > 20:
            return 'coastal_or_riverine'
        elif vegetation > 60:
            return 'forested'
        elif vegetation > 30:
            return 'mixed_vegetation'
        else:
            return 'arid_or_desert'