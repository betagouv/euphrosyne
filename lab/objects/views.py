import json
from typing import Any

from django.contrib.admin import site
from django.contrib.admin.options import IS_POPUP_VAR
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView

from shared.view_mixins import StaffUserRequiredMixin

from . import forms


class ObjectImportC2RMFView(StaffUserRequiredMixin, CreateView):
    template_name = "admin/object_import_c2rmf.html"
    form_class = forms.ObjectGroupImportC2RMFForm

    def form_valid(self, form: forms.ObjectGroupImportC2RMFForm):
        if IS_POPUP_VAR in self.request.POST:
            # pylint: disable=attribute-defined-outside-init
            self.object = form.save(commit=not form.instance.id)
            run_id = self.request.GET.get("run")
            if run_id:
                # At last, check if this object is not already in the run
                if self.object.runs.filter(id=run_id).exists():
                    form.add_error(
                        "c2rmf_id", _("This object has already been added to the run.")
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
        return {
            **super().get_context_data(**kwargs),
            **site.each_context(self.request),
            "title": "Add object",
            "subtitle": _("EROS import"),
            "is_popup": IS_POPUP_VAR in self.request.GET,
            "is_popup_var": IS_POPUP_VAR,
        }
