from django.db import models


class ThesorusConceptModel(models.Model):
    """Abstract model for concept in thesauri."""

    OPENTHESO_THESO_ID: str | None = None

    concept_id = models.CharField(
        "Concept ID on Open Theso",
        max_length=255,
        null=True,
        blank=True,
    )
    label = models.CharField("Label", max_length=255)

    class Meta:
        abstract = True

        constraints = [
            models.UniqueConstraint(
                fields=["label", "concept_id"],
                name="%(class)s_thesorus_concept_unique_label_concept_id",
            ),
            models.UniqueConstraint(
                fields=["concept_id"],
                name="%(class)s_thesorus_concept_unique_concept_id",
            ),
        ]

    def __str__(self) -> str:
        return str(self.label)


class Period(ThesorusConceptModel):
    OPENTHESO_THESO_ID = "th287"


class Era(ThesorusConceptModel):
    OPENTHESO_THESO_ID = "th289"
