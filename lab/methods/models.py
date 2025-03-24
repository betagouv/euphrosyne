from typing import Dict, List, Optional, Tuple, Type, Union
import importlib
import inspect

from django.db import models
from django.conf import settings
from django.utils.functional import cached_property

from .model_fields import (
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from .types import OTHER_VALUE, Detector, Filter, Method


class AnalysisMethod(models.Model):
    """Definition of an analysis method that can be used in experiments"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    field_name = models.CharField(max_length=100, unique=True, help_text="Name of the field in the MethodModel")
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DetectorType(models.Model):
    """Definition of a detector for a specific analysis method"""
    name = models.CharField(max_length=50)
    method = models.ForeignKey(AnalysisMethod, on_delete=models.CASCADE, related_name="detectors")
    field_name = models.CharField(max_length=100, unique=True, help_text="Name of the field in the MethodModel")
    is_other_field = models.BooleanField(default=False, help_text="Whether this is a free-text detector field")
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['method__name', 'name']
        unique_together = [['method', 'name']]
    
    def __str__(self):
        return f"{self.method.name} - {self.name}"


class FilterOption(models.Model):
    """A filter option that can be used with a detector"""
    name = models.CharField(max_length=100)
    detector = models.ForeignKey(DetectorType, on_delete=models.CASCADE, related_name="filter_options")
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['detector__method__name', 'detector__name', 'name']
        unique_together = [['detector', 'name']]
    
    def __str__(self):
        return f"{self.detector.method.name} - {self.detector.name} - {self.name}"


class FilterSet(models.Model):
    """A set of filters for a specific detector"""
    detector = models.OneToOneField(DetectorType, on_delete=models.CASCADE, related_name="filter_set")
    field_name = models.CharField(max_length=100, unique=True, help_text="Name of the field in the MethodModel")
    
    class Meta:
        ordering = ['detector__method__name', 'detector__name']
    
    def __str__(self):
        return f"Filters for {self.detector}"
    
    @property
    def filter_options(self):
        return self.detector.filter_options.filter(is_enabled=True)


class MethodConfiguration:
    """
    Dynamically builds a MethodModel class based on the configured methods, detectors, and filters.
    This avoids hardcoding the fields in the model class.
    """
    
    @classmethod
    def get_method_fields(cls) -> Dict[str, MethodBooleanField]:
        """Returns a dictionary of method field name to field instances"""
        fields = {}
        for method in AnalysisMethod.objects.filter(is_enabled=True):
            fields[method.field_name] = MethodBooleanField(Method(method.name))
        return fields
            
    @classmethod
    def get_detector_fields(cls) -> Dict[str, Union[DetectorBooleanField, DetectorCharField]]:
        """Returns a dictionary of detector field name to field instances"""
        fields = {}
        for detector in DetectorType.objects.filter(is_enabled=True, method__is_enabled=True):
            if detector.is_other_field:
                fields[detector.field_name] = DetectorCharField(
                    Method(detector.method.name), 
                    Detector(OTHER_VALUE if detector.is_other_field else detector.name)
                )
            else:
                fields[detector.field_name] = DetectorBooleanField(
                    Method(detector.method.name), 
                    Detector(detector.name)
                )
        return fields
    
    @classmethod
    def get_filter_fields(cls) -> Dict[str, FiltersCharField]:
        """Returns a dictionary of filter field name to field instances"""
        fields = {}
        for filter_set in FilterSet.objects.filter(detector__is_enabled=True, detector__method__is_enabled=True):
            filter_options = list(filter_set.filter_options.all())
            if filter_options:
                filter_values = [Filter(option.name) for option in filter_options]
                # Always add an "other" option
                if not any(f.value == OTHER_VALUE for f in filter_values):
                    filter_values.append(Filter(OTHER_VALUE))
                
                fields[filter_set.field_name] = FiltersCharField(
                    Method(filter_set.detector.method.name),
                    Detector(filter_set.detector.name),
                    filter_values
                )
        return fields


class MethodModel(models.Model):
    """
    Abstract base model for models that need to track methods, detectors, and filters.
    The actual fields are created dynamically based on the configured methods, detectors, and filters.
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


# Function to build a model dynamically with fields from the configuration
def build_dynamic_method_model() -> Type[MethodModel]:
    """
    Builds a dynamic MethodModel with fields from the configuration.
    """
    model_fields = {}
    
    # Add method fields
    model_fields.update(MethodConfiguration.get_method_fields())
    
    # Add detector fields
    model_fields.update(MethodConfiguration.get_detector_fields())
    
    # Add filter fields
    model_fields.update(MethodConfiguration.get_filter_fields())
    
    # Create a new class that inherits from MethodModel
    return type(
        'DynamicMethodModel', 
        (MethodModel,), 
        {
            **model_fields,
            '__module__': 'lab.methods.models',
            'Meta': type('Meta', (), {'abstract': True})
        }
    )


# This is the model that should be used in your applications
# You'll need to migrate your data and update references to use this model
class ConfigurableMethodModel(MethodModel):
    """
    A MethodModel with fields created dynamically based on the configured methods, detectors, and filters.
    
    This abstract model is designed to be extended by concrete models like Run.
    The actual fields are added during migration based on the database configuration.
    
    For migrations, the fields are defined in the migration file using
    the dynamic_model.get_dynamic_fields_for_migration() function.
    
    At runtime, the fields are loaded from the database configuration when
    the model class is loaded. This allows for fields to be added or removed
    without requiring a new migration.
    """
    class Meta:
        abstract = True
    
    # Fields are added dynamically during migrations
    # See dynamic_model.py for implementation details
    
    @classmethod
    def _get_dynamic_fields(cls):
        """Returns a dictionary of field name to field instance for all dynamic fields."""
        all_fields = {}
        all_fields.update(MethodConfiguration.get_method_fields())
        all_fields.update(MethodConfiguration.get_detector_fields())
        all_fields.update(MethodConfiguration.get_filter_fields())
        return all_fields
    
    @classmethod
    def add_to_class(cls, name, value):
        """
        Hook for adding dynamic fields to model classes.
        
        This method is called by Django's ModelBase metaclass when the model is being defined.
        We override it to add our dynamic fields from the database configuration.
        """
        if name == '_meta':
            # Before the _meta object is created, add our dynamic fields
            dynamic_fields = cls._get_dynamic_fields()
            for field_name, field in dynamic_fields.items():
                # Skip if the field already exists (e.g., from migration)
                if hasattr(cls, field_name):
                    continue
                
                # Add the field to the class
                setattr(cls, field_name, field)
                
        # Call the parent class method to continue normal processing
        super().add_to_class(name, value)


# Example of New Aglae configuration for backward compatibility
def create_default_new_aglae_configuration():
    """
    Creates the default New Aglae configuration when the app is first installed.
    This ensures backward compatibility with existing code.
    """
    # Define methods
    pixe, _ = AnalysisMethod.objects.get_or_create(
        name="PIXE", 
        field_name="method_PIXE",
        defaults={"description": "Particle-Induced X-ray Emission"}
    )
    pige, _ = AnalysisMethod.objects.get_or_create(
        name="PIGE", 
        field_name="method_PIGE",
        defaults={"description": "Particle-Induced Gamma-ray Emission"}
    )
    ibil, _ = AnalysisMethod.objects.get_or_create(
        name="IBIL", 
        field_name="method_IBIL",
        defaults={"description": "Ion Beam Induced Luminescence"}
    )
    fors, _ = AnalysisMethod.objects.get_or_create(
        name="FORS", 
        field_name="method_FORS",
        defaults={"description": "Fiber Optics Reflectance Spectroscopy"}
    )
    rbs, _ = AnalysisMethod.objects.get_or_create(
        name="RBS", 
        field_name="method_RBS",
        defaults={"description": "Rutherford Backscattering Spectrometry"}
    )
    erda, _ = AnalysisMethod.objects.get_or_create(
        name="ERDA", 
        field_name="method_ERDA",
        defaults={"description": "Elastic Recoil Detection Analysis"}
    )
    nra, _ = AnalysisMethod.objects.get_or_create(
        name="NRA", 
        field_name="method_NRA",
        defaults={"description": "Nuclear Reaction Analysis"}
    )
    
    # Define detectors for PIXE
    le0, _ = DetectorType.objects.get_or_create(
        method=pixe, 
        name="LE0", 
        field_name="detector_LE0",
        defaults={"is_other_field": False}
    )
    he1, _ = DetectorType.objects.get_or_create(
        method=pixe, 
        name="HE1", 
        field_name="detector_HE1",
        defaults={"is_other_field": False}
    )
    he2, _ = DetectorType.objects.get_or_create(
        method=pixe, 
        name="HE2", 
        field_name="detector_HE2",
        defaults={"is_other_field": False}
    )
    he3, _ = DetectorType.objects.get_or_create(
        method=pixe, 
        name="HE3", 
        field_name="detector_HE3",
        defaults={"is_other_field": False}
    )
    he4, _ = DetectorType.objects.get_or_create(
        method=pixe, 
        name="HE4", 
        field_name="detector_HE4",
        defaults={"is_other_field": False}
    )
    
    # Define detectors for PIGE
    hpge20, _ = DetectorType.objects.get_or_create(
        method=pige, 
        name="HPGe-20", 
        field_name="detector_HPGe20",
        defaults={"is_other_field": False}
    )
    hpge70, _ = DetectorType.objects.get_or_create(
        method=pige, 
        name="HPGe-70", 
        field_name="detector_HPGe70",
        defaults={"is_other_field": False}
    )
    hpge70n, _ = DetectorType.objects.get_or_create(
        method=pige, 
        name="HPGe-70-N", 
        field_name="detector_HPGe70N",
        defaults={"is_other_field": False}
    )
    
    # Define detectors for IBIL
    ibil_qe65000, _ = DetectorType.objects.get_or_create(
        method=ibil, 
        name="QE65000", 
        field_name="detector_IBIL_QE65000",
        defaults={"is_other_field": False}
    )
    ibil_other, _ = DetectorType.objects.get_or_create(
        method=ibil, 
        name="Other", 
        field_name="detector_IBIL_other",
        defaults={"is_other_field": True}
    )
    
    # Define detectors for FORS
    fors_qe65000, _ = DetectorType.objects.get_or_create(
        method=fors, 
        name="QE65000", 
        field_name="detector_FORS_QE65000",
        defaults={"is_other_field": False}
    )
    fors_other, _ = DetectorType.objects.get_or_create(
        method=fors, 
        name="Other", 
        field_name="detector_FORS_other",
        defaults={"is_other_field": True}
    )
    
    # Define detectors for RBS
    pips130, _ = DetectorType.objects.get_or_create(
        method=rbs, 
        name="PIPS - 130°", 
        field_name="detector_PIPS130",
        defaults={"is_other_field": False}
    )
    pips150, _ = DetectorType.objects.get_or_create(
        method=rbs, 
        name="PIPS - 150°", 
        field_name="detector_PIPS150",
        defaults={"is_other_field": False}
    )
    
    # Define detectors for ERDA and NRA
    erda_other, _ = DetectorType.objects.get_or_create(
        method=erda, 
        name="Other", 
        field_name="detector_ERDA",
        defaults={"is_other_field": True}
    )
    nra_other, _ = DetectorType.objects.get_or_create(
        method=nra, 
        name="Other", 
        field_name="detector_NRA",
        defaults={"is_other_field": True}
    )
    
    # Define filter sets
    le0_filters, _ = FilterSet.objects.get_or_create(
        detector=le0,
        field_name="filters_for_detector_LE0"
    )
    he1_filters, _ = FilterSet.objects.get_or_create(
        detector=he1,
        field_name="filters_for_detector_HE1"
    )
    he2_filters, _ = FilterSet.objects.get_or_create(
        detector=he2,
        field_name="filters_for_detector_HE2"
    )
    he3_filters, _ = FilterSet.objects.get_or_create(
        detector=he3,
        field_name="filters_for_detector_HE3"
    )
    he4_filters, _ = FilterSet.objects.get_or_create(
        detector=he4,
        field_name="filters_for_detector_HE4"
    )
    
    # Define filter options for LE0
    FilterOption.objects.get_or_create(detector=le0, name="Helium")
    FilterOption.objects.get_or_create(detector=le0, name="Air")
    
    # Define HE filter options for all HE detectors
    he_filters = [
        "100 µm Be",
        "100 µm Mylar",
        "200 µm Mylar",
        "50 µm Al",
        "100 µm Al",
        "150 µm Al",
        "200 µm Al",
        "13 µm Cr + 50 µm Al",
        "50 µm Cu",
        "75 µm Cu",
        "25µm Co"
    ]
    
    for detector in [he1, he2, he3, he4]:
        for filter_name in he_filters:
            FilterOption.objects.get_or_create(detector=detector, name=filter_name)
