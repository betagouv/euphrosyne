from django.db import models
from django.utils.translation import gettext_lazy as _

from .types import OTHER_VALUE, Detector, Filter, Method


class MethodBooleanField(models.BooleanField):
    method: Method

    def __init__(self, method: Method):
        self.method = method
        super().__init__(
            verbose_name=method,
            help_text=_("{} analysis technique").format(method),
            default=False,
        )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["verbose_name"]
        del kwargs["help_text"]
        del kwargs["default"]
        args = [self.method, *args]
        return name, path, args, kwargs


class DetectorFieldMixin:
    method: Method
    detector: Detector

    def __init__(
        self: models.Field, method: Method, detector: Detector, *args, **kwargs
    ):
        self.method = method
        self.detector = detector
        super().__init__(  # type: ignore
            verbose_name=_("other detector") if detector == OTHER_VALUE else detector,
            help_text=_("{} / {} detector").format(
                method,
                detector,
            ),
            *args,
            **kwargs
        )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["verbose_name"]
        del kwargs["help_text"]
        args = [self.method, self.detector, *args]
        return name, path, args, kwargs


class DetectorBooleanField(DetectorFieldMixin, models.BooleanField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, default=False)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["default"]
        return name, path, args, kwargs


class DetectorCharField(DetectorFieldMixin, models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_length=45, default="", blank=True)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["default"]
        del kwargs["blank"]
        return name, path, args, kwargs


class FiltersCharField(models.CharField):
    """CharField without explicit choices
    Choice management is done by the Form.
    """

    method: Method
    detector: Detector
    filters: list[Filter]

    def __init__(
        self, method: Method, detector: Detector, filters: list[Filter], *args, **kwargs
    ):
        if not filters:
            # pylint: disable=broad-exception-raised
            raise Exception("FilterCharField requires some filters")
        self.method = method
        self.detector = detector
        self.filters = filters
        super().__init__(  # type: ignore
            verbose_name=_("{} filters").format(detector),
            help_text=_("{} / {} filters choice").format(method, detector),
            max_length=45,
            default="",
            blank=True,
        )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.method, self.detector, self.filters, *args]
        del kwargs["verbose_name"]
        del kwargs["help_text"]
        del kwargs["max_length"]
        del kwargs["default"]
        del kwargs["blank"]
        return name, path, args, kwargs
