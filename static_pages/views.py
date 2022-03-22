from functools import wraps
from pathlib import Path

from django.contrib.admin import site
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from markdown import markdown


class StaticPageResponse(TemplateResponse):
    def __init__(self, request: HttpRequest, title: str, content: str):
        template = "static_pages/base.html"
        super().__init__(
            request,
            template,
            context={
                **site.each_context(request),
                "is_nav_sidebar_enabled": request.user.is_authenticated,
                "content": content,
                "subtitle": title,
            },
        )


def static_page(page_file_markdown):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            with open(page_file_markdown, "r", encoding="utf-8") as md_page:
                html = markdown(md_page.read())
            return view_func(request, html, *args, **kwargs)

        return _wrapped_view

    return decorator


@static_page(Path(__file__).resolve().parent / "pages/cgu.md")
def cgu_view(request, html):
    return StaticPageResponse(request, _("End-user license agreement"), html)


@static_page(Path(__file__).resolve().parent / "pages/legal_notice.md")
def legal_notice_view(request, html):
    return StaticPageResponse(request, _("Legal notice"), html)


@static_page(Path(__file__).resolve().parent / "pages/personal_data.md")
def personal_data_view(request, html):
    return StaticPageResponse(request, _("Personal data and cookies"), html)
