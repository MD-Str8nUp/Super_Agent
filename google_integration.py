import json
import os
from datetime import datetime, timedelta
import base64
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleIntegration:
    def __init__(self, credentials_file="google-credentials.json"):
        """Initialize Google API services using service account credentials"""
        self.calendar_service = None
        self.gmail_service = None
        self.gmail_enabled = False
        self.calendar_enabled = False
        
        try:
            if not os.path.exists(credentials_file):
                logger.warning(f"Google credentials file {credentials_file} not found. Google services will be disabled.")
                return
                
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=[
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.modify'
                ]
            )
            
            # Build Google API services with error handling
            try:
                self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
                self.calendar_enabled = True
                logger.info("Google Calendar service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Calendar service: {e}")
                
            try:
                self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
                # Test Gmail service with a simple call
                self._test_gmail_service()
            except Exception as e:
                logger.warning(f"Gmail service initialization failed: {e}")
                self.gmail_service = None
            
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            
    def _test_gmail_service(self):
        """Test Gmail service availability"""
        try:
            if self.gmail_service:
                # Try to get user profile (minimal permission test)
                profile = self.gmail_service.users().getProfile(userId='me').execute()
                self.gmail_enabled = True
                logger.info("Gmail service test successful")
        except Exception as e:
            logger.warning(f"Gmail service test failed: {e}")
            self.gmail_service = None
            self.gmail_enabled = False

    def send_email(self, to_email, subject, body, from_email=None):
        """Send email using Gmail API with proper error handling"""
        if not self.gmail_enabled or not self.gmail_service:
            raise Exception("Gmail service not available - use SMTP fallback")
        
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = self.gmail_service.users().messages().send(
                userId="me",
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully via Gmail API to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail API error: {e}")
            # Disable Gmail for this session if we get auth errors
            if "Precondition check failed" in str(e) or "rateLimitExceeded" in str(e):
                self.gmail_enabled = False
                logger.warning("Gmail API disabled due to authentication/quota issues")
            raise e

    def create_calendar_event(self, title: str, start_time: str, end_time: str,
                            description: str = "", location: str = "",
                            attendees: List[str] = None) -> Dict[str, Any]:
        """Create a Google Calendar event"""
        try:
            if not self.calendar_service:
                return {"success": False, "error": "Calendar service not initialized"}

            # Fix datetime format - ensure proper ISO format
            def format_datetime(dt_str):
                try:
                    # Parse various datetime formats and convert to ISO
                    if 'T' in dt_str and dt_str.endswith('Z'):
                        return dt_str  # Already in ISO format
                    elif 'T' in dt_str:
                        # Add timezone if missing
                        if '+' not in dt_str and 'Z' not in dt_str:
                            return dt_str + '+10:00'  # Sydney timezone
                        return dt_str
                    else:
                        # Parse date/time format like "30/05/2025 04:31 PM"
                        from datetime import datetime
                        dt = datetime.strptime(dt_str, "%d/%m/%Y %I:%M %p")
                        return dt.strftime("%Y-%m-%dT%H:%M:%S+10:00")
                except:
                    # Fallback - assume it's a valid format
                    return dt_str

            formatted_start = format_datetime(start_time)
            formatted_end = format_datetime(end_time)

            event = {
                'summary': title,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': formatted_start,
                    'timeZone': 'Australia/Sydney',
                },
                'end': {
                    'dateTime': formatted_end,
                    'timeZone': 'Australia/Sydney',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            # Use primary calendar or specify calendar ID
            event = self.calendar_service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            return {
                "success": True, 
                "event_id": event['id'],
                "event_link": event.get('htmlLink', ''),
                "message": f"✅ Event '{title}' created successfully"
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return {"success": False, "error": f"Calendar API error: {e}"}
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"success": False, "error": str(e)}

    def get_upcoming_events(self, max_results: int = 10, days_ahead: int = 7) -> Dict[str, Any]:
        """Get upcoming calendar events"""
        try:
            if not self.calendar_service:
                return {"success": False, "error": "Calendar service not initialized"}

            # Fix datetime formatting for Google Calendar API
            now = datetime.utcnow()
            future_date = now + timedelta(days=days_ahead)
            
            # Ensure proper ISO format with timezone
            time_min = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            time_max = future_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'id': event['id'],
                    'title': event.get('summary', 'No Title'),
                    'start': start,
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
                })
            
            return {
                "success": True,
                "events": formatted_events,
                "count": len(formatted_events)
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return {"success": False, "error": f"Calendar API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return {"success": False, "error": str(e)}

    def read_recent_emails(self, max_results: int = 10, query: str = "is:unread") -> Dict[str, Any]:
        """Read recent emails from Gmail"""
        try:
            if not self.gmail_service:
                return {"success": False, "error": "Gmail service not initialized - Please add google-credentials.json file"}

            # Get list of messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return {"success": True, "emails": [], "count": 0, "message": "No emails found"}
            
            formatted_emails = []
            for msg in messages:
                try:
                    message = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()
                    
                    headers = message['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # Get email body
                    body = self._extract_email_body(message['payload'])
                    
                    formatted_emails.append({
                        'id': msg['id'],
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'snippet': message.get('snippet', ''),
                        'body': body[:500] + '...' if len(body) > 500 else body  # Truncate long bodies
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing email {msg['id']}: {e}")
                    continue
            
            return {
                "success": True,
                "emails": formatted_emails,
                "count": len(formatted_emails)
            }
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            if e.resp.status == 400 and error_details.get('reason') == 'failedPrecondition':
                return {"success": False, "error": "Gmail API not enabled for this service account. Please enable Gmail API in Google Cloud Console and add service account email to Google Workspace."}
            elif e.resp.status == 403:
                return {"success": False, "error": "Permission denied. Service account needs domain-wide delegation for Gmail access."}
            else:
                logger.error(f"Gmail API error: {e}")
                return {"success": False, "error": f"Gmail API error: {e}"}
        except Exception as e:
            logger.error(f"Error reading emails: {e}")
            return {"success": False, "error": f"Gmail connection error: {str(e)}"}

    def send_gmail_email(self, to: str, subject: str, body: str, 
                        cc: str = "", bcc: str = "") -> Dict[str, Any]:
        """Send email via Gmail API"""
        try:
            if not self.gmail_service:
                return {"success": False, "error": "Gmail service not initialized"}

            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": send_message['id'],
                "message": f"✅ Email sent to {to}"
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return {"success": False, "error": f"Gmail API error: {e}"}
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}

    def _extract_email_body(self, payload):
        """Extract email body from Gmail message payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body

    def get_calendar_free_busy(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Check calendar availability for a time period"""
        try:
            if not self.calendar_service:
                return {"success": False, "error": "Calendar service not initialized"}

            body = {
                "timeMin": start_time,
                "timeMax": end_time,
                "items": [{"id": "primary"}]
            }
            
            freebusy = self.calendar_service.freebusy().query(body=body).execute()
            busy_times = freebusy['calendars']['primary']['busy']
            
            return {
                "success": True,
                "busy_times": busy_times,
                "is_free": len(busy_times) == 0
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return {"success": False, "error": f"Calendar API error: {e}"}
        except Exception as e:
            logger.error(f"Error checking calendar availability: {e}")
            return {"success": False, "error": str(e)}

# Initialize global instance
google_integration = GoogleIntegration()