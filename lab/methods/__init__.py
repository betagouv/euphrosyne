# Import types and fields (these don't depend on models)
from .form_fields import SelectWithFreeOther  # noqa: F401
from .model_fields import (  # noqa: F401
    DetectorBooleanField,
    DetectorCharField,
    FiltersCharField,
    MethodBooleanField,
)
from .types import OTHER_VALUE, Detector, Filter, Method  # noqa: F401

# Don't import models directly in __init__ to avoid circular dependencies
# Instead, we'll use explicit imports in files that need MethodModel
