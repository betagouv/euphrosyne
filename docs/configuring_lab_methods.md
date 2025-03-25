# Configuring Lab Methods

This guide explains how to configure method definitions for different laboratory deployments.

## Overview

The Euphrosyne application uses a flexible system for defining laboratory methods, detectors, and filters.
This allows different laboratories to customize the available methods without modifying the core application code.

All method definitions are contained in the `euphrosyne.methods` package, making migrations centralized in one place.

## How Method Configuration Works

1. **Core Infrastructure**: The `lab.methods` package provides the base infrastructure and types
2. **Implementation**: The `euphrosyne.methods` package contains the concrete implementation
3. **Configuration**: The `settings.py` file specifies which method model to use
4. **Integration**: The `Run` model dynamically loads the configured method model

## Customizing Methods for Your Deployment

To customize methods for your laboratory, follow these steps:

### 1. Edit the EuphrosyneMethodModel

The `EuphrosyneMethodModel` in `euphrosyne/methods/models.py` defines all available methods, detectors, and filters.
Modify this file to match your laboratory's requirements:

```python
# Example: Adding a new method
method_FTIR = MethodBooleanField(Method("FTIR"))

# Example: Adding detectors for a method
detector_FTIR_MCT = DetectorBooleanField(Method("FTIR"), Detector("MCT"))
detector_FTIR_DTGS = DetectorBooleanField(Method("FTIR"), Detector("DTGS"))
detector_FTIR_other = DetectorCharField(Method("FTIR"), Detector(OTHER_VALUE))

# Example: Adding filters for a detector
filters_for_detector_FTIR_MCT = FiltersCharField(
    Method("FTIR"),
    Detector("MCT"),
    [Filter("Diamond"), Filter("KBr"), Filter(OTHER_VALUE)]
)
```

### 2. Generate and Apply Migrations

After modifying the `EuphrosyneMethodModel`, generate and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

All migrations will be created in the `euphrosyne.methods` app, keeping your customizations separate from the core code.

### 3. Testing Your Configuration

To verify your method configuration:

1. Create a new run in the admin interface
2. Check that your methods appear in the methods section
3. Ensure the appropriate detectors show up when a method is selected
4. Confirm that filters appear for the relevant detectors

## Technical Details

### MethodModel Structure

- `MethodModel`: Abstract base class with helper methods
- `EuphrosyneMethodModel`: Laboratory-specific implementation with field definitions
- `MethodsConfiguration`: Concrete model that ensures migrations are created

### Field Types

- `MethodBooleanField`: Represents an analysis method (e.g., PIXE, PIGE)
- `DetectorBooleanField`: Boolean field for standard detectors
- `DetectorCharField`: Character field for custom/other detectors
- `FiltersCharField`: Character field for filters

### Important Notes

1. All migrations are generated in the `euphrosyne` app
2. The concrete implementation is loaded dynamically at runtime
3. Changes to method fields require database migrations
4. The `OTHER_VALUE` constant allows for custom values beyond predefined options

## Troubleshooting

### Missing Methods

If methods don't appear in the Run form:

- Check that your method model is correctly registered in settings
- Ensure migrations have been applied
- Verify that the method fields are defined with the correct types
