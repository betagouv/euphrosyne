from lab.controlled_datalist import controlled_datalist_form
from lab.runs.forms import RunDetailsAdminForm, RunDetailsForm

from .models import EuphrosyneRunMetadataModel

RECOMMENDED_ENERGY_LEVELS = {
    EuphrosyneRunMetadataModel.ParticleType.PROTON: [
        1000,
        1500,
        2000,
        2500,
        3000,
        3500,
        3800,
        4000,
    ],
    EuphrosyneRunMetadataModel.ParticleType.ALPHA: [3000, 4000, 5000, 6000],
    EuphrosyneRunMetadataModel.ParticleType.DEUTON: [1000, 1500, 2000],
}


def _get_energy_levels_choices(
    particle_type: EuphrosyneRunMetadataModel.ParticleType,
) -> list[tuple[int, int]]:
    return [(level, level) for level in RECOMMENDED_ENERGY_LEVELS[particle_type]]


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in EuphrosyneRunMetadataModel.ParticleType
    },
)
class AglaeRunDetailsForm(RunDetailsForm):
    pass


@controlled_datalist_form(
    controller_field_name="particle_type",
    controlled_field_name="energy_in_keV",
    choices={
        particle_type: _get_energy_levels_choices(particle_type)
        for particle_type in EuphrosyneRunMetadataModel.ParticleType
    },
)
class AglaeRunDetailsAdminForm(RunDetailsAdminForm):
    pass
