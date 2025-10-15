import json
from typing import Any

from django.contrib.admin import site
from django.contrib.admin.options import IS_POPUP_VAR
from django.forms import ModelForm
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView

from shared.view_mixins import StaffUserRequiredMixin

from . import forms


def object_import_view_factory(form_class: type[forms.ObjectGroupImportBaseForm]):
    class ObjectImportView(StaffUserRequiredMixin, CreateView):
        template_name = "admin/object_import_provider.html"

        form_class: type[forms.ObjectGroupImportBaseForm]

        def __init__(self, **kwargs):
            self.form_class = form_class
            super().__init__(**kwargs)

        def form_valid(self, form: ModelForm):
            if IS_POPUP_VAR in self.request.POST:
                # pylint: disable=attribute-defined-outside-init
                external_object_reference = form.save(commit=not form.instance.id)
                self.object = external_object_reference.object_group
                run_id = self.request.GET.get("run")
                if run_id:
                    # At last, check if this object is not already in the run
                    if self.object.runs.filter(id=run_id).exists():
                        form.add_error(
                            getattr(form, "provider_object_id", None),
                            _("This object has already been added to the run."),
                        )
                        return self.form_invalid(form)
                    self.object.runs.add(run_id)
                popup_response_data = json.dumps(
                    {
                        "action": "add",
                        "obj": str(self.object),
                        "value": str(
                            self.object.serializable_value(self.object._meta.pk.attname)
                        ),
                        "objectgroup_run_run_ids": list(
                            self.object.runs.through.objects.filter(
                                objectgroup=self.object.id
                            ).values_list("id", "run_id")
                        ),
                    }
                )
                return TemplateResponse(
                    self.request,
                    "admin/lab/objectgroup/popup_response.html",
                    {
                        "popup_response_data": popup_response_data,
                    },
                )

            return super().form_valid(form)

        def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
            provider_name = self.form_class().provider_name
            return {
                **super().get_context_data(**kwargs),
                **site.each_context(self.request),
                "title": _("%s import") % provider_name,
                "is_popup": IS_POPUP_VAR in self.request.GET,
                "is_popup_var": IS_POPUP_VAR,
                "provider_name": provider_name,
            }

    return ObjectImportView


ObjectImportErosView = object_import_view_factory(forms.ObjectGroupImportErosForm)

ObjectImportPOPView = object_import_view_factory(forms.ObjectGroupImportPOPForm)
