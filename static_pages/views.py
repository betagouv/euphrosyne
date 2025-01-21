from functools import wraps
from pathlib import Path

from django.contrib.admin import site
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import get_language, get_supported_language_variant
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


def _read_markdown_file(file: Path):
    with open(file, "r", encoding="utf-8") as md_page:
        return markdown(md_page.read())


def static_page(page_file_markdown):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            html = _read_markdown_file(page_file_markdown)
            return view_func(request, html, *args, **kwargs)

        return _wrapped_view

    return decorator


def i18n_static_page(folder_file_markdown: Path):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            locale = get_supported_language_variant(get_language())
            html = _read_markdown_file(folder_file_markdown / f"{locale}.md")
            return view_func(request, html, *args, **kwargs)

        return _wrapped_view

    return decorator


@i18n_static_page(Path(__file__).resolve().parent / "pages/cgu")
def cgu_view(request, html):
    return StaticPageResponse(request, _("End-user license agreement"), html)


@static_page(Path(__file__).resolve().parent / "pages/legal_notice.md")
def legal_notice_view(request, html):
    return StaticPageResponse(request, _("Legal notice"), html)


@static_page(Path(__file__).resolve().parent / "pages/personal_data.md")
def personal_data_view(request, html):
    return StaticPageResponse(request, _("Personal data and cookies"), html)


@static_page(Path(__file__).resolve().parent / "pages/accessibility_declaration.md")
def accessibility_declaration_view(request, html):
    return StaticPageResponse(request, _("Accessibility declaration"), html)


@static_page(
    Path(__file__).resolve().parent / "pages/accessibility_multiyear_schema.md"
)
def accessibility_multiyear_schema_view(request, html):
    return StaticPageResponse(request, _("Accessibility multi-year schema"), html)


@static_page(Path(__file__).resolve().parent / "pages/accessibility_map.md")
def accessibility_map_view(request, html):
    return StaticPageResponse(request, _("Site map"), html)
