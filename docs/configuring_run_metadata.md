# Configuring Run Metadata

This guide explains how to customize lab-specific run metadata fields and run detail forms.

## Overview

Run metadata fields (for example: particle type, energy, beamline) are defined in a
lab-specific metadata model and mixed into the core `Run` model at runtime.

## How Run Metadata Configuration Works

1. **Core Infrastructure**: `lab.runs.metadata.RunMetadataModel` provides the base API
2. **Implementation**: `euphrosyne.runs.EuphrosyneRunMetadataModel` defines lab fields
3. **Configuration**: `RUN_METADATA_MODEL_CLASS` selects the metadata model
4. **Integration**: `lab.runs.models.Run` inherits the configured metadata model

## Customizing Run Metadata for Your Deployment

### 1. Edit the Run Metadata Model

Update `euphrosyne/runs/models.py` to match your laboratory requirements:

```python
class EuphrosyneRunMetadataModel(RunMetadataModel):
    class SampleType(models.TextChoices):
        ORGANIC = "Organic", _("Organic")
        INORGANIC = "Inorganic", _("Inorganic")

    sample_type = models.CharField(
        _("Sample type"), max_length=50, choices=SampleType.choices, blank=True
    )

    @classmethod
    def get_experimental_condition_fieldset_fields(cls):
        return ["sample_type"]
```

### 2. Update Settings

Ensure settings point to your metadata model:

```python
RUN_METADATA_MODEL_CLASS = "euphrosyne.runs.models.EuphrosyneRunMetadataModel"
```

### 3. Generate and Apply Migrations

Because these fields live on `lab.Run`, migrations are generated in the `lab` app:

```bash
python manage.py makemigrations lab
python manage.py migrate
```

## Customizing Run Detail Forms

Aglae-specific run detail forms live in `euphrosyne/runs/forms.py`. They can add
custom behavior (for example, controlled datalists for energy levels).

Configure which forms to use via settings:

```python
RUN_DETAILS_FORM_CLASS = "euphrosyne.runs.forms.AglaeRunDetailsForm"
RUN_DETAILS_ADMIN_FORM_CLASS = "euphrosyne.runs.forms.AglaeRunDetailsAdminForm"
```

## Troubleshooting

### Experimental Fields Missing in Admin

- Confirm `RUN_METADATA_MODEL_CLASS` points to the correct model
- Check `get_experimental_condition_fieldset_fields` is implemented
- Verify migrations have been applied
