from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from ..admin import ObjectInline
from ..models import ObjectGroup


def test_get_formset_sets_min_num_on_post():
    objectgroup = ObjectGroup(id=1)
    inline = ObjectInline(ObjectGroup, admin_site=AdminSite())
    data = {
        "object_set-TOTAL_FORMS": "18",
    }
    request = RequestFactory().post(
        reverse("admin:lab_objectgroup_change", args=[objectgroup.id]), data=data
    )

    assert inline.get_min_num(request, objectgroup) == 18


def test_get_formset_ignores_min_num_on_get():
    objectgroup = ObjectGroup(id=1)
    inline = ObjectInline(ObjectGroup, admin_site=AdminSite())
    request = RequestFactory().get(
        reverse("admin:lab_objectgroup_change", args=[objectgroup.id])
    )

    assert not inline.get_min_num(request, objectgroup)
