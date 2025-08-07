"""
Alert System
============

Sistema de alertas y notificaciones para detección de riesgos:
- Gestión de alertas
- Reglas de notificación
- Integración con sistemas externos
- Base de datos de alertas
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from pathlib import Path
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.image import MimeImage
import uuid

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Gestor principal de alertas
    """
    
    # Niveles de severidad
    SEVERITY_LEVELS = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    
    # Tipos de alerta
    ALERT_TYPES = {
        'manifestation': 'Manifestación/Multitud',
        'weapon_detected': 'Arma Detectada',
        'fire_smoke': 'Fuego/Humo',
        'traffic_jam': 'Atasco de Tráfico',
        'crowd_density': 'Alta Densidad de Personas',
        'suspicious_activity': 'Actividad Sospechosa',
        'vehicle_anomaly': 'Anomalía Vehicular',
        'perimeter_breach': 'Violación de Perímetro',
        'system_error': 'Error del Sistema'
    }
    
    def __init__(self, db_path: str = "alerts.db"):
        """
        Inicializar el gestor de alertas
        
        Args:
            db_path: Ruta a la base de datos de alertas
        """
        self.db_path = db_path
        self.notification_rules = {}
        self.active_alerts = {}
        self.alert_lock = threading.Lock()
        
        # Configuración de notificaciones
        self.email_config = self._load_email_config()
        self.webhook_config = self._load_webhook_config()
        
        # Callbacks para notificaciones en tiempo real
        self.notification_callbacks = []
        
        # Inicializar base de datos
        self._init_database()
        
        # Cargar reglas de notificación
        self._load_notification_rules()
        
        logger.info("🚨 AlertManager inicializado")
    
    def _init_database(self):
        """Inicializar base de datos de alertas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla principal de alertas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    cam_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    confidence REAL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME,
                    resolved_by TEXT,
                    resolution_notes TEXT,
                    video_path TEXT,
                    thumbnail_path TEXT,
                    zone_id TEXT,
                    latitude REAL,
                    longitude REAL
                )
            ''')
            
            # Tabla de notificaciones enviadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    recipient TEXT,
                    status TEXT DEFAULT 'pending',
                    sent_at DATETIME,
                    error_message TEXT,
                    FOREIGN KEY (alert_id) REFERENCES alerts (id)
                )
            ''')
            
            # Tabla de reglas de notificación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para optimización
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_cam_id ON alerts (cam_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts (alert_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts (resolved)')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Base de datos de alertas inicializada")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
    
    def _load_email_config(self) -> Dict:
        """Cargar configuración de email"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL'),
            'enabled': os.getenv('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true'
        }
    
    def _load_webhook_config(self) -> Dict:
        """Cargar configuración de webhooks"""
        return {
            'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
            'discord_webhook': os.getenv('DISCORD_WEBHOOK_URL'),
            'teams_webhook': os.getenv('TEAMS_WEBHOOK_URL'),
            'generic_webhook': os.getenv('GENERIC_WEBHOOK_URL'),
            'enabled': os.getenv('WEBHOOK_ALERTS_ENABLED', 'false').lower() == 'true'
        }
    
    def _load_notification_rules(self):
        """Cargar reglas de notificación desde la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, conditions, actions, enabled 
                FROM notification_rules 
                WHERE enabled = TRUE
            ''')
            
            rules = cursor.fetchall()
            
            for rule_id, name, conditions_json, actions_json, enabled in rules:
                try:
                    conditions = json.loads(conditions_json)
                    actions = json.loads(actions_json)
                    
                    self.notification_rules[rule_id] = {
                        'name': name,
                        'conditions': conditions,
                        'actions': actions,
                        'enabled': enabled
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parseando regla {rule_id}: {e}")
            
            conn.close()
            
            logger.info(f"📋 {len(self.notification_rules)} reglas de notificación cargadas")
            
        except Exception as e:
            logger.error(f"❌ Error cargando reglas de notificación: {e}")
    
    def create_alert(self, 
                    cam_id: str,
                    alert_type: str,
                    severity: str,
                    title: str,
                    description: str,
                    confidence: float = 1.0,
                    metadata: Optional[Dict] = None,
                    video_path: Optional[str] = None,
                    thumbnail_path: Optional[str] = None,
                    zone_id: Optional[str] = None,
                    latitude: Optional[float] = None,
                    longitude: Optional[float] = None) -> str:
        """
        Crear nueva alerta
        
        Returns:
            ID de la alerta creada
        """
        try:
            alert_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Validar parámetros
            if alert_type not in self.ALERT_TYPES:
                logger.warning(f"⚠️ Tipo de alerta desconocido: {alert_type}")
            
            if severity not in self.SEVERITY_LEVELS:
                logger.warning(f"⚠️ Nivel de severidad desconocido: {severity}")
                severity = 'medium'
            
            # Preparar metadata
            metadata_json = json.dumps(metadata or {})
            
            # Guardar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (
                    id, cam_id, alert_type, severity, title, description,
                    confidence, metadata, timestamp, video_path, thumbnail_path,
                    zone_id, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id, cam_id, alert_type, severity, title, description,
                confidence, metadata_json, timestamp, video_path, thumbnail_path,
                zone_id, latitude, longitude
            ))
            
            conn.commit()
            conn.close()
            
            # Agregar a alertas activas
            with self.alert_lock:
                self.active_alerts[alert_id] = {
                    'id': alert_id,
                    'cam_id': cam_id,
                    'alert_type': alert_type,
                    'severity': severity,
                    'title': title,
                    'description': description,
                    'confidence': confidence,
                    'metadata': metadata or {},
                    'timestamp': timestamp.isoformat(),
                    'resolved': False,
                    'video_path': video_path,
                    'thumbnail_path': thumbnail_path,
                    'zone_id': zone_id,
                    'latitude': latitude,
                    'longitude': longitude
                }
            
            # Procesar notificaciones
            self._process_notifications(alert_id)
            
            # Ejecutar callbacks de notificación en tiempo real
            self._trigger_real_time_notifications(self.active_alerts[alert_id])
            
            logger.info(f"🚨 Nueva alerta creada: {alert_id} ({alert_type}, {severity})")
            
            return alert_id
            
        except Exception as e:
            logger.error(f"❌ Error creando alerta: {e}")
            return ""
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system", 
                     resolution_notes: str = "") -> bool:
        """
        Resolver una alerta
        
        Args:
            alert_id: ID de la alerta
            resolved_by: Usuario que resolvió la alerta
            resolution_notes: Notas sobre la resolución
            
        Returns:
            True si se resolvió correctamente
        """
        try:
            resolved_at = datetime.now()
            
            # Actualizar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET resolved = TRUE, resolved_at = ?, resolved_by = ?, resolution_notes = ?
                WHERE id = ?
            ''', (resolved_at, resolved_by, resolution_notes, alert_id))
            
            if cursor.rowcount == 0:
                conn.close()
                logger.warning(f"⚠️ Alerta {alert_id} no encontrada")
                return False
            
            conn.commit()
            conn.close()
            
            # Actualizar alertas activas
            with self.alert_lock:
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id].update({
                        'resolved': True,
                        'resolved_at': resolved_at.isoformat(),
                        'resolved_by': resolved_by,
                        'resolution_notes': resolution_notes
                    })
            
            logger.info(f"✅ Alerta {alert_id} resuelta por {resolved_by}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resolviendo alerta {alert_id}: {e}")
            return False
    
    def _process_notifications(self, alert_id: str):
        """Procesar notificaciones para una alerta"""
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return
            
            # Evaluar reglas de notificación
            matching_rules = self._evaluate_notification_rules(alert)
            
            for rule_id in matching_rules:
                rule = self.notification_rules[rule_id]
                
                # Ejecutar acciones de la regla
                for action in rule['actions']:
                    self._execute_notification_action(alert_id, action)
            
        except Exception as e:
            logger.error(f"❌ Error procesando notificaciones para {alert_id}: {e}")
    
    def _evaluate_notification_rules(self, alert: Dict) -> List[int]:
        """Evaluar qué reglas de notificación se aplican a una alerta"""
        matching_rules = []
        
        for rule_id, rule in self.notification_rules.items():
            try:
                conditions = rule['conditions']
                
                # Evaluar condiciones
                matches = True
                
                # Verificar tipo de alerta
                if 'alert_types' in conditions:
                    if alert['alert_type'] not in conditions['alert_types']:
                        matches = False
                
                # Verificar severidad
                if 'min_severity' in conditions:
                    min_severity_level = self.SEVERITY_LEVELS.get(conditions['min_severity'], 0)
                    alert_severity_level = self.SEVERITY_LEVELS.get(alert['severity'], 0)
                    if alert_severity_level < min_severity_level:
                        matches = False
                
                # Verificar cámaras
                if 'cam_ids' in conditions:
                    if alert['cam_id'] not in conditions['cam_ids']:
                        matches = False
                
                # Verificar zonas
                if 'zone_ids' in conditions and alert.get('zone_id'):
                    if alert['zone_id'] not in conditions['zone_ids']:
                        matches = False
                
                # Verificar confianza mínima
                if 'min_confidence' in conditions:
                    if alert['confidence'] < conditions['min_confidence']:
                        matches = False
                
                # Verificar horario (opcional)
                if 'time_range' in conditions:
                    current_hour = datetime.now().hour
                    time_range = conditions['time_range']
                    if not (time_range['start'] <= current_hour <= time_range['end']):
                        matches = False
                
                if matches:
                    matching_rules.append(rule_id)
                    
            except Exception as e:
                logger.error(f"❌ Error evaluando regla {rule_id}: {e}")
        
        return matching_rules
    
    def _execute_notification_action(self, alert_id: str, action: Dict):
        """Ejecutar acción de notificación"""
        try:
            action_type = action.get('type')
            
            if action_type == 'email':
                self._send_email_notification(alert_id, action)
            elif action_type == 'webhook':
                self._send_webhook_notification(alert_id, action)
            elif action_type == 'slack':
                self._send_slack_notification(alert_id, action)
            elif action_type == 'discord':
                self._send_discord_notification(alert_id, action)
            else:
                logger.warning(f"⚠️ Tipo de acción desconocido: {action_type}")
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando acción de notificación: {e}")
    
    def _send_email_notification(self, alert_id: str, action: Dict):
        """Enviar notificación por email"""
        if not self.email_config.get('enabled'):
            return
        
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return
            
            # Preparar email
            msg = MimeMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = action.get('recipient')
            msg['Subject'] = f"[ALERTA {alert['severity'].upper()}] {alert['title']}"
            
            # Cuerpo del email
            body = f"""
            Nueva alerta detectada:
            
            Tipo: {self.ALERT_TYPES.get(alert['alert_type'], alert['alert_type'])}
            Severidad: {alert['severity'].upper()}
            Cámara: {alert['cam_id']}
            Descripción: {alert['description']}
            Confianza: {alert['confidence']:.2%}
            Timestamp: {alert['timestamp']}
            
            Ubicación: {alert.get('zone_id', 'No especificada')}
            """
            
            if alert.get('latitude') and alert.get('longitude'):
                body += f"\nCoordenadas: {alert['latitude']}, {alert['longitude']}"
            
            msg.attach(MimeText(body, 'plain'))
            
            # Adjuntar thumbnail si existe
            if alert.get('thumbnail_path') and os.path.exists(alert['thumbnail_path']):
                with open(alert['thumbnail_path'], 'rb') as f:
                    img = MimeImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename='thumbnail.jpg')
                    msg.attach(img)
            
            # Enviar email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            # Registrar notificación
            self._log_notification(alert_id, 'email', action.get('recipient'), 'sent')
            
            logger.info(f"📧 Email enviado para alerta {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando email para alerta {alert_id}: {e}")
            self._log_notification(alert_id, 'email', action.get('recipient'), 'failed', str(e))
    
    def _send_webhook_notification(self, alert_id: str, action: Dict):
        """Enviar notificación por webhook genérico"""
        if not self.webhook_config.get('enabled'):
            return
        
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return
            
            webhook_url = action.get('url') or self.webhook_config.get('generic_webhook')
            if not webhook_url:
                return
            
            # Preparar payload
            payload = {
                'alert_id': alert_id,
                'cam_id': alert['cam_id'],
                'alert_type': alert['alert_type'],
                'severity': alert['severity'],
                'title': alert['title'],
                'description': alert['description'],
                'confidence': alert['confidence'],
                'timestamp': alert['timestamp'],
                'metadata': alert['metadata']
            }
            
            # Enviar webhook
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Registrar notificación
            self._log_notification(alert_id, 'webhook', webhook_url, 'sent')
            
            logger.info(f"🔗 Webhook enviado para alerta {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando webhook para alerta {alert_id}: {e}")
            self._log_notification(alert_id, 'webhook', action.get('url'), 'failed', str(e))
    
    def _send_slack_notification(self, alert_id: str, action: Dict):
        """Enviar notificación a Slack"""
        try:
            webhook_url = self.webhook_config.get('slack_webhook')
            if not webhook_url:
                return
            
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return
            
            # Preparar mensaje para Slack
            color = {
                'low': '#36a64f',      # Verde
                'medium': '#ff9500',   # Naranja
                'high': '#ff0000',     # Rojo
                'critical': '#8B0000'  # Rojo oscuro
            }.get(alert['severity'], '#808080')
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 {alert['title']}",
                        "text": alert['description'],
                        "fields": [
                            {
                                "title": "Tipo",
                                "value": self.ALERT_TYPES.get(alert['alert_type'], alert['alert_type']),
                                "short": True
                            },
                            {
                                "title": "Severidad",
                                "value": alert['severity'].upper(),
                                "short": True
                            },
                            {
                                "title": "Cámara",
                                "value": alert['cam_id'],
                                "short": True
                            },
                            {
                                "title": "Confianza",
                                "value": f"{alert['confidence']:.2%}",
                                "short": True
                            }
                        ],
                        "ts": int(datetime.fromisoformat(alert['timestamp']).timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self._log_notification(alert_id, 'slack', 'slack_channel', 'sent')
            logger.info(f"💬 Notificación Slack enviada para alerta {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación Slack para alerta {alert_id}: {e}")
            self._log_notification(alert_id, 'slack', 'slack_channel', 'failed', str(e))
    
    def _send_discord_notification(self, alert_id: str, action: Dict):
        """Enviar notificación a Discord"""
        try:
            webhook_url = self.webhook_config.get('discord_webhook')
            if not webhook_url:
                return
            
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return
            
            # Color según severidad
            color_map = {
                'low': 0x36a64f,      # Verde
                'medium': 0xff9500,   # Naranja
                'high': 0xff0000,     # Rojo
                'critical': 0x8B0000  # Rojo oscuro
            }
            
            embed = {
                "title": f"🚨 {alert['title']}",
                "description": alert['description'],
                "color": color_map.get(alert['severity'], 0x808080),
                "fields": [
                    {
                        "name": "Tipo",
                        "value": self.ALERT_TYPES.get(alert['alert_type'], alert['alert_type']),
                        "inline": True
                    },
                    {
                        "name": "Severidad",
                        "value": alert['severity'].upper(),
                        "inline": True
                    },
                    {
                        "name": "Cámara",
                        "value": alert['cam_id'],
                        "inline": True
                    },
                    {
                        "name": "Confianza",
                        "value": f"{alert['confidence']:.2%}",
                        "inline": True
                    }
                ],
                "timestamp": alert['timestamp']
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self._log_notification(alert_id, 'discord', 'discord_channel', 'sent')
            logger.info(f"🎮 Notificación Discord enviada para alerta {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación Discord para alerta {alert_id}: {e}")
            self._log_notification(alert_id, 'discord', 'discord_channel', 'failed', str(e))
    
    def _log_notification(self, alert_id: str, notification_type: str, 
                         recipient: str, status: str, error_message: str = ""):
        """Registrar notificación en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (
                    alert_id, notification_type, recipient, status, sent_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert_id, notification_type, recipient, status, 
                datetime.now() if status == 'sent' else None, error_message
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error registrando notificación: {e}")
    
    def _trigger_real_time_notifications(self, alert: Dict):
        """Disparar callbacks de notificación en tiempo real"""
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ Error en callback de notificación: {e}")
    
    def add_notification_callback(self, callback: Callable):
        """Agregar callback para notificaciones en tiempo real"""
        self.notification_callbacks.append(callback)
    
    def get_alerts(self, 
                  resolved: Optional[bool] = None,
                  cam_id: Optional[str] = None,
                  alert_type: Optional[str] = None,
                  severity: Optional[str] = None,
                  limit: int = 50,
                  offset: int = 0) -> List[Dict]:
        """
        Obtener alertas con filtros
        
        Returns:
            Lista de alertas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Construir query con filtros
            where_conditions = []
            params = []
            
            if resolved is not None:
                where_conditions.append("resolved = ?")
                params.append(resolved)
            
            if cam_id:
                where_conditions.append("cam_id = ?")
                params.append(cam_id)
            
            if alert_type:
                where_conditions.append("alert_type = ?")
                params.append(alert_type)
            
            if severity:
                where_conditions.append("severity = ?")
                params.append(severity)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f'''
                SELECT * FROM alerts 
                {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alert = dict(row)
                # Parsear metadata JSON
                if alert['metadata']:
                    try:
                        alert['metadata'] = json.loads(alert['metadata'])
                    except:
                        alert['metadata'] = {}
                alerts.append(alert)
            
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo alertas: {e}")
            return []
    
    def get_alert_statistics(self) -> Dict:
        """Obtener estadísticas de alertas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = FALSE")
            active_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE DATE(timestamp) = DATE('now')")
            today_alerts = cursor.fetchone()[0]
            
            # Por severidad
            cursor.execute('''
                SELECT severity, COUNT(*) 
                FROM alerts 
                WHERE resolved = FALSE
                GROUP BY severity
            ''')
            severity_counts = dict(cursor.fetchall())
            
            # Por tipo
            cursor.execute('''
                SELECT alert_type, COUNT(*) 
                FROM alerts 
                WHERE DATE(timestamp) >= DATE('now', '-7 days')
                GROUP BY alert_type
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            type_counts = dict(cursor.fetchall())
            
            # Por cámara
            cursor.execute('''
                SELECT cam_id, COUNT(*) 
                FROM alerts 
                WHERE DATE(timestamp) >= DATE('now', '-7 days')
                GROUP BY cam_id
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            cam_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'today_alerts': today_alerts,
                'by_severity': severity_counts,
                'by_type': type_counts,
                'by_camera': cam_counts,
                'notification_rules': len(self.notification_rules)
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def cleanup(self):
        """Limpiar recursos del gestor de alertas"""
        with self.alert_lock:
            self.active_alerts.clear()
        
        self.notification_callbacks.clear()
        
        logger.info("🚨 AlertManager limpiado")


if __name__ == "__main__":
    # Test del gestor de alertas
    alert_manager = AlertManager()
    
    # Crear alerta de prueba
    alert_id = alert_manager.create_alert(
        cam_id="test_cam_01",
        alert_type="manifestation",
        severity="high",
        title="Manifestación detectada",
        description="Se detectó una multitud de más de 50 personas",
        confidence=0.85
    )
    
    print(f"Alerta creada: {alert_id}")
    print(f"Estadísticas: {alert_manager.get_alert_statistics()}")
