import datetime

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import reverse, serializers, validators
from rest_framework.fields import empty

from euphro_auth.emails import send_invitation_email
from euphro_auth.models import User
from lab.emails import send_project_invitation_email
from lab.participations.models import Employer, Institution, Participation

from ..models import Project, Run
from ..objects.models import ExternalObjectReference, ObjectGroup, RunObjetGroupImage


class ProjectRunObjectGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectGroup
        fields = ("label", "id")


class ProjectRunSerializer(serializers.ModelSerializer):
    objects = ProjectRunObjectGroupSerializer(many=True, source="run_object_groups")
    methods_url = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = (
            "label",
            "particle_type",
            "energy_in_keV",
            "objects",
            "methods_url",
        )

    def get_methods_url(self, obj: Run):
        return reverse.reverse(
            "api:run-detail-methods", args=[obj.id], request=self.context["request"]
        )


class ProjectSerializer(serializers.ModelSerializer):
    runs = ProjectRunSerializer(many=True)

    class Meta:
        model = Project
        fields = ("name", "runs", "slug")


class UpcomingProjectSerializer(serializers.ModelSerializer):
    change_url = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    num_runs = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ("name", "start_date", "change_url", "status", "num_runs")

    def get_change_url(self, obj: Project):
        return reverse.reverse("admin:lab_project_change", args=[obj.id])

    def get_start_date(self, obj: Project):
        # Get start_date by ordering runs by start_date and filtering the
        # ones that are after now
        ordered_start_dates = [
            r.start_date
            for r in sorted(
                filter(
                    lambda r: r.start_date and r.start_date >= timezone.now(),
                    obj.runs.all(),
                ),
                key=lambda r: r.start_date or datetime.datetime.max,
            )
        ]
        if not ordered_start_dates:
            return None
        return ordered_start_dates[0]

    def get_num_runs(self, obj: Project):
        return obj.runs.count()

    def get_status(self, obj: Project):
        return {
            "label": obj.status.value[1],
            "class_name": obj.status.name.lower(),
        }


class RunMethodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = (
            "method_PIXE",
            "method_PIGE",
            "method_IBIL",
            "method_FORS",
            "method_RBS",
            "method_ERDA",
            "method_NRA",
            "detector_LE0",
            "detector_HE1",
            "detector_HE2",
            "detector_HE3",
            "detector_HE4",
            "detector_HPGe20",
            "detector_HPGe70",
            "detector_HPGe70N",
            "detector_IBIL_QE65000",
            "detector_IBIL_other",
            "detector_FORS_QE65000",
            "detector_FORS_other",
            "detector_PIPS130",
            "detector_PIPS150",
            "detector_ERDA",
            "detector_NRA",
            "filters_for_detector_LE0",
            "filters_for_detector_HE1",
            "filters_for_detector_HE2",
            "filters_for_detector_HE3",
            "filters_for_detector_HE4",
        )


class _RunObjectGroupExternalObjectReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalObjectReference
        fields = ("id", "provider_name", "provider_object_id")


class _RunObjectGroupObjectGroupSerializer(serializers.ModelSerializer):
    dating = serializers.SerializerMethodField()
    external_reference = _RunObjectGroupExternalObjectReferenceSerializer()

    class Meta:
        model = ObjectGroup
        fields = (
            "label",
            "id",
            "object_count",
            "dating",
            "materials",
            "c2rmf_id",  # deprecated
            "external_reference",
        )

    def get_dating(self, obj: ObjectGroup):
        return obj.dating_era.label if obj.dating_era else ""

    def get_c2rmf_id(self, obj: ObjectGroup):
        if (
            hasattr(obj, "external_reference")
            and obj.external_reference.provider_name == "eros"
        ):
            return obj.external_reference.provider_object_id
        return None


class RunObjectGroupSerializer(serializers.ModelSerializer):
    objectgroup = _RunObjectGroupObjectGroupSerializer()

    class Meta:
        model = Run.run_object_groups.through
        fields = ("id", "objectgroup")


class AvailableObjectGroupSerializer(_RunObjectGroupObjectGroupSerializer):
    pass


class RunObjectGroupCreateSerializer(serializers.ModelSerializer):
    objectgroup = serializers.PrimaryKeyRelatedField(queryset=ObjectGroup.objects.all())

    class Meta:
        model = Run.run_object_groups.through
        fields = ("objectgroup",)


class ObjectGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectGroup
        fields = (
            "id",
            "label",
        )
        read_only_fields = ("id",)


class RunObjectGroupImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunObjetGroupImage
        fields = ("id", "path", "transform")

        read_only_fields = ("id",)

    def validate_transform(self, value: dict | None):
        """
        Check that image has valid size.
        """
        if value is None:
            return value
        if ("width" in value and value["width"] == 0) and (
            "height" in value and value["height"] == 0
        ):
            raise serializers.ValidationError(
                "Image transform must have width and height set to a non-zero value"
            )
        return value


class GetObjectImageFromProviderResponseSerializer(serializers.Serializer):
    images = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    def create(self, validated_data):
        raise NotImplementedError("This serializer is read-only")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer is read-only")


class _EmployerParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ("email", "first_name", "last_name", "function")


class _UserParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("email", "id", "first_name", "last_name")
        read_only_fields = ("id", "first_name", "last_name")

    def build_standard_field(self, field_name, model_field):
        # We remove the UniqueValidator on email because we use get_or_create.
        field_class, field_kwargs = super().build_standard_field(
            field_name, model_field
        )
        if field_name == "email":
            field_kwargs["validators"] = list(
                filter(
                    lambda f: not isinstance(f, validators.UniqueValidator),
                    field_kwargs.get("validators", []),
                )
            )
        return field_class, field_kwargs


class _InstitutionParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ("id", "name", "ror_id", "country")

    def get_validators(self):
        # We remove the UniqueTogetherValidator on email because we use get_or_create.
        vals = super().get_validators()
        vals = list(
            filter(
                lambda x: not isinstance(x, validators.UniqueTogetherValidator), vals
            )
        )
        return vals


class ProjectUserUniqueValidator:
    requires_context = True

    def __call__(self, value, serializer_field):
        project = serializer_field.context.get("project")
        if not project:
            raise ValueError("ProjectUserUniqueValidator requires 'project' in context")
        user_email = value.get("email")
        if not user_email:
            raise ValueError(
                "ProjectUserUniqueValidator requires 'email' in the user data"
            )
        if (
            serializer_field.root.instance
            and serializer_field.root.instance.user.email == user_email
        ):
            # If the user email is the same
            # and we're in partial update mode, we can skip the check
            return
        if Participation.objects.filter(
            project=project,
            user__email=user_email,
        ).exists():
            raise serializers.ValidationError(
                _("This user is already a participant in the project.")
            )


class ParticipationSerializer(serializers.ModelSerializer):
    user = _UserParticipationSerializer(validators=[ProjectUserUniqueValidator()])
    institution = _InstitutionParticipationSerializer()

    class Meta:
        model = Participation
        fields = ("id", "user", "institution", "on_premises")
        # We set on_premises in the views, so make it read-only here
        read_only_fields = ("id", "on_premises")

    def create(self, validated_data):
        institution_data = validated_data.pop("institution")
        institution, _ = Institution.objects.get_or_create(
            name=institution_data["name"],
            ror_id=institution_data.get("ror_id"),
            country=institution_data.get("country"),
        )

        user_data = validated_data.pop("user")
        user = self._handle_user_data(user_data)

        instance = super().create(
            {**validated_data, "institution": institution, "user": user}
        )

        send_project_invitation_email(user.email, instance.project)

        return instance

    def update(self, instance, validated_data):
        institution_data = validated_data.pop("institution", None)
        if institution_data:
            institution, _ = Institution.objects.get_or_create(
                name=institution_data["name"],
                ror_id=institution_data.get("ror_id"),
                country=institution_data.get("country"),
            )
            validated_data["institution"] = institution
        return super().update(instance, validated_data)

    def _handle_user_data(self, user_data: dict) -> User:
        user, created = get_user_model().objects.get_or_create(email=user_data["email"])
        if created:
            send_invitation_email(user)
        return user


class OnPremisesParticipationSerializer(ParticipationSerializer):
    employer = _EmployerParticipationSerializer(required=False, allow_null=True)

    def __init__(self, instance=None, data=empty, **kwargs):
        self.Meta.fields = [*self.Meta.fields, "employer"]
        super().__init__(instance, data, **kwargs)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self._is_employer_form_exempt(attrs):
            return attrs
        if self._is_employer_data_missing(attrs):
            required_message = self.fields["employer"].error_messages.get(
                "required", _("This field is required.")
            )
            raise serializers.ValidationError({"employer": [required_message]})
        return attrs

    def create(self, validated_data):
        employer = None
        employer_data = validated_data.pop("employer", None)
        if employer_data:
            employer = Employer.objects.create(**employer_data)
        instance = super().create({**validated_data, "employer": employer})

        self._handle_user_change(instance)

        return instance

    def update(self, instance: Participation, validated_data: dict):
        user_data = validated_data.pop("user", None)
        user_has_changed = False
        if user_data:
            if instance.user.email != user_data.get("email", instance.user.email):
                user_has_changed = True
            user = self._handle_user_data(user_data)
            validated_data["user"] = user

        employer_data = validated_data.pop("employer", None)
        if (
            self._get_institution_ror_id(validated_data)
            in settings.PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS
            and instance.employer
        ):
            # If the institution changed to one that is exempt, remove employer
            instance.employer = None
        else:
            if employer_data:
                employer_instance = instance.employer
                if employer_instance:
                    for field, value in employer_data.items():
                        setattr(employer_instance, field, value)
                    employer_instance.save()
                else:
                    employer = Employer.objects.create(**employer_data)
                    instance.employer = employer
        instance = super().update(instance, validated_data)
        if user_has_changed:
            send_project_invitation_email(instance.user.email, instance.project)
            self._handle_user_change(instance)
        return instance

    def _is_employer_data_missing(self, attrs: dict) -> bool:
        if self.partial and "employer" not in attrs:
            return False
        if attrs.get("employer") is not None:
            return False
        if self.instance and self.instance.employer:
            return False
        return True

    def _is_employer_form_exempt(self, attrs: dict) -> bool:
        ror_id = self._get_institution_ror_id(attrs)
        if not ror_id:
            return False
        return ror_id in settings.PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS

    def _get_institution_ror_id(self, attrs: dict) -> str | None:
        institution_data = attrs.get("institution")
        if institution_data:
            ror_id = institution_data.get("ror_id")
            if ror_id:
                return ror_id
            if self.instance and self.instance.institution:
                return self.instance.institution.ror_id
            return None
        if self.instance and self.instance.institution:
            return self.instance.institution.ror_id
        return None

    def _handle_user_change(self, instance: Participation | None = None):
        if apps.is_installed("radiation_protection") and instance:
            # pylint: disable=import-outside-toplevel
            from radiation_protection.certification import (
                check_radio_protection_certification,
            )

            check_radio_protection_certification(
                instance.user,
            )
