import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapi import build
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from utils.teams_processor import TeamsProcessor

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class EmailIntegration:
    def __init__(self):
        self.teams_processor = TeamsProcessor()
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        token_path = 'data/token.json'
        credentials_path = 'data/credentials.json'
        
        # Check if we have saved credentials
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print("⚠️  Gmail credentials not found!")
                    print("Please download credentials.json from Google Cloud Console")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            os.makedirs('data', exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def fetch_otter_emails(self, days_back=7):
        """
        Fetch emails from Otter.ai containing meeting summaries
        
        Args:
            days_back: How many days back to search
        """
        if not self.service:
            return "Gmail service not authenticated"
        
        try:
            # Calculate date for query
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Search for Otter.ai emails
            query = f'from:no-reply@otter.ai after:{after_date}'
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No Otter.ai emails found in the last {days_back} days"
            
            return messages
            
        except Exception as e:
            return f"Error fetching emails: {str(e)}"
    
    def parse_otter_email(self, message_id):
        """Parse an Otter.ai email and extract the meeting summary"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Get email body
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                data = parts[0]['body']['data']
            else:
                data = message['payload']['body']['data']
            
            body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Extract subject (meeting title)
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Unknown')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse date
            try:
                meeting_date = datetime.strptime(date_str.split(',')[1].strip()[:11], '%d %b %Y')
                meeting_date = meeting_date.strftime('%Y-%m-%d')
            except:
                meeting_date = datetime.now().strftime('%Y-%m-%d')
            
            # Clean up the body (remove HTML if present)
            # This is a simple cleanup - you might need more sophisticated parsing
            body = re.sub('<[^<]+?>', '', body)  # Remove HTML tags
            body = re.sub(r'\n\s*\n', '\n\n', body)  # Remove extra blank lines
            
            summary = f"""
Meeting: {subject}
Date: {meeting_date}

{body[:3000]}  # Limit to first 3000 characters
"""
            
            return {
                'summary': summary,
                'date': meeting_date,
                'subject': subject
            }
            
        except Exception as e:
            return {'error': f"Error parsing email: {str(e)}"}
    
    def sync_otter_emails(self, days_back=7):
        """
        Sync Otter.ai emails to the meeting summary system
        
        Args:
            days_back: Number of days to look back
        """
        print(f"\n📧 Syncing Otter.ai emails from the last {days_back} day(s)...")
        
        messages = self.fetch_otter_emails(days_back)
        
        if isinstance(messages, str):
            return messages
        
        synced_count = 0
        for message in messages:
            parsed = self.parse_otter_email(message['id'])
            
            if 'error' not in parsed:
                result = self.teams_processor.store_meeting_summary(
                    parsed['summary'],
                    parsed['date']
                )
                
                if "successfully" in result:
                    synced_count += 1
                    print(f"  ✅ Synced: {parsed['subject']}")
        
        return f"✅ Successfully synced {synced_count} meeting(s) from email"