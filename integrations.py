"""
External service integrations: RentVine, Email, and Slack
"""
import os
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import logging
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class RentVineAPI:
    """RentVine property management system integration"""
    
    def __init__(self):
        self.subdomain = os.getenv("RENTVINE_SUBDOMAIN", "").rstrip('/')
        self.access_key = os.getenv("RENTVINE_ACCESS_KEY")
        self.secret = os.getenv("RENTVINE_SECRET")
        self.base_url = f"{self.subdomain}/api/v1"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for RentVine"""
        return {
            "X-Access-Key": self.access_key,
            "X-Secret": self.secret,
            "Content-Type": "application/json"
        }
    
    async def send_tenant_message(
        self,
        tenant_id: str,
        subject: str,
        message: str,
        attachments: Optional[List[str]] = None,
        reply_to_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message to tenant through RentVine"""
        try:
            payload = {
                "tenant_id": tenant_id,
                "subject": subject,
                "message": message,
                "sent_by": "system",
                "message_type": "email",
                "attachments": attachments or [],
                "reply_to": reply_to_message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages/send",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent via RentVine to tenant {tenant_id}")
                    return response.json()
                else:
                    logger.error(f"RentVine API error: {response.status_code} - {response.text}")
                    return {"error": f"Failed to send: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"RentVine send error: {str(e)}")
            return {"error": str(e)}
    
    async def get_tenant_info(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant information from RentVine"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tenants/{tenant_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Tenant not found: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"RentVine get tenant error: {str(e)}")
            return {"error": str(e)}
    
    async def create_work_order(
        self,
        unit_id: str,
        description: str,
        priority: str,
        category: str,
        assigned_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create work order in RentVine"""
        try:
            payload = {
                "unit_id": unit_id,
                "description": description,
                "priority": priority.upper(),
                "category": category,
                "status": "open",
                "assigned_to": assigned_to,
                "created_date": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/work-orders",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Work order created in RentVine for unit {unit_id}")
                    return response.json()
                else:
                    return {"error": f"Failed to create work order: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"RentVine work order error: {str(e)}")
            return {"error": str(e)}

class EmailService:
    """SMTP email service for direct email replies"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@aictive.com")
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add text and HTML parts
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return False

class SlackApprovalFlow:
    """Slack integration for human-in-the-loop approval"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.approval_channel = os.getenv("SLACK_APPROVAL_CHANNEL", "#approvals")
        
    async def request_approval(
        self,
        response_id: str,
        staff_name: str,
        tenant_email: str,
        email_subject: str,
        proposed_response: str,
        attachments: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send approval request to Slack with interactive buttons"""
        try:
            # Create Slack message with blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📧 Email Response Approval Required"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*From:* {staff_name}"},
                        {"type": "mrkdwn", "text": f"*To:* {tenant_email}"},
                        {"type": "mrkdwn", "text": f"*Subject:* {email_subject}"},
                        {"type": "mrkdwn", "text": f"*Category:* {metadata.get('category', 'Unknown')}"}
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Proposed Response:*\n```{proposed_response[:1000]}```"
                    }
                }
            ]
            
            # Add attachments info
            if attachments:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Attachments:* {', '.join(attachments)}"
                    }
                })
            
            # Add action buttons
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": f"approve_{response_id}",
                        "value": response_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✏️ Edit"},
                        "action_id": f"edit_{response_id}",
                        "value": response_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "action_id": f"reject_{response_id}",
                        "value": response_id
                    }
                ]
            })
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        "channel": self.approval_channel,
                        "blocks": blocks,
                        "text": f"Approval needed for response to {tenant_email}"
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Approval request sent to Slack for {response_id}")
                    return {"status": "pending", "response_id": response_id}
                else:
                    logger.error(f"Slack webhook error: {response.status_code}")
                    return {"error": "Failed to send to Slack"}
                    
        except Exception as e:
            logger.error(f"Slack approval error: {str(e)}")
            return {"error": str(e)}
    
    async def send_edit_dialog(
        self,
        response_id: str,
        current_text: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Send edit dialog to Slack user"""
        # In a real implementation, this would use Slack's dialog API
        # For now, we'll simulate by sending instructions
        try:
            message = {
                "channel": f"@{user_id}",
                "text": f"Please edit the response for ID {response_id}:",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Current Response:*\n```{current_text}```"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Reply to this message with your edited version."
                        }
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=message)
                return {"status": "edit_requested", "response_id": response_id}
                
        except Exception as e:
            logger.error(f"Slack edit dialog error: {str(e)}")
            return {"error": str(e)}

class ResponseOrchestrator:
    """Orchestrates the complete response flow"""
    
    def __init__(self):
        self.rentvine = RentVineAPI()
        self.email_service = EmailService()
        self.slack = SlackApprovalFlow()
        
    async def send_response(
        self,
        response_data: Dict[str, Any],
        approval_required: bool = True,
        use_rentvine: bool = True
    ) -> Dict[str, Any]:
        """Orchestrate sending response with approval flow"""
        
        response_id = f"resp_{datetime.utcnow().timestamp()}"
        
        # Step 1: Request approval if required
        if approval_required:
            approval_result = await self.slack.request_approval(
                response_id=response_id,
                staff_name=response_data["staff_name"],
                tenant_email=response_data["tenant_email"],
                email_subject=response_data["subject"],
                proposed_response=response_data["message"],
                attachments=response_data.get("attachments", []),
                metadata=response_data.get("metadata", {})
            )
            
            if "error" in approval_result:
                return approval_result
            
            # Wait for approval (in production, this would be webhook-based)
            # For demo, we'll simulate approval after 5 seconds
            await asyncio.sleep(5)
            
        # Step 2: Send via RentVine or email
        if use_rentvine and response_data.get("tenant_id"):
            # Send via RentVine
            result = await self.rentvine.send_tenant_message(
                tenant_id=response_data["tenant_id"],
                subject=response_data["subject"],
                message=response_data["message"],
                attachments=response_data.get("attachment_urls", []),
                reply_to_message_id=response_data.get("original_message_id")
            )
        else:
            # Send via email
            success = await self.email_service.send_email(
                to_email=response_data["tenant_email"],
                subject=response_data["subject"],
                body=response_data["message"],
                html_body=response_data.get("html_message"),
                attachments=response_data.get("attachments"),
                reply_to=response_data.get("reply_to_email")
            )
            result = {"success": success} if success else {"error": "Email send failed"}
        
        # Step 3: Log the response
        logger.info(f"Response {response_id} sent: {result}")
        
        # Step 4: Update any related work orders if maintenance
        if response_data.get("metadata", {}).get("category") == "maintenance":
            if response_data.get("create_work_order"):
                wo_result = await self.rentvine.create_work_order(
                    unit_id=response_data.get("unit_id"),
                    description=response_data.get("issue_description"),
                    priority=response_data.get("priority", "medium"),
                    category="maintenance",
                    assigned_to=response_data.get("assigned_technician")
                )
                result["work_order"] = wo_result
        
        return {
            "response_id": response_id,
            "status": "sent",
            "method": "rentvine" if use_rentvine else "email",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

# Webhook handler for Slack interactions
async def handle_slack_action(action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Slack button actions"""
    action = action_data.get("actions", [{}])[0]
    action_id = action.get("action_id", "")
    response_id = action.get("value", "")
    
    if action_id.startswith("approve_"):
        # Approved - proceed with sending
        return {"status": "approved", "response_id": response_id}
        
    elif action_id.startswith("edit_"):
        # Request edit
        slack = SlackApprovalFlow()
        return await slack.send_edit_dialog(
            response_id=response_id,
            current_text="[current response text]",
            user_id=action_data.get("user", {}).get("id")
        )
        
    elif action_id.startswith("reject_"):
        # Rejected
        return {"status": "rejected", "response_id": response_id}
    
    return {"status": "unknown_action"}