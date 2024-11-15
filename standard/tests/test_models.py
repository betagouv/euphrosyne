from django.forms import ValidationError
import pytest
from ..models import Standard, MeasuringPointStandard
from lab.measuring_points.models import MeasuringPoint
from lab.tests import factories as lab_factories


@pytest.mark.django_db
def test_measuring_point_standard_clean_prevent_object_group_and_standard():
    standard = Standard.objects.create(label="Standard")

    og_measuring_point = MeasuringPoint.objects.create(
        run=lab_factories.RunFactory(),
        object_group=lab_factories.ObjectGroupFactory(),
    )

    with pytest.raises(ValidationError):
        MeasuringPointStandard(
            standard=standard, measuring_point=og_measuring_point
        ).clean()

    other_measuring_point = MeasuringPoint.objects.create(
        run=lab_factories.RunFactory(),
    )
    MeasuringPointStandard(
        standard=standard, measuring_point=other_measuring_point
    ).clean()
