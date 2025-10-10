"""
Template rendering utilities using Jinja2.
"""

import os
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Create Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def render_template(template_name: str, **context: Any) -> str:
    """
    Render a Jinja2 template with the given context.

    Args:
        template_name (str): Name of the template file (e.g., 'reset_password.html')
        **context: Template variables to pass to the template

    Returns:
        str: Rendered HTML content

    Raises:
        TemplateNotFound: If the template file doesn't exist
    """
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except TemplateNotFound as e:
        raise TemplateNotFound(
            f"Template '{template_name}' not found in templates directory"
        ) from e


def render_email_template(template_name: str, **context: Any) -> str:
    """
    Convenience function for rendering email templates.

    Args:
        template_name (str): Name of the email template file
        **context: Template variables

    Returns:
        str: Rendered email HTML content
    """
    return render_template(template_name, **context)
