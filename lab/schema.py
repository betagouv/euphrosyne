# pylint: disable=no-member,unused-argument
import itertools

import graphene
from django.db.models import Prefetch, Q
from graphene_django import DjangoObjectType

from euphro_auth.models import User
from lab.methods.model_fields import DetectorCharField

from .models import Institution, Object, ObjectGroup, Participation, Project, Run


class ObjectType(DjangoObjectType):
    class Meta:
        model = Object
        fields = ("label", "collection")


class ObjectGroupType(DjangoObjectType):
    data_available = graphene.Boolean(required=True)

    class Meta:
        model = ObjectGroup
        fields = (
            "id",
            "c2rmf_id",
            "label",
            "materials",
            "discovery_place",
            "collection",
            "dating",
            "object_set",
            "runs",
            "data_available",
            "created",
        )

    def resolve_data_available(self, info):
        if not hasattr(self, "is_data_available"):
            raise AttributeError(
                "is_data_available must be annotated on the queryset in the \
                Quey section (lab.schema.Query). See \
                https://docs.djangoproject.com/en/4.2/topics/db/aggregation/"
            )
        return self.is_data_available


class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution
        fields = ("name", "country")


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class LeaderType(DjangoObjectType):
    class Meta:
        model = Participation
        fields = ("user", "institution")


class DetectorType(graphene.ObjectType):
    name = graphene.String(required=True)
    enabled = graphene.Boolean(required=True)
    filters = graphene.List(graphene.String, required=True)


class MethodType(graphene.ObjectType):
    name = graphene.String(required=True)
    enabled = graphene.Boolean(required=True)
    detectors = graphene.List(DetectorType, required=True)


class RunType(DjangoObjectType):
    methods = graphene.List(MethodType)

    class Meta:
        model = Run
        fields = (
            "label",
            "start_date",
            "particle_type",
            "energy_in_keV",
            "beamline",
            "methods",
            "project",
        )

    def resolve_methods(self, info):
        methods = []
        for method_field in self.get_method_fields():
            method = MethodType(name=method_field.method, detectors=[])
            if not getattr(
                self, method_field.attname
            ):  # Empty detectors if method is not enabled
                continue
            for detector_field in self.get_detector_fields():
                if detector_field.method == method.name:
                    # DetectorCharField
                    if isinstance(detector_field, DetectorCharField):
                        if not getattr(self, detector_field.attname):
                            continue
                        detector = DetectorType(
                            name=getattr(self, detector_field.attname),
                            filters=[],
                        )
                    # DetectorBooleanField
                    else:
                        detector = DetectorType(
                            name=detector_field.detector,
                            filters=[],
                        )
                        if not getattr(self, detector_field.attname):
                            continue
                    for filter_field in self.get_filters_fields():
                        if (
                            filter_field.method == method.name
                            and filter_field.detector == detector.name
                        ):
                            detector.filters.append(getattr(self, filter_field.attname))
                    method.detectors.append(detector)
            methods.append(method)
        return methods


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = (
            "name",
            "status",
            "comments",
            "runs",
            "leader",
            "object_groups",
            "slug",
            "created",
        )

    object_group_materials = graphene.List(graphene.String)
    status = graphene.String()
    leader = graphene.Field(LeaderType)
    object_groups = graphene.List(ObjectGroupType)

    def resolve_status(self, info):
        return self.status

    def resolve_object_group_materials(self, info):
        project_materials = ObjectGroup.objects.filter(runs__project=self).values_list(
            "materials", flat=True
        )
        return set(itertools.chain(*project_materials))

    def resolve_leader(self, info):
        return self.leader

    def resolve_object_groups(self, info):
        return list(
            set(
                objectgroup
                for run in self.runs.all()
                for objectgroup in run.run_object_groups.all()
            )
        )


class Query(graphene.ObjectType):
    last_projects = graphene.List(ProjectType, limit=graphene.Int())
    project_detail = graphene.Field(ProjectType, slug=graphene.String())
    object_group_detail = graphene.Field(ObjectGroupType, pk=graphene.String())

    def resolve_last_projects(self, info, limit=None):
        projects = Project.objects.only_finished().order_by("-created").distinct()
        if limit:
            projects = projects[:limit]
        return projects

    def resolve_project_detail(self, _, slug):
        return (
            Project.objects.only_finished()
            .prefetch_related(
                "runs",
                "runs__run_object_groups",
                "runs__run_object_groups__object_set",
            )
            .filter(slug=slug)
            .first()
        )

    def resolve_object_group_detail(self, _, pk):  # pylint: disable=invalid-name
        return (
            ObjectGroup.objects.filter(pk=pk)
            .prefetch_related(Prefetch("runs", queryset=Run.objects.only_finished()))
            .annotate(is_data_available=Q(runs__project__is_data_available=True))
            .first()
        )


schema = graphene.Schema(query=Query)