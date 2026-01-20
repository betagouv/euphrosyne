from django.db import models


class RunMetadataModel(models.Model):
    """
    Base abstract model that provides the infrastructure for run medata-related fields.
    """

    class Meta:
        abstract = True

    @classmethod
    def get_experimental_condition_fieldset_fields(cls):
        raise NotImplementedError()
