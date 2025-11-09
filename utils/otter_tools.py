from langchain_core.tools import tool
from utils.otter_integration import OtterAIIntegration

otter = OtterAIIntegration()

@tool
def sync_otter_meetings(days_back: int = 1) -> str:
    """
    Sync recent meeting transcripts from Otter.ai.
    
    Args:
        days_back: Number of days to look back for meetings (default: 1)
    """
    try:
        result = otter.sync_recent_meetings(days_back)
        return result
    except Exception as e:
        return f"Error syncing Otter.ai meetings: {str(e)}"

@tool
def list_otter_meetings(days_back: int = 7) -> str:
    """
    List recent meetings from Otter.ai without syncing them.
    
    Args:
        days_back: Number of days to look back (default: 7)
    """
    try:
        speeches = otter.get_recent_transcripts(days_back)
        
        if isinstance(speeches, dict) and "error" in speeches:
            return speeches["error"]
        
        if not speeches:
            return f"No meetings found in the last {days_back} day(s)"
        
        result = f"Otter.ai Meetings (Last {days_back} days):\n\n"
        for speech in speeches:
            title = speech.get("title", "Untitled")
            created = speech.get("created_at", "Unknown date")
            duration = speech.get("duration", 0)
            
            result += f"📝 {title}\n"
            result += f"   Date: {created}\n"
            result += f"   Duration: {duration//60} minutes\n\n"
        
        return result
    except Exception as e:
        return f"Error listing Otter.ai meetings: {str(e)}"