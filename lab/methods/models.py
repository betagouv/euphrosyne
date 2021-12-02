from typing import Optional, Union

from django.db import models

from .model_fields import (
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from .types import OTHER_VALUE, Detector, Filter, Method


class MethodModel(models.Model):
    class Meta:
        abstract = True

    method_PIXE = MethodBooleanField(Method("PIXE"))
    method_PIGE = MethodBooleanField(Method("PIGE"))
    method_IBIL = MethodBooleanField(Method("IBIL"))
    method_FORS = MethodBooleanField(Method("FORS"))
    method_RBS = MethodBooleanField(Method("RBS"))
    method_ERDA = MethodBooleanField(Method("ERDA"))
    method_NRA = MethodBooleanField(Method("NRA"))

    detector_LE0 = DetectorBooleanField(Method("PIXE"), Detector("LE0"))
    detector_HE1 = DetectorBooleanField(Method("PIXE"), Detector("HE1"))
    detector_HE2 = DetectorBooleanField(Method("PIXE"), Detector("HE2"))
    detector_HE3 = DetectorBooleanField(Method("PIXE"), Detector("HE3"))
    detector_HE4 = DetectorBooleanField(Method("PIXE"), Detector("HE4"))
    detector_HPGe20 = DetectorBooleanField(Method("PIGE"), Detector("HPGe-20"))
    detector_HPGe70 = DetectorBooleanField(Method("PIGE"), Detector("HPGe-70"))
    detector_HPGe70N = DetectorBooleanField(Method("PIGE"), Detector("HPGe-70-N"))
    detector_IBIL_QE65000 = DetectorBooleanField(Method("IBIL"), Detector("QE65000"))
    detector_IBIL_other = DetectorCharField(Method("IBIL"), Detector(OTHER_VALUE))
    detector_FORS_QE65000 = DetectorBooleanField(Method("FORS"), Detector("QE65000"))
    detector_FORS_other = DetectorCharField(Method("FORS"), Detector(OTHER_VALUE))
    detector_PIPS130 = DetectorBooleanField(Method("RBS"), Detector("PIPS - 130°"))
    detector_PIPS150 = DetectorBooleanField(Method("RBS"), Detector("PIPS - 150°"))
    detector_ERDA = DetectorCharField(Method("ERDA"), Detector(OTHER_VALUE))
    detector_NRA = DetectorCharField(Method("NRA"), Detector(OTHER_VALUE))

    HE_FILTERS = [
        Filter("100 µm Be"),
        Filter("100 µm Mylar"),
        Filter("200 µm Mylar"),
        Filter("50 µm Al"),
        Filter("100 µm Al"),
        Filter("150 µm Al"),
        Filter("200 µm Al"),
        Filter("13 µm Cr + 50 µm Al"),
        Filter("50 µm Cu"),
        Filter("75 µm Cu"),
        Filter(OTHER_VALUE),
    ]
    filters_for_detector_LE0 = FiltersCharField(
        Method("PIXE"), Detector("LE0"), [Filter("Helium"), Filter("Air")]
    )
    filters_for_detector_HE1 = FiltersCharField(
        Method("PIXE"), Detector("HE1"), HE_FILTERS
    )
    filters_for_detector_HE2 = FiltersCharField(
        Method("PIXE"), Detector("HE2"), HE_FILTERS
    )
    filters_for_detector_HE3 = FiltersCharField(
        Method("PIXE"), Detector("HE3"), HE_FILTERS
    )
    filters_for_detector_HE4 = FiltersCharField(
        Method("PIXE"), Detector("HE4"), HE_FILTERS
    )

    @classmethod
    def get_method_fields(cls) -> list[MethodBooleanField]:
        return [f for f in cls._meta.get_fields() if isinstance(f, MethodBooleanField)]

    @classmethod
    def get_method_field(cls, method: Method) -> MethodBooleanField:
        return next(f for f in cls.get_method_fields() if f.method == method)

    @classmethod
    def get_detector_fields(
        cls,
    ) -> list[Union[DetectorBooleanField, DetectorCharField]]:
        return [
            f
            for f in cls._meta.get_fields()
            if isinstance(f, (DetectorBooleanField, DetectorCharField))
        ]

    @classmethod
    def get_detector_field(
        cls, method: Method, detector: Detector
    ) -> Union[DetectorBooleanField, DetectorCharField]:
        return next(
            f
            for f in cls.get_detector_fields()
            if (f.method, f.detector) == (method, detector)
        )

    @classmethod
    def get_filters_fields(cls) -> list[FiltersCharField]:
        return [f for f in cls._meta.get_fields() if isinstance(f, FiltersCharField)]

    @classmethod
    def get_filters_field(
        cls, method: Method, detector: Detector
    ) -> Optional[FiltersCharField]:
        try:
            return next(
                f
                for f in cls.get_filters_fields()
                if (f.method, f.detector) == (method, detector)
            )
        except StopIteration:
            return None

    @classmethod
    def get_method_detector_fields(
        cls,
    ) -> list[
        tuple[MethodBooleanField, Union[DetectorBooleanField, DetectorCharField]]
    ]:
        return [
            (cls.get_method_field(df.method), df) for df in cls.get_detector_fields()
        ]

    @classmethod
    def get_method_detector_filters_fields(
        cls,
    ) -> list[
        tuple[
            MethodBooleanField,
            Union[DetectorBooleanField, DetectorCharField],
            FiltersCharField,
        ]
    ]:
        return [
            (
                cls.get_method_field(f.method),
                cls.get_detector_field(f.method, f.detector),
                f,
            )
            for f in cls.get_filters_fields()
        ]
