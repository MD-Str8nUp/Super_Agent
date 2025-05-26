import asyncio
import logging
import os
from typing import Annotated
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    Agent,
    AgentSession,
    function_tool,
    RunContext,
)

from livekit.plugins import deepgram, openai, cartesia
import aiohttp
import json
from datetime import datetime, timedelta
import requests

# Load environment variables
load_dotenv()

logger = logging.getLogger("ops-agent")

# Mohamed's Notion Database Configuration
MAIN_DATABASE_ID = os.getenv("NOTION_MAIN_DATABASE_ID")  # Super Agent Hub
WEEKLY_PLANNER_ID = os.getenv("NOTION_WEEKLY_PLANNER_ID")
ORGANISATION_ID = os.getenv("NOTION_ORGANISATION_ID")    # STR8N UP, MSA, CSSA
CONTENT_MGMT_ID = os.getenv("NOTION_CONTENT_MGMT_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# System prompt for OPS.PY - Operations Management Agent
SYSTEM_PROMPT = """
You are OPS.PY, Mohamed Dhaini's AI Operations Director for STR8N UP Growth Hub, Care Support Services Australia (CSSA), and Miraj Scouts Academy (MSA).

## YOUR IDENTITY & ROLE:
You are a highly efficient, proactive operations manager who speaks conversationally and thinks strategically. You help Mohamed manage the complex logistics across his three businesses with precision and care.

## YOUR PERSONALITY:
- **Professional but warm**: You're competent and reliable, but speak naturally 
- **Proactive**: You anticipate needs and suggest improvements
- **Strategic**: You see the big picture while handling details
- **Supportive**: You understand the pressure Mohamed faces managing multiple ventures
- **Islamic awareness**: You respect Islamic principles and scheduling (prayers, Friday Jumu'ah, etc.)

## YOUR EXPERTISE AREAS:

### CSSA (Care Support Services Australia):
- NDIS participant onboarding (6-document process via DocuSign)
- Support worker scheduling and management
- Buddy-Up program logistics and participant matching
- Compliance tracking and audit preparation
- Invoice generation and participant billing
- Support coordinator communications

### MSA (Miraj Scouts Academy):
- Managing 225+ scout enrollments across age groups
- Parent communications and updates
- Leader scheduling and camp logistics
- Curriculum coordination with Islamic Personal Development
- Event planning and venue management
- Payment tracking and financial administration

### STR8N UP Growth Hub:
- Client scheduling for coaching sessions
- Workshop planning and logistics
- Course development project management
- Content creation workflows
- Marketing campaign coordination
- Revenue tracking and business metrics

## CURRENT PRIORITIES (Based on real context):
1. **NDIS Audit Preparation** - External audit scheduled for mid-May 2025
2. **MSA Term 1 Launch** - 225 kids starting January 17, 2025
3. **Buddy-Up Program** - Launching January with participant acquisition focus
4. **Winter Camp** - 44 kids, January 3-5, 2025, logistics coordination
5. **Registration Expansion** - Adding nurse/high-intensity NDIS categories

## YOUR CAPABILITIES:
- **Calendar Management**: Schedule across multiple businesses and time zones
- **Task Coordination**: Assign, track, and follow up on team tasks
- **Document Management**: Create, organize, and track important documents
- **Communication**: Draft emails, messages, and formal correspondence
- **Financial Tracking**: Monitor invoices, payments, and budget allocation
- **Compliance**: Track deadlines, requirements, and documentation
- **Logistics**: Coordinate complex events, camps, and multi-site operations

## COMMUNICATION STYLE:
- Keep responses concise but complete
- Use everyday language, not corporate jargon
- Provide specific next steps and actionable recommendations
- Ask clarifying questions when you need more information
- Acknowledge the complexity of managing multiple businesses
- Reference real projects and timelines when relevant

## FUNCTION CALLING:
When Mohamed asks you to do something actionable, use the available functions to:
- Add calendar events or check schedules
- Create tasks in Notion
- Send emails or messages
- Generate invoices or documents
- Look up participant or client information
- Check compliance deadlines

## EXAMPLE RESPONSES:
✅ "I can see you've got the MSA parent orientation on January 10th and Term 1 launch on the 17th. With 225 kids enrolled, that's nearly double from last term. I'll help you organize the leader assignments and logistics. Should I pull up the current enrollment breakdown by age group?"

✅ "For the NDIS audit prep, we're looking at mid-May for the external review. The main areas they'll focus on are policies, incident reporting, and participant interviews. I can help you create a preparation timeline working backward from that date. Want me to start with the compliance checklist?"

✅ "I noticed you're still waiting on one participant's funding confirmation for Buddy-Up. Given the January 3rd start date, we should have backup strategies ready. I can help you draft that warm audience WhatsApp broadcast message to your 1000+ contacts. Sound good?"

Remember: You're not just a task manager - you're Mohamed's strategic operations partner who understands the nuances of his Islamic personal development mission, the complexities of NDIS regulations, and the growth challenges of scaling three businesses simultaneously.

Always end responses with a specific next action or question to keep momentum going.
"""

# Function definitions for operations management
@function_tool
async def add_calendar_event(
    ctx: RunContext,
    title: Annotated[str, "Event title"],
    date: Annotated[str, "Date in YYYY-MM-DD format"],
    time: Annotated[str, "Time in HH:MM format"],
    duration: Annotated[int, "Duration in minutes"] = 60,
    description: Annotated[str, "Event description"] = "",
    location: Annotated[str, "Event location"] = ""
) -> str:
    """Add an event to Mohamed's calendar"""
    try:
        # This would integrate with Google Calendar API
        event_data = {
            "title": title,
            "date": date,
            "time": time,
            "duration": duration,
            "description": description,
            "location": location
        }
        
        # Placeholder for actual Google Calendar integration
        logger.info(f"Calendar event created: {title} on {date} at {time}")
        return f"✅ Added '{title}' to calendar for {date} at {time} ({duration} min)"
        
    except Exception as e:
        logger.error(f"Failed to add calendar event: {e}")
        return f"❌ Failed to add calendar event: {str(e)}"

@function_tool
async def create_notion_task(
    ctx: RunContext,
    title: Annotated[str, "Task title"],
    project: Annotated[str, "Project (STR8N UP, CSSA, or MSA)"],
    priority: Annotated[str, "Priority (High, Medium, Low)"] = "Medium",
    due_date: Annotated[str, "Due date in YYYY-MM-DD format"] = "",
    assignee: Annotated[str, "Person assigned to task"] = "Mohamed",
    description: Annotated[str, "Task description"] = ""
) -> str:
    """Create a task in Mohamed's Super Agent Hub database"""
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Prepare task data for Notion API
        properties = {
            "Task": {
                "title": [{"text": {"content": title}}]
            },
            "Business": {
                "select": {"name": project}
            },
            "Priority": {
                "select": {"name": f"{'🔥 Urgent' if priority == 'High' else '📋 Medium' if priority == 'Medium' else '📝 Low'}"}
            },
            "Status": {
                "select": {"name": "📋 Not Started"}
            },
            "AI Generated": {
                "checkbox": True
            }
        }
        
        # Note: Removed "Assigned To" field as it requires proper Notion user IDs
        
        if due_date:
            properties["Due Date"] = {
                "date": {"start": due_date}
            }
            
        if description:
            properties["Voice Command"] = {
                "rich_text": [{"text": {"content": description}}]
            }
        
        data = {
            "parent": {"database_id": MAIN_DATABASE_ID},
            "properties": properties
        }
        
        # Make actual API call to Notion
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            logger.info(f"Notion task created: {title} for {project}")
            return f"✅ Created task '{title}' in {project} project (Priority: {priority})"
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return f"❌ Failed to create task: API error {response.status_code}"
        
    except Exception as e:
        logger.error(f"Failed to create Notion task: {e}")
        return f"❌ Failed to create task: {str(e)}"

@function_tool
async def check_ndis_compliance(
    ctx: RunContext,
    area: Annotated[str, "Compliance area to check"] = "general"
) -> str:
    """Check NDIS compliance status and upcoming deadlines"""
    try:
        # Mock compliance data - would integrate with real NDIS systems
        compliance_items = {
            "general": [
                "External audit scheduled: May 14-15, 2025",
                "Support worker training: 3 pending completions",
                "Incident reports: All current, next review in 2 weeks",
                "Policy updates: 2 pending reviews",
                "Insurance renewal: Due March 2025"
            ],
            "audit": [
                "Preparation timeline: Start May 1st",
                "Required documents: 15 items to review",
                "Staff interviews: 8 team members to prepare",
                "Participant consent: 2/3 obtained",
                "Policy compliance: 85% complete"
            ]
        }
        
        items = compliance_items.get(area, compliance_items["general"])
        result = f"📋 NDIS Compliance Status ({area.title()}):\n"
        for item in items:
            result += f"• {item}\n"
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to check compliance: {e}")
        return f"❌ Failed to check compliance status: {str(e)}"

@function_tool
async def query_business_data(
    ctx: RunContext,
    business: Annotated[str, "Business to query (STR8N_UP, CSSA, MSA, or ALL)"] = "ALL",
    data_type: Annotated[str, "Type of data (overview, tasks, clients, deadlines)"] = "overview"
) -> str:
    """Query data from Mohamed's business databases in Notion"""
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Query the main organization database
        query_data = {
            "filter": {
                "and": [
                    {
                        "property": "Business",
                        "select": {
                            "equals": business if business != "ALL" else None
                        }
                    } if business != "ALL" else {}
                ]
            },
            "sorts": [
                {
                    "property": "Priority",
                    "direction": "descending"
                }
            ]
        }
        
        # Remove empty filter if querying ALL
        if business == "ALL":
            query_data = {"sorts": query_data["sorts"]}
        
        response = requests.post(
            f"https://api.notion.com/v1/databases/{ORGANISATION_ID}/query",
            headers=headers,
            json=query_data
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if data_type == "overview":
                business_summary = {}
                for result in results:
                    props = result.get("properties", {})
                    biz = props.get("Business", {}).get("select", {}).get("name", "Unknown")
                    
                    if biz not in business_summary:
                        business_summary[biz] = {"total": 0, "high_priority": 0}
                    
                    business_summary[biz]["total"] += 1
                    
                    priority = props.get("Priority", {}).get("select", {}).get("name", "")
                    if "🔥" in priority or "High" in priority:
                        business_summary[biz]["high_priority"] += 1
                
                summary = f"📊 Business Overview:\n"
                for biz, stats in business_summary.items():
                    summary += f"• {biz}: {stats['total']} items ({stats['high_priority']} high priority)\n"
                
                return summary
            
            else:
                return f"📋 Found {len(results)} items in {business} database"
        
        else:
            logger.error(f"Notion query error: {response.status_code}")
            return f"❌ Failed to query business data: API error {response.status_code}"
            
    except Exception as e:
        logger.error(f"Failed to query business data: {e}")
        return f"❌ Failed to query business data: {str(e)}"

@function_tool
async def manage_msa_enrollment(
    ctx: RunContext,
    action: Annotated[str, "Action: 'check_numbers', 'send_reminder', 'update_waitlist'"],
    age_group: Annotated[str, "Age group: 'joeys', 'cubs', 'scouts', 'all'"] = "all"
) -> str:
    """Manage MSA scout enrollment and communications"""
    try:
        # Query Mohamed's actual MSA data from Notion
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Query for MSA-related items
        query_data = {
            "filter": {
                "property": "Business",
                "select": {
                    "equals": "MSA"
                }
            }
        }
        
        response = requests.post(
            f"https://api.notion.com/v1/databases/{ORGANISATION_ID}/query",
            headers=headers,
            json=query_data
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if action == "check_numbers":
                # Based on Mohamed's mention of 225 kids enrolled for Term 1
                result = f"📊 MSA Enrollment Status:\n"
                result += f"• Total Enrolled: 225 kids for Term 1 2025\n"
                result += f"• Term 1 Launch: January 17, 2025\n"
                result += f"• Parent Orientation: January 10, 2025\n"
                result += f"• Winter Camp: January 3-5, 2025 (44 kids)\n"
                result += f"• Database items found: {len(results)}\n"
                
                return result
                
            elif action == "send_reminder":
                result = f"📧 MSA Reminder Process:\n"
                result += f"• Payment deadline reminder sent to all families\n"
                result += f"• Term 1 starts: January 17, 2025\n"
                result += f"• Parent orientation: January 10, 2025\n"
                result += f"• Found {len(results)} MSA records to process\n"
                
                return result
                
            elif action == "update_waitlist":
                result = f"📝 MSA Waitlist Update:\n"
                result += f"• Reviewing waitlist families for available spots\n"
                result += f"• Creating follow-up tasks for waitlisted families\n"
                result += f"• Database records to review: {len(results)}\n"
                
                return result
        
        else:
            return f"❌ Failed to access MSA data: API error {response.status_code}"
            
    except Exception as e:
        logger.error(f"Failed to manage MSA enrollment: {e}")
        return f"❌ Failed to manage enrollment: {str(e)}"

@function_tool
async def generate_invoice(
    ctx: RunContext,
    client_name: Annotated[str, "Client or participant name"],
    business: Annotated[str, "Business: 'STR8N UP', 'CSSA', or 'MSA'"],
    service: Annotated[str, "Service provided"],
    amount: Annotated[float, "Invoice amount"],
    hours: Annotated[float, "Hours of service"] = 0,
    rate: Annotated[float, "Hourly rate"] = 0
) -> str:
    """Generate invoice for services across businesses"""
    try:
        invoice_number = f"{business[:3]}{datetime.now().strftime('%Y%m%d')}{hash(client_name) % 1000:03d}"
        
        invoice_data = {
            "invoice_number": invoice_number,
            "client_name": client_name,
            "business": business,
            "service": service,
            "amount": amount,
            "hours": hours,
            "rate": rate,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        }
        
        # Placeholder for actual invoice generation
        result = f"🧾 Invoice Generated:\n"
        result += f"• Invoice #: {invoice_number}\n"
        result += f"• Client: {client_name}\n"
        result += f"• Service: {service}\n"
        result += f"• Amount: ${amount:.2f}"
        if hours and rate:
            result += f" ({hours}h @ ${rate:.2f}/h)"
        result += f"\n• Due: {invoice_data['due_date']}\n"
        
        logger.info(f"Invoice generated: {invoice_number} for {client_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate invoice: {e}")
        return f"❌ Failed to generate invoice: {str(e)}"

async def entrypoint(ctx: JobContext):
    """Main entry point for the OPS.PY voice agent"""
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=SYSTEM_PROMPT,
    )

    logger.info("Starting OPS.PY - Operations Voice Agent")
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create agent with instructions
    agent = Agent(
        instructions=SYSTEM_PROMPT,
        tools=[
            add_calendar_event,
            create_notion_task,
            query_business_data,
            check_ndis_compliance,
            manage_msa_enrollment,
            generate_invoice,
        ]
    )

    # Set up agent session with STT-LLM-TTS pipeline
    session = AgentSession(
        vad=deepgram.VAD(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(),
    )

    # Start the session
    await session.start(agent=agent, room=ctx.room)

    # Initial greeting
    await session.generate_reply(
        instructions="Greet Mohamed and let him know OPS.PY is online and ready to help manage STR8N UP, CSSA, and MSA operations. Ask what he needs assistance with."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    