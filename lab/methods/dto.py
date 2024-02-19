from dataclasses import dataclass

from .model_fields import DetectorCharField
from .models import MethodModel


@dataclass
class DetectorDTO:
    name: str
    filters: list[str]


@dataclass
class MethodDTO:
    name: str
    detectors: list[DetectorDTO]


def method_model_to_dto(run: MethodModel) -> list[MethodDTO]:
    methods = []
    for method_field in run.get_method_fields():
        method = MethodDTO(name=method_field.method, detectors=[])
        if not getattr(
            run, method_field.attname
        ):  # Empty detectors if method is not enabled
            continue
        for detector_field in run.get_detector_fields():
            if detector_field.method == method.name:
                # DetectorCharField
                if isinstance(detector_field, DetectorCharField):
                    if not getattr(run, detector_field.attname):
                        continue
                    detector = DetectorDTO(
                        name=getattr(run, detector_field.attname),
                        filters=[],
                    )
                # DetectorBooleanField
                else:
                    detector = DetectorDTO(
                        name=detector_field.detector,
                        filters=[],
                    )
                    if not getattr(run, detector_field.attname):
                        continue
                for filter_field in run.get_filters_fields():
                    if (
                        filter_field.method == method.name
                        and filter_field.detector == detector.name
                    ):
                        detector.filters.append(getattr(run, filter_field.attname))
                method.detectors.append(detector)
        methods.append(method)
    return methods
