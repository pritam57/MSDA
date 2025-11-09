from langchain_core.tools import tool
from utils.teams_processor import TeamsProcessor
import os
from datetime import datetime, timedelta

teams_processor = TeamsProcessor()

@tool
def receive_meeting_summary(summary_text: str, meeting_date: str = None) -> str:
    """
    Receive and store a daily meeting summary from Otter.ai or other sources.
    
    Args:
        summary_text: The meeting summary text
        meeting_date: Date of the meeting (YYYY-MM-DD format). If not provided, uses today's date.
    """
    try:
        result = teams_processor.store_meeting_summary(summary_text, meeting_date)
        return result
    except Exception as e:
        return f"Error storing meeting summary: {str(e)}"

@tool
def list_meeting_summaries(start_date: str = None, end_date: str = None) -> str:
    """
    List all stored meeting summaries within a date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: End date (YYYY-MM-DD). Defaults to today.
    """
    try:
        summaries = teams_processor.list_summaries(start_date, end_date)
        return summaries
    except Exception as e:
        return f"Error listing summaries: {str(e)}"

@tool
def generate_monthly_report(month: str = None, year: str = None) -> str:
    """
    Generate a comprehensive monthly report from all meeting summaries.
    Analyzes decisions made, tasks completed, and customer pulse.
    
    Args:
        month: Month number (1-12). Defaults to current month.
        year: Year (YYYY). Defaults to current year.
    """
    try:
        report = teams_processor.generate_monthly_report(month, year)
        return report
    except Exception as e:
        return f"Error generating monthly report: {str(e)}"

@tool
def search_meeting_summaries(query: str) -> str:
    """
    Search through meeting summaries for specific topics, decisions, or action items.
    
    Args:
        query: Search query (e.g., "customer feedback", "project timeline", "budget")
    """
    try:
        results = teams_processor.search_summaries(query)
        return results
    except Exception as e:
        return f"Error searching summaries: {str(e)}"

@tool
def send_report_to_teams(report_text: str, channel_name: str = "General") -> str:
    """
    Send a generated report to a Microsoft Teams channel.
    
    Args:
        report_text: The report content to send
        channel_name: Name of the Teams channel (default: "General")
    """
    try:
        result = teams_processor.send_to_teams(report_text, channel_name)
        return result
    except Exception as e:
        return f"Error sending to Teams: {str(e)}"