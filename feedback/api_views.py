from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .serializers import FeedbackFormSerializer


@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
@api_view(["POST"])
def feedback_view(request):
    serializer = FeedbackFormSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        email = data["email"]
        message = data["message"]
        name = data["name"]

        # Prepare email
        email_message = EmailMessage(
            subject=f"Feedback from {name}",
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.FEEDBACK_EMAILS,
            reply_to=[email],
        )

        # Attach files
        for file in request.FILES.values():
            email_message.attach(
                file.name,
                file.file.read(),  # Read the file content
                file.content_type,
            )

        # Send email
        email_message.send()

        return Response({"detail": "feedback sent"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
