#!/usr/bin/env python3
"""
Historical Data ETL Automation Script
====================================

Automated script for daily ETL updates of historical datasets.
Includes error handling, logging, and notification systems.
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import traceback
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from historical_datasets_etl import HistoricalDataETL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_historical_etl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class HistoricalETLAutomation:
    """Automation manager for historical data ETL processes"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.etl = HistoricalDataETL()
        self.last_run_file = Path("./data/last_etl_run.json")
        
        # Ensure data directories exist
        Path("./data/raw").mkdir(parents=True, exist_ok=True)
        Path("./data/processed").mkdir(parents=True, exist_ok=True)
        Path("./logs").mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "schedule": {
                "daily_time": "02:00",  # 2 AM daily
                "timezone": "UTC"
            },
            "notification": {
                "enabled": False,
                "email": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": []
                }
            },
            "data_sources": {
                "force_refresh_days": 7,  # Force refresh if data older than 7 days
                "batch_size": 1000,
                "timeout_minutes": 30
            },
            "alerts": {
                "error_threshold": 3,  # Send alert after 3 consecutive failures
                "success_notification": True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def run_etl_job(self, force_refresh: bool = False) -> Dict:
        """Execute the ETL job with comprehensive error handling"""
        start_time = datetime.now()
        job_id = start_time.strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"🚀 Starting ETL job {job_id}")
        
        try:
            # Check if force refresh is needed based on last run
            if not force_refresh:
                force_refresh = self._should_force_refresh()
            
            # Run the ETL process
            results = self.etl.run_full_etl(force_refresh=force_refresh)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare success summary
            total_records = sum(results.values())
            success_summary = {
                "job_id": job_id,
                "status": "success",
                "start_time": start_time.isoformat(),
                "execution_time_seconds": execution_time,
                "total_records": total_records,
                "dataset_counts": results,
                "force_refresh": force_refresh
            }
            
            # Save run info
            self._save_run_info(success_summary)
            
            # Log success
            logger.info(f"✅ ETL job {job_id} completed successfully")
            logger.info(f"📊 Total records processed: {total_records:,}")
            logger.info(f"⏱️ Execution time: {execution_time:.1f} seconds")
            
            # Send success notification if enabled
            if self.config["alerts"]["success_notification"]:
                self._send_notification("ETL Success", success_summary)
            
            return success_summary
            
        except Exception as e:
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare error summary
            error_summary = {
                "job_id": job_id,
                "status": "error",
                "start_time": start_time.isoformat(),
                "execution_time_seconds": execution_time,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "force_refresh": force_refresh
            }
            
            # Save run info
            self._save_run_info(error_summary)
            
            # Log error
            logger.error(f"❌ ETL job {job_id} failed: {e}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            
            # Check if we should send error alert
            consecutive_failures = self._get_consecutive_failures()
            if consecutive_failures >= self.config["alerts"]["error_threshold"]:
                self._send_notification("ETL Failure Alert", error_summary)
            
            return error_summary
    
    def _should_force_refresh(self) -> bool:
        """Determine if force refresh is needed based on last successful run"""
        if not self.last_run_file.exists():
            return True
        
        try:
            with open(self.last_run_file, 'r') as f:
                last_run = json.load(f)
            
            if last_run.get("status") != "success":
                return True
            
            last_run_time = datetime.fromisoformat(last_run["start_time"])
            days_since_last_run = (datetime.now() - last_run_time).days
            
            return days_since_last_run >= self.config["data_sources"]["force_refresh_days"]
            
        except Exception as e:
            logger.warning(f"Could not determine last run status: {e}")
            return True
    
    def _save_run_info(self, run_info: Dict) -> None:
        """Save run information to file"""
        try:
            with open(self.last_run_file, 'w') as f:
                json.dump(run_info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save run info: {e}")
    
    def _get_consecutive_failures(self) -> int:
        """Get number of consecutive failures"""
        try:
            if not self.last_run_file.exists():
                return 0
            
            with open(self.last_run_file, 'r') as f:
                last_run = json.load(f)
            
            # For simplicity, return 1 if last run failed, 0 if succeeded
            # In a full implementation, you'd track multiple runs
            return 1 if last_run.get("status") == "error" else 0
            
        except Exception:
            return 0
    
    def _send_notification(self, subject: str, summary: Dict) -> None:
        """Send email notification if configured"""
        if not self.config["notification"]["enabled"]:
            return
        
        try:
            email_config = self.config["notification"]["email"]
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config["from_email"]
            msg['To'] = ", ".join(email_config["to_emails"])
            msg['Subject'] = f"Historical ETL: {subject}"
            
            # Create body
            body = self._format_notification_body(summary)
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.sendmail(email_config["from_email"], email_config["to_emails"], msg.as_string())
            server.quit()
            
            logger.info(f"📧 Notification sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _format_notification_body(self, summary: Dict) -> str:
        """Format notification email body"""
        if summary["status"] == "success":
            return f"""
Historical Data ETL - Success Report

Job ID: {summary["job_id"]}
Start Time: {summary["start_time"]}
Execution Time: {summary["execution_time_seconds"]:.1f} seconds
Total Records: {summary["total_records"]:,}
Force Refresh: {summary["force_refresh"]}

Dataset Breakdown:
{chr(10).join(f"- {dataset}: {count:,} records" for dataset, count in summary["dataset_counts"].items())}

ETL completed successfully.
            """
        else:
            return f"""
Historical Data ETL - Error Report

Job ID: {summary["job_id"]}
Start Time: {summary["start_time"]}
Execution Time: {summary["execution_time_seconds"]:.1f} seconds
Force Refresh: {summary["force_refresh"]}

Error: {summary["error"]}

Please check the logs for more details.
            """
    
    def get_status(self) -> Dict:
        """Get current automation status"""
        status = {
            "automation_active": True,
            "config": self.config,
            "last_run": None,
            "next_scheduled_run": None
        }
        
        # Get last run info
        if self.last_run_file.exists():
            try:
                with open(self.last_run_file, 'r') as f:
                    status["last_run"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load last run info: {e}")
        
        # Calculate next scheduled run (simplified)
        try:
            daily_time = self.config["schedule"]["daily_time"]
            now = datetime.now()
            next_run = now.replace(
                hour=int(daily_time.split(':')[0]),
                minute=int(daily_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            if next_run <= now:
                next_run += timedelta(days=1)
            
            status["next_scheduled_run"] = next_run.isoformat()
            
        except Exception as e:
            logger.warning(f"Could not calculate next run time: {e}")
        
        return status
    
    def setup_scheduler(self) -> None:
        """Setup the scheduled ETL job"""
        daily_time = self.config["schedule"]["daily_time"]
        
        schedule.every().day.at(daily_time).do(self.run_etl_job)
        
        logger.info(f"📅 ETL scheduled to run daily at {daily_time}")
        
        # Run scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point for the automation script"""
    parser = argparse.ArgumentParser(description="Historical Data ETL Automation")
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--run-now', action='store_true', help='Run ETL immediately')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all data')
    parser.add_argument('--schedule', action='store_true', help='Run in scheduled mode')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = HistoricalETLAutomation(config_path=args.config)
    
    if args.status:
        # Show status
        status = automation.get_status()
        print(json.dumps(status, indent=2))
        
    elif args.run_now:
        # Run ETL immediately
        result = automation.run_etl_job(force_refresh=args.force_refresh)
        print(json.dumps(result, indent=2))
        
    elif args.schedule:
        # Run in scheduled mode
        logger.info("🎯 Starting ETL automation in scheduled mode")
        automation.setup_scheduler()
        
    else:
        # Show help
        parser.print_help()


if __name__ == "__main__":
    main()
