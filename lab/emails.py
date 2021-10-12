from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import gettext_lazy as _

from .models import Project


def send_project_invitation_email(email: str, project: Project):
    """
    Send an email with an invitation link based on a user ID and a token used for
    authentication.
    """

    context = {
        "email": email,
        "site_url": settings.SITE_URL,
        "project_id": project.id,
        "project_name": project.name,
    }
    subject = _(f"[Euphrosyne] Invitation to join project {project.name}")
    body = loader.render_to_string("project_invitation_email.txt", context)

    email_message = EmailMultiAlternatives(subject=subject, body=body, to=[email])
    html_email = loader.render_to_string("project_invitation_email.html", context)
    email_message.attach_alternative(html_email, "text/html")

    email_message.send()
