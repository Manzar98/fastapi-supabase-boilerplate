"""
Email handling utilities.
"""

import logging
from typing import List, Union, Optional
import resend
from core.config import settings
from utils.template_renderer import render_email_template

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key

def send_email(
    to: Union[str, List[str]],
    subject: str,
    body: str
) -> Optional[dict]:
    """
    Send an email using Resend.

    Args:
        to (str | list[str]): Recipient email address or list of addresses.
        subject (str): Email subject.
        body (str): HTML body of the email.

    Returns:
        dict | None: The Resend API response if successful, otherwise None.
    """
    if not to or not subject or not body:
        logger.warning("Email not sent: missing recipient, subject, or body.")
        return None

    try:
        params: resend.Emails.SendParams = {
            "from": f"Deltacron <{settings.resend_from_email}>",
            "to": to if isinstance(to, list) else [to],
            "subject": subject,
            "html": body,
        }
        response: resend.Email = resend.Emails.send(params)
        logger.info("Email sent to %s with subject '%s'", to, subject)
        return response
    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error("Failed to send email to %s: %s", to, e, exc_info=True)
        return None


def send_templated_email(
    to: Union[str, List[str]],
    subject: str,
    template_name: str,
    **template_context: any
) -> Optional[dict]:
    """
    Send an email using a Jinja2 template.

    Args:
        to (str | list[str]): Recipient email address or list of addresses.
        subject (str): Email subject.
        template_name (str): Name of the template file (e.g., 'reset_password.html').
        **template_context: Template variables to pass to the template.

    Returns:
        dict | None: The Resend API response if successful, otherwise None.
    """
    try:
        # Render the template
        html_body = render_email_template(template_name, **template_context)
        
        # Send the email using the existing send_email function
        return send_email(to, subject, html_body)
    except Exception as e:
        logger.error("Failed to send templated email to %s: %s", to, e, exc_info=True)
        return None
