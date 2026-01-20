from django.db import models


class RunMetadataModel(models.Model):
    """
    Base abstract model that provides the infrastructure for run metadata-related fields.
    """

    class Meta:
        abstract = True

    @classmethod
    def get_experimental_condition_fieldset_fields(cls):
        """
        Returns the list of field names to be included in the 'Experimental Condition'
        fieldset in the run details form.
        """
        raise NotImplementedError()
