import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from utils.teams_processor import TeamsProcessor

load_dotenv()

class OtterAIIntegration:
    def __init__(self):
        self.api_key = os.getenv("OTTER_API_KEY")
        self.base_url = "https://otter.ai/forward/api/v1"
        self.teams_processor = TeamsProcessor()
        
    def get_recent_transcripts(self, days_back=1):
        """
        Fetch recent transcripts from Otter.ai
        
        Args:
            days_back: Number of days to look back for transcripts
        """
        if not self.api_key:
            return {"error": "OTTER_API_KEY not configured in .env file"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            # Get list of speeches (transcripts)
            response = requests.get(
                f"{self.base_url}/speeches",
                headers=headers,
                params={
                    "created_after": start_date.isoformat(),
                    "created_before": end_date.isoformat()
                }
            )
            
            if response.status_code == 200:
                speeches = response.json().get("speeches", [])
                return speeches
            else:
                return {"error": f"API Error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to fetch transcripts: {str(e)}"}
    
    def get_transcript_details(self, speech_id):
        """Get detailed transcript including summary"""
        if not self.api_key:
            return {"error": "OTTER_API_KEY not configured"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/speeches/{speech_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to fetch transcript: {str(e)}"}
    
    def sync_recent_meetings(self, days_back=1):
        """
        Automatically sync recent Otter.ai meetings to the system
        
        Args:
            days_back: Number of days to look back
        """
        print(f"\n🔄 Syncing Otter.ai meetings from the last {days_back} day(s)...")
        
        speeches = self.get_recent_transcripts(days_back)
        
        if isinstance(speeches, dict) and "error" in speeches:
            return speeches["error"]
        
        if not speeches:
            return "No new meetings found."
        
        synced_count = 0
        for speech in speeches:
            speech_id = speech.get("id")
            title = speech.get("title", "Untitled Meeting")
            created_at = speech.get("created_at")
            
            # Get full transcript details
            details = self.get_transcript_details(speech_id)
            
            if isinstance(details, dict) and "error" not in details:
                # Extract summary and transcript
                summary = details.get("summary", "")
                transcript = details.get("transcript", "")
                
                # Combine into a meeting summary
                meeting_summary = f"""
Title: {title}
Date: {created_at}

Summary:
{summary}

Key Points:
{transcript[:2000]}  # Limit to first 2000 chars
"""
                
                # Store in the system
                meeting_date = created_at.split("T")[0] if created_at else None
                result = self.teams_processor.store_meeting_summary(
                    meeting_summary, 
                    meeting_date
                )
                
                if "successfully" in result:
                    synced_count += 1
                    print(f"  ✅ Synced: {title}")
        
        return f"✅ Successfully synced {synced_count} meeting(s) from Otter.ai"
    
    def auto_sync_scheduler(self, interval_hours=24):
        """
        Set up automatic syncing at regular intervals
        
        Args:
            interval_hours: How often to sync (in hours)
        """
        import schedule
        import time
        
        def job():
            print("\n⏰ Running scheduled Otter.ai sync...")
            result = self.sync_recent_meetings(days_back=1)
            print(result)
        
        schedule.every(interval_hours).hours.do(job)
        
        print(f"⏰ Automatic sync scheduled every {interval_hours} hour(s)")
        print("Press Ctrl+C to stop the scheduler\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute