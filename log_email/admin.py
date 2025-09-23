from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import EmailLog, EmailLogQuerySet
from .providers import get_email_provider


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("subject", "to", "status", "date")
    list_display_links = None
    actions_on_top = False

    def get_queryset(self, request):
        provider = get_email_provider()
        msgs = provider.list_messages(limit=200)  # fetch more if you want
        objs = [EmailLog(**m) for m in msgs]
        return EmailLogQuerySet(EmailLog, objs)

    def changelist_view(self, request, extra_context: dict | None = None):
        extra_context = extra_context or {}
        extra_context["title"] = _("Latest sent emails")
        return super().changelist_view(request, extra_context)

    def get_changelist_instance(self, request):
        # cl = super().get_changelist_instance(request)
        ChangeList = self.get_changelist(request)
        list_filter = []
        search_fields = []
        list_select_related = False
        sortable_by = []
        cl = ChangeList(
            request,
            self.model,
            self.list_display,
            self.get_list_display_links(request, self.list_display),
            list_filter,
            self.date_hierarchy,
            search_fields,
            list_select_related,
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            sortable_by,
            self.search_help_text,
        )
        cl.queryset = self.get_queryset(request)
        return cl
