from euphrosyne.methods.models import EuphrosyneMethodModel


class MethodsConfiguration(EuphrosyneMethodModel):
    """
    Concrete model that exists solely to generate migrations for the method fields.
    This model will never be used directly but ensures migrations are created
    in the euphrosyne app instead of the lab app.
    """

    class Meta:
        app_label = "euphrosyne"
        # We need this to be managed for migrations to be created
        managed = True
        db_table = "euphrosyne_methods_configuration"
        verbose_name = "Methods Configuration"
        verbose_name_plural = "Methods Configurations"
