"""
Enhanced API for Professional Conflict Monitoring System
Provides REST endpoints for all AI-powered analysis capabilities
including real-time monitoring, predictions, and executive reporting.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json
import base64
from pathlib import Path

# Import enhanced orchestrator
from src.orchestration.enhanced_orchestrator import EnhancedGeopoliticalOrchestrator

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Geopolitical Intelligence API",
    description="Professional conflict monitoring and analysis system with AI-powered capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the enhanced orchestrator on startup"""
    global orchestrator
    try:
        logger.info("Initializing Enhanced Geopolitical Intelligence System...")
        orchestrator = EnhancedGeopoliticalOrchestrator()
        logger.info("System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise

# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    include_data_collection: bool = Field(default=True, description="Whether to collect new data")
    include_vision_analysis: bool = Field(default=False, description="Whether to analyze visual content")
    generate_reports: bool = Field(default=True, description="Whether to generate executive reports")
    days_back: int = Field(default=7, description="Number of days to analyze")

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., description="Text to analyze")
    language: str = Field(default="en", description="Language code")
    analysis_types: List[str] = Field(default=["entities", "classification", "sentiment"], 
                                    description="Types of analysis to perform")

class ImageAnalysisRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image or image URL")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    coordinates: Optional[List[float]] = Field(default=None, description="GPS coordinates [lat, lon]")

class AlertConfigRequest(BaseModel):
    severity_threshold: str = Field(default="medium", description="Minimum severity for alerts")
    regions: List[str] = Field(default=[], description="Regions to monitor")
    notification_channels: List[str] = Field(default=["email"], description="Notification channels")
    recipients: List[str] = Field(default=[], description="Notification recipients")

class ReportRequest(BaseModel):
    report_type: str = Field(default="daily", description="Type of report")
    format_types: List[str] = Field(default=["html"], description="Output formats")
    period_days: int = Field(default=7, description="Period to cover in days")

# API Endpoints

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with system information"""
    return {
        "system": "Enhanced Geopolitical Intelligence API",
        "version": "2.0.0",
        "status": "operational",
        "capabilities": [
            "Multilingual NLP Analysis",
            "Computer Vision Analysis", 
            "Trend Prediction",
            "Anomaly Detection",
            "Real-time Monitoring",
            "Executive Reporting",
            "Alert Generation"
        ],
        "documentation": "/docs"
    }

@app.get("/system/status", tags=["System"])
async def get_system_status():
    """Get comprehensive system status"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        status = orchestrator.get_system_status()
        return JSONResponse(content=status)
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/comprehensive", tags=["Analysis"])
async def run_comprehensive_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Run comprehensive geopolitical intelligence analysis"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Run analysis in background for long-running operations
        def run_analysis():
            return orchestrator.run_comprehensive_analysis(
                include_data_collection=request.include_data_collection,
                include_vision_analysis=request.include_vision_analysis,
                generate_reports=request.generate_reports
            )
        
        # For now, run synchronously (could be made async for production)
        results = run_analysis()
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/text", tags=["Analysis"])
async def analyze_text(request: TextAnalysisRequest):
    """Analyze text for entities, conflict classification, and sentiment"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        results = {
            "text_length": len(request.text),
            "language": request.language,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Entity extraction
        if "entities" in request.analysis_types:
            entities = orchestrator.ner_processor.extract_entities(request.text, request.language)
            results["entities"] = entities
        
        # Conflict classification
        if "classification" in request.analysis_types:
            conflict_type = orchestrator.conflict_classifier.classify_conflict_type(request.text)
            intensity = orchestrator.conflict_classifier.analyze_intensity(request.text)
            humanitarian = orchestrator.conflict_classifier.analyze_humanitarian_impact(request.text)
            
            results["classification"] = {
                "conflict_type": conflict_type,
                "intensity": intensity,
                "humanitarian_impact": humanitarian
            }
        
        # Sentiment analysis
        if "sentiment" in request.analysis_types:
            sentiment = orchestrator.conflict_classifier.analyze_sentiment(request.text)
            results["sentiment"] = sentiment
        
        # Actor relationships
        if "relationships" in request.analysis_types and "entities" in results:
            relationships = orchestrator.actor_mapper.extract_relationships(request.text, results["entities"])
            results["relationships"] = relationships
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/image", tags=["Analysis"])
async def analyze_image(request: ImageAnalysisRequest):
    """Analyze image for conflict-related content"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Analyze image
        coordinates = tuple(request.coordinates) if request.coordinates else None
        
        if request.image_data.startswith('http'):
            # URL provided
            results = orchestrator.vision_analyzer.analyze_image(request.image_data, request.analysis_type)
        else:
            # Assume base64 data
            results = orchestrator.vision_analyzer.analyze_image(request.image_data, request.analysis_type)
        
        # Add satellite analysis if coordinates provided
        if coordinates and request.analysis_type == "satellite":
            satellite_results = orchestrator.vision_analyzer.analyze_satellite_imagery(
                request.image_data, coordinates
            )
            results.update(satellite_results)
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/upload-image", tags=["Analysis"])
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    analysis_type: str = Form(default="comprehensive"),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None)
):
    """Upload and analyze an image file"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Read and encode image
        image_data = await file.read()
        image_base64 = base64.b64encode(image_data).decode()
        image_data_url = f"data:image/{file.filename.split('.')[-1]};base64,{image_base64}"
        
        # Analyze image
        coordinates = (latitude, longitude) if latitude and longitude else None
        results = orchestrator.vision_analyzer.analyze_image(image_data_url, analysis_type)
        
        if coordinates:
            satellite_results = orchestrator.vision_analyzer.analyze_satellite_imagery(
                image_data_url, coordinates
            )
            results.update(satellite_results)
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error in image upload analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions/trends", tags=["Predictions"])
async def get_trend_predictions(days: int = 30, confidence_interval: float = 0.8):
    """Get conflict trend predictions"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Load recent data for prediction
        recent_data = orchestrator._load_recent_data(days=30)
        
        if len(recent_data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient data for predictions")
        
        # Prepare data and get predictions
        import pandas as pd
        df_data = []
        for article in recent_data:
            df_data.append({
                'timestamp': article.get('timestamp'),
                'risk_score': article.get('risk_score', 0),
                'conflict_intensity': article.get('conflict_intensity', 0),
                'humanitarian_impact': article.get('humanitarian_impact', 0)
            })
        
        df = pd.DataFrame(df_data)
        ts_data = orchestrator.trend_predictor.prepare_time_series_data(df)
        
        if len(ts_data) >= 30:
            # Train models
            orchestrator.trend_predictor.train_prophet_model(ts_data)
            
            # Get predictions
            predictions = orchestrator.trend_predictor.predict_future_trends(
                periods=days, 
                confidence_interval=confidence_interval
            )
            
            return JSONResponse(content=predictions)
        else:
            raise HTTPException(status_code=400, detail="Insufficient data for model training")
    
    except Exception as e:
        logger.error(f"Error getting trend predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies/detect", tags=["Anomalies"])
async def detect_anomalies(method: str = "isolation_forest", days: int = 7):
    """Detect anomalies in recent conflict data"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Load recent data
        recent_data = orchestrator._load_recent_data(days=days)
        
        if len(recent_data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient data for anomaly detection")
        
        import pandas as pd
        df = pd.DataFrame(recent_data)
        
        # Detect anomalies
        results = orchestrator.anomaly_detector.detect_anomalies(df, method)
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patterns/analyze", tags=["Patterns"])
async def analyze_patterns(pattern_type: str = "temporal", days: int = 30):
    """Analyze patterns in conflict data"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Load recent data
        recent_data = orchestrator._load_recent_data(days=days)
        
        if len(recent_data) < 5:
            raise HTTPException(status_code=400, detail="Insufficient data for pattern analysis")
        
        import pandas as pd
        df = pd.DataFrame(recent_data)
        
        # Analyze patterns
        results = orchestrator.pattern_analyzer.identify_patterns(df, pattern_type)
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/start", tags=["Monitoring"])
async def start_monitoring():
    """Start real-time conflict monitoring"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        result = orchestrator.start_real_time_monitoring()
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/stop", tags=["Monitoring"])
async def stop_monitoring():
    """Stop real-time conflict monitoring"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        result = orchestrator.stop_real_time_monitoring()
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/status", tags=["Monitoring"])
async def get_monitoring_status():
    """Get real-time monitoring status"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        status = {
            "monitoring_active": orchestrator.real_time_monitor.monitoring_active,
            "timestamp": datetime.now().isoformat()
        }
        
        if orchestrator.real_time_monitor:
            alert_stats = orchestrator.real_time_monitor.get_alert_statistics()
            status.update(alert_stats)
        
        return JSONResponse(content=status)
    
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/recent", tags=["Alerts"])
async def get_recent_alerts(hours: int = 24, severity: Optional[str] = None):
    """Get recent alerts"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        if not orchestrator.real_time_monitor:
            raise HTTPException(status_code=503, detail="Real-time monitor not available")
        
        # Get alerts from monitor
        all_alerts = orchestrator.real_time_monitor.alert_history
        
        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert.to_dict() for alert in all_alerts 
            if alert.timestamp >= cutoff_time
        ]
        
        # Filter by severity if specified
        if severity:
            recent_alerts = [
                alert for alert in recent_alerts 
                if alert.get('severity') == severity
            ]
        
        return JSONResponse(content={
            "alerts": recent_alerts,
            "total_count": len(recent_alerts),
            "period_hours": hours,
            "severity_filter": severity
        })
    
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/generate", tags=["Reports"])
async def generate_report(request: ReportRequest):
    """Generate executive report"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Load data for the specified period
        recent_data = orchestrator._load_recent_data(days=request.period_days)
        
        # Prepare report data
        report_data = {
            'period_start': datetime.now() - timedelta(days=request.period_days),
            'period_end': datetime.now(),
            'conflicts': recent_data,
            'alerts': orchestrator.real_time_monitor.alert_history[-50:] if orchestrator.real_time_monitor else []
        }
        
        # Generate report
        reports = orchestrator.report_generator.generate_executive_report(
            data=report_data,
            report_type=request.report_type,
            format_types=request.format_types
        )
        
        return JSONResponse(content={
            "reports_generated": reports,
            "report_type": request.report_type,
            "formats": request.format_types,
            "period_days": request.period_days
        })
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/download/{filename}", tags=["Reports"])
async def download_report(filename: str):
    """Download generated report file"""
    try:
        reports_dir = Path("reports")
        file_path = reports_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment/trends", tags=["Sentiment"])
async def get_sentiment_trends(groupby: str = "region", days: int = 30):
    """Get sentiment trends analysis"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Load recent data
        recent_data = orchestrator._load_recent_data(days=days)
        
        if len(recent_data) < 5:
            raise HTTPException(status_code=400, detail="Insufficient data for sentiment analysis")
        
        import pandas as pd
        df = pd.DataFrame(recent_data)
        
        # Calculate sentiment scores if not available
        if 'sentiment_score' not in df.columns:
            for i, row in df.iterrows():
                text = row.get('content', '') or row.get('title', '')
                if text:
                    sentiment = orchestrator.conflict_classifier.analyze_sentiment(text)
                    score = sentiment.get('confidence', 0)
                    if sentiment.get('sentiment') == 'negative':
                        score = -score
                    df.at[i, 'sentiment_score'] = score
        
        # Analyze sentiment trends
        results = orchestrator.sentiment_analyzer.analyze_sentiment_trends(df, groupby)
        
        return JSONResponse(content=results)
    
    except Exception as e:
        logger.error(f"Error getting sentiment trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/recent", tags=["Data"])
async def get_recent_data(days: int = 7, limit: int = 100):
    """Get recent conflict data"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        recent_data = orchestrator._load_recent_data(days=days)
        
        # Limit results
        if len(recent_data) > limit:
            recent_data = recent_data[:limit]
        
        return JSONResponse(content={
            "data": recent_data,
            "count": len(recent_data),
            "period_days": days,
            "limit_applied": limit
        })
    
    except Exception as e:
        logger.error(f"Error getting recent data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    try:
        if not orchestrator:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "System not initialized"}
            )
        
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "orchestrator": orchestrator is not None,
                "database": orchestrator._check_database_status().get('connected', False),
                "ai_models": all([
                    orchestrator.ner_processor is not None,
                    orchestrator.conflict_classifier is not None,
                    orchestrator.vision_analyzer is not None
                ])
            }
        }
        
        # Check if any component is unhealthy
        if not all(health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return JSONResponse(content=health_status)
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": "The requested endpoint does not exist"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )

# Main function to run the API
def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the enhanced API server"""
    uvicorn.run(
        "src.api.enhanced_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_api()