import pytest

from ...methods.dto import DetectorDTO, MethodDTO, method_model_to_dto
from .. import factories


@pytest.mark.django_db
def test_run_methods_repr():
    run = factories.RunFactory(
        method_PIXE=True,
        method_RBS=True,
        method_NRA=True,
        detector_LE0=True,
        detector_HE1=True,
        detector_PIPS130=True,
        detector_NRA="blabla",
        filters_for_detector_LE0="Helium",
        filters_for_detector_HE1="100 µm Be",
    )

    methods_repr = method_model_to_dto(run)

    assert methods_repr == [
        MethodDTO(
            name="PIXE",
            detectors=[
                DetectorDTO(name="LE0", filters=["Helium"]),
                DetectorDTO(name="HE1", filters=["100 µm Be"]),
            ],
        ),
        MethodDTO(
            name="RBS",
            detectors=[
                DetectorDTO(name="PIPS - 130°", filters=[]),
            ],
        ),
        MethodDTO(
            name="NRA",
            detectors=[
                DetectorDTO(name="blabla", filters=[]),
            ],
        ),
    ]
