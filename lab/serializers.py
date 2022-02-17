import datetime
import locale

from django.utils import translation


def _default_converter(value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%d %B %Y %H:%S")
    return value


def convert_for_ui(
    request,
    obj,
    fieldnames: list[str],
):
    """Prepare for serialization of the object with pretty datetimes"""

    current_locale = (translation.to_locale(request.LANGUAGE_CODE), "UTF-8")
    try:
        locale.setlocale(locale.LC_ALL, locale=current_locale)
    except locale.Error:
        locale.setlocale(locale.LC_ALL, locale="en_US")

    def _serialize(field_name):
        field = getattr(obj, field_name)
        if isinstance(field, datetime.datetime):
            return field.strftime("%d %B %Y %H:%S")
        return str(field)

    return {
        fieldname: _default_converter(getattr(obj, fieldname))
        for fieldname in fieldnames
    }
