from rest_framework import generics

from ..models import Run
from .permissions import IsLabAdminUser
from .serializers import RunMethodsSerializer


class RunMethodsView(generics.RetrieveAPIView):
    queryset = Run.objects.all()
    serializer_class = RunMethodsSerializer
    permission_classes = [IsLabAdminUser]
