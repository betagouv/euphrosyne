from typing import Optional, Union

from django.db import models

from .model_fields import (
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from .types import Detector, Method


class MethodModel(models.Model):
    """
    Base abstract model that provides the infrastructure for method-related fields.
    This model doesn't define any specific methods - those are defined in lab-specific
    implementation classes.
    """

    class Meta:
        abstract = True

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
