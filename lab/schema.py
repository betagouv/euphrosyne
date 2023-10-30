import itertools

import graphene
from graphene_django import DjangoObjectType

from .models import ObjectGroup, Project


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = (
            "name",
            "problem_statement",
            "status",
            "comments",
        )

    object_group_labels = graphene.List(graphene.String)
    status = graphene.String()

    def resolve_status(self, info):  # pylint: disable=unused-argument
        return self.status

    def resolve_object_group_labels(self, info):  # pylint: disable=unused-argument
        project_materials = ObjectGroup.objects.filter(runs__project=self).values_list(
            "materials", flat=True
        )
        return set(itertools.chain(*project_materials))


class Query(graphene.ObjectType):
    last_projects = graphene.List(ProjectType, limit=graphene.Int())

    def resolve_last_projects(
        self, info, limit=None
    ):  # pylint: disable=unused-argument
        projects = Project.objects.only_finished().order_by("-created")
        if limit:
            projects = projects[:limit]
        return projects


schema = graphene.Schema(query=Query)
