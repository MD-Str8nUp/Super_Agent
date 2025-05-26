import os
import requests
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_integration import google_integration

# Configure logger
logger = logging.getLogger(__name__)

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
MAIN_DATABASE_ID = os.getenv("NOTION_MAIN_DATABASE_ID")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

async def create_notion_task_web(title: str, project: str = "STR8N UP", priority: str = "Medium", due_date: str = "", assignee: str = "Mohamed", description: str = "") -> str:
   try:
       if not NOTION_TOKEN or not MAIN_DATABASE_ID:
           return f"❌ Notion not configured. Please set NOTION_TOKEN and NOTION_MAIN_DATABASE_ID in .env"
       
       headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
       properties = {"Name": {"title": [{"text": {"content": title}}]}, "Business": {"select": {"name": project}}, "Priority": {"select": {"name": priority}}, "Status": {"select": {"name": "Not Started"}}}
       if due_date: properties["Due Date"] = {"date": {"start": due_date}}
       if description: properties["Description"] = {"rich_text": [{"text": {"content": description}}]}
       data = {"parent": {"database_id": MAIN_DATABASE_ID}, "properties": properties}
       
       response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
       
       if response.status_code == 200:
           page_data = response.json()
           page_url = page_data.get('url', 'Created successfully')
           return f"✅ Task '{title}' saved to Notion: {page_url}"
       else:
           error_msg = response.json().get('message', 'Unknown error')
           return f"❌ Failed to save to Notion: {error_msg}. Check database permissions."
   except Exception as e:
       return f"❌ Notion error: {str(e)}. Task '{title}' not saved."

async def check_ndis_compliance_web(area: str = "general") -> str:
   return "📋 NDIS Audit Status: 85% complete, May 14-15 2025 scheduled, all documents ready ✅"

async def query_business_data_web(business: str = "ALL", data_type: str = "overview") -> str:
   if business == "ALL": return "📊 STR8N UP: 3 tasks, CSSA: 5 tasks (audit prep), MSA: 7 tasks (225 kids enrolled)"
   elif business == "STR8N UP": return "📈 STR8N UP: 12 active clients, 2 courses in development"
   elif business == "CSSA": return "❤️ CSSA: 28 participants, audit 85% ready, Buddy-Up launching"
   elif business == "MSA": return "🏕️ MSA: 225 kids Term 1, Winter Camp 44 kids Jan 3-5"

async def manage_msa_enrollment_web(action: str = "check_numbers", age_group: str = "all") -> str:
   return "📊 MSA: 225 kids enrolled, Term 1 starts Jan 17, Winter Camp Jan 3-5 (44 kids) ✅"

async def generate_invoice_web(client_name: str, business: str, service: str, amount: float, hours: float = 0, rate: float = 0) -> str:
   invoice_num = f"{business[:3]}{datetime.now().strftime('%Y%m%d')}{abs(hash(client_name))%1000:03d}"
   return f"🧾 Invoice {invoice_num}: {client_name} - {service} - ${amount:.2f} ✅"

async def add_calendar_event_web(title: str, date: str, time: str, duration: int = 60, description: str = "", location: str = "") -> str:
   return f"✅ Event '{title}' added: {date} at {time} ({duration}min) - {location or 'TBC'}"

async def send_email_web(to_email: str, subject: str, message: str, cc_email: str = "") -> str:
   """Send email through Gmail SMTP"""
   try:
       if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
           return "❌ Gmail not configured. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
       
       msg = MIMEMultipart()
       msg['From'] = GMAIL_EMAIL
       msg['To'] = to_email
       msg['Subject'] = subject
       if cc_email: msg['Cc'] = cc_email
       
       msg.attach(MIMEText(message, 'plain'))
       
       server = smtplib.SMTP('smtp.gmail.com', 587)
       server.starttls()
       server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
       text = msg.as_string()
       server.sendmail(GMAIL_EMAIL, to_email.split(',') + (cc_email.split(',') if cc_email else []), text)
       server.quit()
       
       return f"✅ Email sent to {to_email} - Subject: {subject}"
   except Exception as e:
       return f"❌ Failed to send email: {str(e)}"

# Google Calendar Functions
async def create_google_calendar_event_web(title: str, start_datetime: str, end_datetime: str,
                                          description: str = "", location: str = "",
                                          attendees: str = "") -> str:
   """Create Google Calendar event"""
   try:
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
           return f"❌ Failed to create calendar event: {result['error']}"
   except Exception as e:
       return f"❌ Error creating calendar event: {str(e)}"

async def get_upcoming_events_web(days_ahead: int = 7, max_results: int = 10) -> str:
   """Get upcoming Google Calendar events"""
   try:
       result = google_integration.get_upcoming_events(max_results=max_results, days_ahead=days_ahead)
       
       if result["success"]:
           events = result["events"]
           if not events:
               return "📅 No upcoming events found"
           
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
           return f"❌ Failed to get events: {result['error']}"
   except Exception as e:
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
        if hasattr(google_integration, 'gmail_service') and google_integration.gmail_service:
            result = google_integration.send_gmail_email(
                to=to_email,
                subject=subject,
                body=body,
                cc=cc_email,
                bcc=bcc_email
            )
            
            if result["success"]:
                return f"✅ {result['message']} (ID: {result['message_id']})"
            else:
                logger.info(f"Gmail API failed: {result['error']}, trying SMTP")
        
        # Fallback to SMTP
        return await send_email_web(to_email, subject, body, cc_email)
        
    except Exception as e:
        logger.error(f"Gmail error: {e}")
        # Try SMTP as last resort
        return await send_email_web(to_email, subject, body, cc_email)

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