from django.db.models import QuerySet
from django.urls import reverse
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser

from ..models import Run
from ..permissions import is_lab_admin


class CalendarSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source="project_id")
    title = serializers.SerializerMethodField()
    start = serializers.DateTimeField(source="start_date")
    end = serializers.DateTimeField(source="end_date")
    url = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = (
            "id",
            "group_id",
            "title",
            "start",
            "end",
            "url",
        )

    def get_title(self, obj: Run):
        return f"{obj.label} [{obj.project.name}]"

    def get_url(self, obj: Run):
        return reverse("admin:lab_run_change", args=[obj.id])


class CalendarView(ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = CalendarSerializer

    def get_queryset(self):
        qs: QuerySet = Run.objects
        if not is_lab_admin(self.request.user):
            qs = qs.filter(project__members__id=self.request.user.id).distinct()
        if "start" in self.request.query_params:
            qs = qs.filter(start_date__gte=self.request.query_params["start"])
        if "end" in self.request.query_params:
            qs = qs.filter(start_date__lte=self.request.query_params["end"])
        return qs.all()
