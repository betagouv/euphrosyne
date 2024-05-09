from django.core import checks
from django.db import connection, models


class ModelField(models.CharField):
    """Same as CharField but python object is a django.db.models.Model class."""

    _choice_not_found_error = (
        "Some model %s.%s choices saved in DB do not exist in the code. "
        "Did you rename or delete a model? Incorrect choices: %s"
    )

    def from_db_value(self, value, *args):
        """Converts the value as it's loaded from the database."""
        if value is None:
            return value
        return self._get_value_from_choices(value)

    def to_python(self, value):
        """Converts the value into the correct Python object."""
        if not isinstance(value, str):
            return value

        if value is None:
            return value

        return self._get_value_from_choices(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Ignore choice changes when generating migrations
        if "choices" in kwargs:
            del kwargs["choices"]
        if "default" in kwargs:
            del kwargs["default"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        """Convert class to string value to be saved in the DB."""
        return str(value)

    def _check_choices(self):
        """Checks if all choices saved in the database exist in the code."""
        if self.model._meta.db_table not in connection.introspection.table_names():
            return []  # Skip check if table does not exist yet
        model_names_from_choices = [str(choice[0][0]) for choice in self.choices]
        wrong_models = self.model.objects.exclude(type_of__in=model_names_from_choices)
        if wrong_models:
            wrong_choices = [
                choice
                for model in wrong_models
                for choice in getattr(model.choices)
                if choice[0][0] in model_names_from_choices
            ]
            formatted_wrong_choices = ", ".join(wrong_choices)
            return [
                checks.Error(
                    self._choice_not_found_error
                    % (self.model, self.attname, formatted_wrong_choices),
                )
            ]
        return []

    def _get_value_from_choices(self, value: str):
        """
        Retrieves the corresponding choice for the given value.
        If choice is invalid, it raises a ValueError.
        """
        try:
            return next(choice for choice in self.choices if str(choice[0][0]) == value)
        except StopIteration as error:
            raise ValueError(
                self._choice_not_found_error % (self.model, self.attname, value)
            ) from error
