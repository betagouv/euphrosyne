from rest_framework import generics

from ..models import Project
from .permissions import IsLabAdminUser
from .serializers import ProjectSerializer


class ProjectList(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsLabAdminUser]
