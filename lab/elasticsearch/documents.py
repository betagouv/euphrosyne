from typing import TypedDict

import opensearchpy as os

from lab.methods.dto import DetectorDTO, MethodDTO


class _ObjectDict(TypedDict):
    label: str
    collection: str
    inventory: str


class ObjectDoc(os.InnerDoc):
    label = os.Text()
    collection = os.Keyword()
    inventory = os.Keyword()


class ObjectGroupDoc(os.InnerDoc):
    id = os.Keyword()
    c2rmf_id = os.Keyword()
    label = os.Text()
    materials = os.Text(multi=True)
    discovery_place_label = os.Text()
    collection = os.Keyword()
    inventory = os.Keyword()
    dating_period_label = os.Text()
    dating_era_label = os.Text()
    objects = os.Object(ObjectDoc, multi=True)

    def add_object(self, label: str, collection: str, inventory: str):
        self.objects.append(
            ObjectDoc(label=label, collection=collection, inventory=inventory)
        )


class LeaderDoc(os.InnerDoc):
    user_first_name = os.Keyword()
    user_last_name = os.Keyword()
    institution_name = os.Keyword()
    institution_country = os.Keyword()


class DetectorDoc(os.InnerDoc):
    name = os.Keyword()
    filters = os.Keyword(multi=True)


class MethodDoc(os.InnerDoc):
    name = os.Keyword()
    detectors = os.Object(DetectorDoc, multi=True)

    def add_detector(self, name: str, filters: list[str]):
        self.detectors.append(DetectorDoc(name=name, filters=filters))


class RunDoc(os.InnerDoc):
    id = os.Keyword()
    label = os.Text()
    start_date = os.Date()
    particle_type = os.Keyword()
    energy_in_kev = os.Keyword()
    beamline = os.Keyword()
    methods = os.Object(MethodDoc, multi=True)
    project_slug = os.Keyword()

    def add_method(
        self,
        name: str,
        detectors: list[DetectorDTO] | None = None,
    ):
        method_doc = MethodDoc(name=name)
        if detectors:
            for detector in detectors:
                method_doc.add_detector(detector.name, detector.filters)
        self.methods.append(method_doc)


class ProjectDoc(os.InnerDoc):
    name = os.Text()
    slug = os.Keyword()
    leader = os.Object(LeaderDoc)


class ProjectPageData(os.InnerDoc):
    leader = os.Object(LeaderDoc)
    runs = os.Object(RunDoc, multi=True)
    object_groups = os.Object(ObjectGroupDoc, multi=True)

    def add_object_group(
        self,
        object_group: ObjectGroupDoc,
        objects: list[_ObjectDict] | None = None,
    ):
        if objects:
            for obj in objects:
                object_group.add_object(
                    obj["label"], obj["collection"], obj["inventory"]
                )
        self.object_groups.append(object_group)

    def add_run(
        self,
        run: RunDoc,
        methods: list[MethodDTO] | None = None,
    ):
        if methods:
            for method in methods:
                run.add_method(method.name, method.detectors)
        self.runs.append(run)


class ObjectPageData(os.InnerDoc):
    runs = os.Object(RunDoc, multi=True)
    projects = os.Object(ProjectDoc, multi=True)

    def add_run(
        self,
        run: RunDoc,
        methods: list[MethodDTO] | None = None,
    ):
        if methods:
            for method in methods:
                run.add_method(method.name, method.detectors)
        self.runs.append(run)

    def add_project(
        self,
        name: str,
        slug: str,
        leader: LeaderDoc | None = None,
    ):
        project = ProjectDoc(name=name, slug=slug, leader=leader)
        self.projects.append(project)


class CatalogItem(os.Document):

    class Index:
        name = "catalog"

    id = os.Keyword()
    category = os.Keyword()
    name = os.Text()
    slug = os.Keyword()
    created = os.Date()
    materials = os.Keyword(multi=True)
    is_data_available = os.Boolean()

    project_page_data = os.Object(ProjectPageData)
    object_page_data = os.Object(ObjectPageData)

    # Project specific fields
    comments = os.Text()
    status = os.Keyword()
    discovery_place_points = os.GeoPoint(multi=True)

    # Object specific fields
    c2rmf_id = os.Keyword()
    discovery_place_label = os.Text()
    discovery_place_point = os.GeoPoint()
    collection = os.Text()
    inventory_number = os.Keyword()
    objects = os.Object(ObjectDoc, multi=True)
    collections = os.Keyword(multi=True)
    inventory_numbers = os.Keyword(multi=True)

    dating_period_label = os.Text()
    dating_period_theso_huma_num_id = os.Keyword()
    dating_period_theso_huma_num_parent_ids = os.Keyword(multi=True)
    dating_era_label = os.Text()
    dating_era_theso_huma_num_id = os.Keyword()
    dating_era_theso_huma_num_parent_ids = os.Keyword(multi=True)

    def add_object(
        self,
        label: str,
        collection: str,
        inventory: str,
    ):
        self.objects.append(
            ObjectDoc(label=label, collection=collection, inventory=inventory)
        )
