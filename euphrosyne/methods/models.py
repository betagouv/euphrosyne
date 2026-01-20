from django.db import models
from django.utils.translation import gettext_lazy as _

from lab.methods.model_fields import (
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from lab.methods.models import MethodModel
from lab.methods.types import OTHER_VALUE, Detector, Filter, Method


class EuphrosyneMethodModel(MethodModel):
    """
    Concrete implementation of MethodModel for the AGLAE laboratory.
    This model defines the actual database fields for methods, detectors, and filters.
    All migrations will be generated in the euphrosyne app rather than in the lab app.
    """

    class Meta:
        # Explicitly set app_label to ensure migrations go to euphrosyne
        app_label = "euphrosyne"
        abstract = True

    class ParticleType(models.TextChoices):
        PROTON = "Proton", _("Proton")
        ALPHA = "Alpha particle", _("Alpha particle")
        DEUTON = "Deuton", _("Deuton")

    class Beamline(models.TextChoices):
        MICROBEAM = "Microbeam", _("Microbeam")

    particle_type = models.CharField(
        _("Particle type"), max_length=45, choices=ParticleType.choices, blank=True
    )
    energy_in_keV = models.IntegerField(
        _("Energy level (in keV)"), null=True, blank=True
    )
    beamline = models.CharField(
        _("Beamline"),
        max_length=45,
        choices=Beamline.choices,
        default=Beamline.MICROBEAM,
    )

    # Methods available at AGLAE
    method_PIXE = MethodBooleanField(Method("PIXE"))
    method_PIGE = MethodBooleanField(Method("PIGE"))
    method_IBIL = MethodBooleanField(Method("IBIL"))
    method_FORS = MethodBooleanField(Method("FORS"))
    method_RBS = MethodBooleanField(Method("RBS"))
    method_ERDA = MethodBooleanField(Method("ERDA"))
    method_NRA = MethodBooleanField(Method("NRA"))

    # Detectors for each method
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

    # Filters for each detector
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
        Filter("25µm Co"),
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
