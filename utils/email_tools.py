from langchain_core.tools import tool
from utils.email_integration import EmailIntegration

email_integration = EmailIntegration()

@tool
def sync_email_meetings(days_back: int = 7) -> str:
    """
    Sync meeting summaries from Otter.ai emails in Gmail.
    
    Args:
        days_back: Number of days to look back for emails (default: 7)
    """
    try:
        result = email_integration.sync_otter_emails(days_back)
        return result
    except Exception as e:
        return f"Error syncing emails: {str(e)}"

@tool
def list_email_meetings(days_back: int = 7) -> str:
    """
    List Otter.ai meeting emails without syncing them.
    
    Args:
        days_back: Number of days to look back (default: 7)
    """
    try:
        messages = email_integration.fetch_otter_emails(days_back)
        
        if isinstance(messages, str):
            return messages
        
        result = f"Otter.ai Emails (Last {days_back} days):\n\n"
        for msg in messages:
            parsed = email_integration.parse_otter_email(msg['id'])
            if 'error' not in parsed:
                result += f"📧 {parsed['subject']}\n"
                result += f"   Date: {parsed['date']}\n\n"
        
        return result
    except Exception as e:
        return f"Error listing emails: {str(e)}"