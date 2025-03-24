import json
import tempfile
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from lab.methods.models import (
    AnalysisMethod,
    ConfigurableMethodModel,
    DetectorType,
    FilterOption,
    FilterSet,
    build_dynamic_method_model,
)


class TestMethodModel(ConfigurableMethodModel):
    """Test model that inherits from ConfigurableMethodModel for testing."""
    class Meta:
        app_label = 'lab_methods'
        abstract = True


class DynamicModelTestCase(TestCase):
    """Test the dynamic model generation for ConfigurableMethodModel."""
    
    def setUp(self):
        """Create a sample configuration for testing."""
        # Create a method
        self.pixe = AnalysisMethod.objects.create(
            name="PIXE", 
            field_name="method_pixe",
            description="Particle-Induced X-ray Emission"
        )
        
        # Create detectors
        self.le0 = DetectorType.objects.create(
            method=self.pixe,
            name="LE0",
            field_name="detector_pixe_le0",
            is_other_field=False
        )
        
        self.custom = DetectorType.objects.create(
            method=self.pixe,
            name="Custom",
            field_name="detector_pixe_custom",
            is_other_field=True
        )
        
        # Create filter sets
        self.le0_filters = FilterSet.objects.create(
            detector=self.le0,
            field_name="filters_for_detector_le0"
        )
        
        # Create filter options
        FilterOption.objects.create(detector=self.le0, name="Helium")
        FilterOption.objects.create(detector=self.le0, name="Air")
    
    def test_dynamic_model_field_generation(self):
        """Test that dynamic fields are properly generated."""
        dynamic_model = build_dynamic_method_model()
        
        # Check method field
        self.assertTrue(hasattr(dynamic_model, "method_pixe"))
        
        # Check detector fields
        self.assertTrue(hasattr(dynamic_model, "detector_pixe_le0"))
        self.assertTrue(hasattr(dynamic_model, "detector_pixe_custom"))
        
        # Check filter field
        self.assertTrue(hasattr(dynamic_model, "filters_for_detector_le0"))
        
        # Check that fields are of the correct type
        from lab.methods.model_fields import (
            MethodBooleanField, 
            DetectorBooleanField, 
            DetectorCharField,
            FiltersCharField
        )
        
        self.assertIsInstance(dynamic_model.method_pixe.field, MethodBooleanField)
        self.assertIsInstance(dynamic_model.detector_pixe_le0.field, DetectorBooleanField)
        self.assertIsInstance(dynamic_model.detector_pixe_custom.field, DetectorCharField)
        self.assertIsInstance(dynamic_model.filters_for_detector_le0.field, FiltersCharField)
    
    def test_default_configuration_command(self):
        """Test the management command with --default option."""
        # Clear existing configuration
        AnalysisMethod.objects.all().delete()
        
        # Run the command
        call_command('init_method_configuration', default=True)
        
        # Check that default methods are created
        self.assertTrue(AnalysisMethod.objects.filter(name="PIXE").exists())
        self.assertTrue(AnalysisMethod.objects.filter(name="PIGE").exists())
        
        # Check that detectors are created
        self.assertTrue(DetectorType.objects.filter(name="LE0").exists())
        self.assertTrue(DetectorType.objects.filter(name="HE1").exists())
        
        # Check that filter sets are created
        pixe = AnalysisMethod.objects.get(name="PIXE")
        le0 = DetectorType.objects.get(method=pixe, name="LE0")
        self.assertTrue(FilterSet.objects.filter(detector=le0).exists())
        
        # Check that filter options are created
        self.assertTrue(FilterOption.objects.filter(detector=le0, name="Helium").exists())
        self.assertTrue(FilterOption.objects.filter(detector=le0, name="Air").exists())
    
    def test_json_configuration_command(self):
        """Test the management command with --from-json option."""
        # Clear existing configuration
        AnalysisMethod.objects.all().delete()
        
        # Create a temporary JSON file
        json_config = {
            "methods": [
                {
                    "name": "XRF",
                    "description": "X-ray Fluorescence",
                    "detectors": [
                        {
                            "name": "SDD",
                            "is_other_field": False,
                            "filters": ["No Filter", "Al Filter"]
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as tmp:
            json.dump(json_config, tmp)
            tmp.flush()
            
            # Run the command
            call_command('init_method_configuration', json_file=tmp.name)
        
        # Check that methods are created
        self.assertTrue(AnalysisMethod.objects.filter(name="XRF").exists())
        
        # Check that detectors are created
        xrf = AnalysisMethod.objects.get(name="XRF")
        self.assertTrue(DetectorType.objects.filter(method=xrf, name="SDD").exists())
        
        # Check that filter options are created
        sdd = DetectorType.objects.get(method=xrf, name="SDD")
        self.assertTrue(FilterOption.objects.filter(detector=sdd, name="No Filter").exists())
        self.assertTrue(FilterOption.objects.filter(detector=sdd, name="Al Filter").exists())