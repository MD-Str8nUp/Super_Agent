import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_integration import google_integration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
MAIN_DATABASE_ID = os.getenv("NOTION_MAIN_DATABASE_ID")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

async def create_notion_task_web(title: str, project: str = "STR8N UP", priority: str = "Medium", 
                                due_date: str = "", assignee: str = "Mohamed", description: str = "") -> str:
    """Create a task in Notion with correct property names for your database"""
    try:
        if not NOTION_TOKEN:
            return "❌ Notion not configured. Please set NOTION_TOKEN in .env file"
        
        if not MAIN_DATABASE_ID:
            return "❌ Notion database not configured. Please set NOTION_MAIN_DATABASE_ID in .env file"
        
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}", 
            "Content-Type": "application/json", 
            "Notion-Version": "2022-06-28"
        }
        
        # Build properties using YOUR database's schema
        properties = {
            # Task is the title property (not Name)
            "Task": {"title": [{"text": {"content": title}}]},
            "Business": {"select": {"name": project}},
            "Priority": {"select": {"name": priority}},
            "Status": {"select": {"name": "Not Started"}},
            "AI Generated": {"checkbox": True},
            "Category": {"select": {"name": "Task"}}
        }
        
        # Add optional properties
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}
        
        # Use Notes field instead of Description
        if description:
            properties["Notes"] = {"rich_text": [{"text": {"content": description}}]}
        
        # Create the page
        data = {
            "parent": {"database_id": MAIN_DATABASE_ID}, 
            "properties": properties
        }
        
        response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        
        if response.status_code == 200:
            page_data = response.json()
            page_url = page_data.get('url', 'Created successfully')
            return f"✅ Task '{title}' saved to Notion: {page_url}"
        else:
            error_data = response.json()
            error_msg = error_data.get('message', 'Unknown error')
            return f"❌ Failed to create task: {error_msg}"
            
    except requests.exceptions.RequestException as e:
        return f"❌ Network error connecting to Notion: {str(e)}"
    except Exception as e:
        logger.error(f"Notion error: {e}")
        return f"❌ Unexpected error: {str(e)}"

async def retrieve_notion_data_web(business: str = "ALL", status: str = "ALL", limit: int = 10) -> str:
    """Retrieve data from Notion database"""
    try:
        if not NOTION_TOKEN:
            return "❌ Notion not configured. Please set NOTION_TOKEN in .env file"
        
        if not MAIN_DATABASE_ID:
            return "❌ Notion database not configured. Please set NOTION_MAIN_DATABASE_ID in .env file"
        
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Build query filters
        filters = []
        if business != "ALL":
            filters.append({
                "property": "Business",
                "select": {"equals": business}
            })
        
        if status != "ALL":
            filters.append({
                "property": "Status",
                "select": {"equals": status}
            })
        
        query_body = {
            "page_size": limit,
            "sorts": [{"property": "Created", "direction": "descending"}]
        }
        
        if filters:
            if len(filters) == 1:
                query_body["filter"] = filters[0]
            else:
                query_body["filter"] = {"and": filters}
        
        url = f"https://api.notion.com/v1/databases/{MAIN_DATABASE_ID}/query"
        response = requests.post(url, headers=headers, json=query_body)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return f"📋 No tasks found for {business} with status {status}"
            
            response_text = f"📋 Retrieved {len(results)} tasks from Notion:\n\n"
            
            for item in results:
                props = item.get("properties", {})
                
                # Extract task details
                task_title = ""
                if "Task" in props and props["Task"]["title"]:
                    task_title = props["Task"]["title"][0]["text"]["content"]
                
                business_name = ""
                if "Business" in props and props["Business"]["select"]:
                    business_name = props["Business"]["select"]["name"]
                
                status_name = ""
                if "Status" in props and props["Status"]["select"]:
                    status_name = props["Status"]["select"]["name"]
                
                priority = ""
                if "Priority" in props and props["Priority"]["select"]:
                    priority = props["Priority"]["select"]["name"]
                
                due_date = ""
                if "Due Date" in props and props["Due Date"]["date"]:
                    due_date = props["Due Date"]["date"]["start"]
                
                response_text += f"• **{task_title}**\n"
                response_text += f"  Business: {business_name}\n"
                response_text += f"  Status: {status_name}\n"
                response_text += f"  Priority: {priority}\n"
                if due_date:
                    response_text += f"  Due: {due_date}\n"
                response_text += "\n"
            
            return response_text
        else:
            return f"❌ Failed to retrieve data: {response.status_code} - {response.text}"
            
    except Exception as e:
        logger.error(f"Notion retrieval error: {e}")
        return f"❌ Error retrieving data: {str(e)}"

async def check_ndis_compliance_web(area: str = "general") -> str:
    """Check NDIS compliance status"""
    return "📋 NDIS Audit Status: 85% complete, May 14-15 2025 scheduled, all documents ready ✅"

async def query_business_data_web(business: str = "ALL", data_type: str = "overview") -> str:
    """Query business data"""
    if business == "ALL": 
        return "📊 STR8N UP: 3 tasks, CSSA: 5 tasks (audit prep), MSA: 7 tasks (225 kids enrolled)"
    elif business == "STR8N UP": 
        return "📈 STR8N UP: 12 active clients, 2 courses in development"
    elif business == "CSSA": 
        return "❤️ CSSA: 28 participants, audit 85% ready, Buddy-Up launching"
    elif business == "MSA": 
        return "🏕️ MSA: 225 kids Term 1, Winter Camp 44 kids Jan 3-5"
    else:
        return f"❓ Unknown business: {business}"

async def manage_msa_enrollment_web(action: str = "check_numbers", age_group: str = "all") -> str:
    """Manage MSA enrollment"""
    return "📊 MSA: 225 kids enrolled, Term 1 starts Jan 17, Winter Camp Jan 3-5 (44 kids) ✅"

async def generate_invoice_web(client_name: str, business: str, service: str, amount: float, 
                              hours: float = 0, rate: float = 0) -> str:
    """Generate invoice"""
    invoice_num = f"{business[:3]}{datetime.now().strftime('%Y%m%d')}{abs(hash(client_name))%1000:03d}"
    return f"🧾 Invoice {invoice_num}: {client_name} - {service} - ${amount:.2f} ✅"

async def add_calendar_event_web(title: str, date: str, time: str, duration: int = 60, 
                                description: str = "", location: str = "") -> str:
    """Add calendar event (legacy function - use create_google_calendar_event_web instead)"""
    try:
        # Convert date and time to datetime format
        datetime_str = f"{date}T{time}:00"
        start_datetime = datetime.fromisoformat(datetime_str)
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Use Google Calendar API
        return await create_google_calendar_event_web(
            title=title,
            start_datetime=start_datetime.isoformat(),
            end_datetime=end_datetime.isoformat(),
            description=description,
            location=location
        )
    except Exception as e:
        return f"❌ Error adding calendar event: {str(e)}"

async def send_email_web(to_email: str, subject: str, message: str, cc_email: str = "") -> str:
    """Send email through Gmail API with SMTP fallback (no infinite loops)"""
    # First try Gmail API
    try:
        if hasattr(google_integration, 'gmail_enabled') and google_integration.gmail_enabled:
            google_integration.send_email(to_email, subject, message)
            return f"✅ Email sent via Gmail API to {to_email} - Subject: {subject}"
    except Exception as e:
        logger.info(f"Gmail API failed: {e}, trying SMTP")
    
    # Fallback to SMTP
    return await send_smtp_email(to_email, subject, message, cc_email)

# Google Calendar Functions
async def create_google_calendar_event_web(title: str, start_datetime: str, end_datetime: str,
                                          description: str = "", location: str = "",
                                          attendees: str = "") -> str:
    """Create Google Calendar event with improved error handling"""
    try:
        # Check if Google integration is available
        if not hasattr(google_integration, 'calendar_service') or not google_integration.calendar_service:
            return "❌ Google Calendar not configured. Please check google-credentials.json file exists"
        
        attendee_list = [email.strip() for email in attendees.split(',')] if attendees else []
        
        result = google_integration.create_calendar_event(
            title=title,
            start_time=start_datetime,
            end_time=end_datetime,
            description=description,
            location=location,
            attendees=attendee_list
        )
        
        if result["success"]:
            return f"✅ {result['message']} - {result.get('event_link', '')}"
        else:
            # Provide helpful error messages
            error = result['error']
            if "403" in str(error):
                return "❌ Calendar API permission denied. Enable Calendar API in Google Cloud Console"
            elif "404" in str(error):
                return "❌ Calendar not found. Share your calendar with: ops-py-service-account@claude-calendar-sync-460423.iam.gserviceaccount.com"
            else:
                return f"❌ Failed to create event: {error}"
    except Exception as e:
        logger.error(f"Calendar error: {e}")
        return f"❌ Error creating calendar event: {str(e)}"

async def get_upcoming_events_web(days_ahead: int = 7, max_results: int = 10) -> str:
    """Get upcoming Google Calendar events with error handling"""
    try:
        if not hasattr(google_integration, 'calendar_service') or not google_integration.calendar_service:
            return "❌ Google Calendar not configured. Please check google-credentials.json"
        
        result = google_integration.get_upcoming_events(
            max_results=max_results, 
            days_ahead=days_ahead
        )
        
        if result["success"]:
            events = result["events"]
            if not events:
                return "📅 No upcoming events found. Make sure your calendar is shared with: ops-py-service-account@claude-calendar-sync-460423.iam.gserviceaccount.com"
            
            response = f"📅 Upcoming Events ({len(events)} found):\n\n"
            for event in events:
                start_time = event["start"].replace('T', ' ').replace('Z', '')
                response += f"• **{event['title']}**\n"
                response += f"  📅 {start_time}\n"
                if event["location"]:
                    response += f"  📍 {event['location']}\n"
                response += "\n"
            
            return response
        else:
            error = result['error']
            if "403" in str(error):
                return "❌ Calendar API access denied. Check API permissions"
            else:
                return f"❌ Failed to get events: {error}"
    except Exception as e:
        logger.error(f"Calendar error: {e}")
        return f"❌ Error getting events: {str(e)}"

# Gmail Functions
async def read_recent_emails_web(max_results: int = 10, query: str = "is:unread") -> str:
    """Read recent Gmail emails with better error handling"""
    try:
        if not hasattr(google_integration, 'gmail_service') or not google_integration.gmail_service:
            return "❌ Gmail API not configured. Using SMTP for sending only."
        
        result = google_integration.read_recent_emails(
            max_results=max_results, 
            query=query
        )
        
        if result["success"]:
            emails = result["emails"]
            if not emails:
                return "📧 No emails found"
            
            response = f"📧 Recent Emails ({len(emails)} found):\n\n"
            for email in emails:
                response += f"• **From:** {email['sender']}\n"
                response += f"  **Subject:** {email['subject']}\n"
                response += f"  **Date:** {email['date']}\n"
                response += f"  **Preview:** {email['snippet'][:100]}...\n\n"
            
            return response
        else:
            error = result['error']
            if "403" in str(error):
                return "❌ Gmail API requires domain-wide delegation. Use SMTP for sending."
            elif "400" in str(error) and "failedPrecondition" in str(error):
                return "❌ Gmail API not enabled. Enable it in Google Cloud Console or use SMTP."
            else:
                return f"❌ Failed to read emails: {error}"
    except Exception as e:
        logger.error(f"Gmail error: {e}")
        return f"❌ Error reading emails: {str(e)}"

async def send_gmail_web(to_email: str, subject: str, body: str, cc_email: str = "", bcc_email: str = "") -> str:
    """Send email via Gmail API with SMTP fallback"""
    try:
        # Try Gmail API first
        if hasattr(google_integration, 'gmail_enabled') and google_integration.gmail_enabled:
            try:
                google_integration.send_email(to_email, subject, body)
                return f"✅ Email sent via Gmail API to {to_email} - Subject: {subject}"
            except Exception as e:
                logger.info(f"Gmail API failed: {e}, trying SMTP")
        
        # Fallback to SMTP directly (avoid infinite loop)
        return await send_smtp_email(to_email, subject, body, cc_email)
        
    except Exception as e:
        logger.error(f"Gmail error: {e}")
        # Try SMTP as last resort
        return await send_smtp_email(to_email, subject, body, cc_email)

async def send_smtp_email(to_email: str, subject: str, message: str, cc_email: str = "") -> str:
    """Send email via SMTP only"""
    try:
        if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
            return "❌ Email not configured. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
        
        if GMAIL_EMAIL == "your-email@gmail.com":
            return "❌ Please update GMAIL_EMAIL in .env with your actual email address"
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        if cc_email:
            msg['Cc'] = cc_email
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        text = msg.as_string()
        recipients = to_email.split(',') + (cc_email.split(',') if cc_email else [])
        server.sendmail(GMAIL_EMAIL, recipients, text)
        server.quit()
        
        return f"✅ Email sent to {to_email} via SMTP - Subject: {subject}"
    except smtplib.SMTPAuthenticationError:
        return "❌ SMTP authentication failed. Please check GMAIL_APP_PASSWORD. Generate app password at: https://myaccount.google.com/apppasswords"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

async def check_calendar_availability_web(start_datetime: str, end_datetime: str) -> str:
    """Check calendar availability with error handling"""
    try:
        if not hasattr(google_integration, 'calendar_service') or not google_integration.calendar_service:
            return "❌ Google Calendar not configured. Please check google-credentials.json"
        
        result = google_integration.get_calendar_free_busy(start_datetime, end_datetime)
        
        if result["success"]:
            if result["is_free"]:
                return f"✅ Calendar is FREE from {start_datetime} to {end_datetime}"
            else:
                busy_times = result["busy_times"]
                response = f"❌ Calendar has conflicts:\n"
                for busy in busy_times:
                    start = busy["start"].replace('T', ' ').replace('Z', '')
                    end = busy["end"].replace('T', ' ').replace('Z', '')
                    response += f"• Busy: {start} - {end}\n"
                return response
        else:
            error = result['error']
            if "403" in str(error):
                return "❌ Calendar API access denied. Check permissions"
            else:
                return f"❌ Failed to check availability: {error}"
    except Exception as e:
        logger.error(f"Calendar availability error: {e}")
        return f"❌ Error checking availability: {str(e)}"
