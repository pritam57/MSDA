import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings  # Updated
from langchain_chroma import Chroma  # Updated
from langchain.schema import Document
from dotenv import load_dotenv
import pymsteams

load_dotenv()

class TeamsProcessor:
    def __init__(self):
        self.summaries_dir = Path("data/meeting_summaries")
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = "data/summaries_db"
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
        
        # Teams webhook URL (you'll need to create this in Teams)
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL", "")
        
        self._load_vectorstore()
    
    def _load_vectorstore(self):
        """Load or create vector store for meeting summaries"""
        if os.path.exists(self.db_path):
            self.vectorstore = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )
        else:
            self.vectorstore = None
    
    def store_meeting_summary(self, summary_text: str, meeting_date: str = None):
        """Store a meeting summary with metadata"""
        if not meeting_date:
            meeting_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            datetime.strptime(meeting_date, "%Y-%m-%d")
        except ValueError:
            return "Error: Invalid date format. Use YYYY-MM-DD"
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_{meeting_date}_{timestamp}.json"
        filepath = self.summaries_dir / filename
        
        # Store summary with metadata
        summary_data = {
            "date": meeting_date,
            "timestamp": timestamp,
            "content": summary_text,
            "created_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        # Add to vector store
        doc = Document(
            page_content=summary_text,
            metadata={
                "source": filename,
                "date": meeting_date,
                "type": "meeting_summary"
            }
        )
        
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=[doc],
                embedding=self.embeddings,
                persist_directory=self.db_path
            )
        else:
            self.vectorstore.add_documents([doc])
        
        return f"✅ Meeting summary stored successfully for {meeting_date}"
    
    def list_summaries(self, start_date: str = None, end_date: str = None):
        """List all meeting summaries within date range"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        summaries = []
        for filepath in sorted(self.summaries_dir.glob("meeting_*.json")):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if start_date <= data['date'] <= end_date:
                    summaries.append({
                        "date": data['date'],
                        "preview": data['content'][:200] + "..."
                    })
        
        if not summaries:
            return f"No meeting summaries found between {start_date} and {end_date}"
        
        result = f"Meeting Summaries ({start_date} to {end_date}):\n\n"
        for summary in summaries:
            result += f"📅 {summary['date']}\n{summary['preview']}\n\n"
        
        return result
    
    def search_summaries(self, query: str, k: int = 5):
        """Search through meeting summaries"""
        if not self.vectorstore:
            return "No meeting summaries stored yet."
        
        results = self.vectorstore.similarity_search(query, k=k)
        
        if not results:
            return f"No results found for: {query}"
        
        response = f"Search results for '{query}':\n\n"
        for doc in results:
            response += f"📅 Date: {doc.metadata.get('date', 'Unknown')}\n"
            response += f"Content: {doc.page_content[:300]}...\n\n"
        
        return response
    
    def generate_monthly_report(self, month: str = None, year: str = None):
        """Generate comprehensive monthly report"""
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        month = int(month)
        year = int(year)
        
        # Get date range for the month
        start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
        if month == 12:
            end_date = datetime(year, 12, 31).strftime("%Y-%m-%d")
        else:
            end_date = (datetime(year, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Collect all summaries for the month
        summaries = []
        for filepath in sorted(self.summaries_dir.glob("meeting_*.json")):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if start_date <= data['date'] <= end_date:
                    summaries.append(data)
        
        if not summaries:
            return f"No meeting summaries found for {month}/{year}"
        
        # Combine all summaries
        combined_text = "\n\n---\n\n".join([
            f"Date: {s['date']}\n{s['content']}" for s in summaries
        ])
        
        # Generate report using Claude
        prompt = f"""You are analyzing meeting summaries for {month}/{year}.

Below are all the meeting summaries for this month:

{combined_text}

Please generate a comprehensive monthly report with the following sections:

## 📊 Monthly Summary Report - {month}/{year}

### 1. Key Decisions Made
List all major decisions that were made during the month.

### 2. Completed Tasks & Milestones
Summarize all tasks and milestones that were completed.

### 3. Ongoing Projects & Status
Provide status updates on ongoing projects.

### 4. Action Items & Next Steps
List pending action items and next steps.

### 5. Customer Pulse
Analyze customer feedback, concerns, and satisfaction indicators mentioned in meetings.

### 6. Team Performance & Challenges
Highlight team achievements and any challenges faced.

### 7. Key Metrics
Extract any numbers, metrics, or KPIs mentioned.

### 8. Strategic Insights
Provide strategic insights and recommendations based on the month's discussions.

Be specific, cite dates where relevant, and provide a clear, actionable summary."""

        response = self.llm.invoke(prompt)
        report_content = response.content
        
        # Save report
        report_filename = f"monthly_report_{year}_{month:02d}.txt"
        report_path = self.summaries_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_content
    
    def send_to_teams(self, message: str, channel_name: str = "General"):
        """Send message to Microsoft Teams channel"""
        if not self.teams_webhook:
            return "⚠️ Teams webhook URL not configured. Set TEAMS_WEBHOOK_URL in .env file"
        
        try:
            teams_message = pymsteams.connectorcard(self.teams_webhook)
            teams_message.text(message)
            teams_message.send()
            return f"✅ Message sent to Teams channel: {channel_name}"
        except Exception as e:
            return f"Error sending to Teams: {str(e)}"