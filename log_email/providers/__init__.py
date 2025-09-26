from .mailjet import MailjetProvider


def get_email_provider():
    # For now, we only support Mailjet. In the future, you could add logic here
    return MailjetProvider()
