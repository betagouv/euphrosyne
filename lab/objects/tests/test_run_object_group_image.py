from django.test import SimpleTestCase

from ..models import RunObjetGroupImage


class TestRunObjectGroupImage(SimpleTestCase):
    def test_run_object_group_image_file_name(self):

        assert RunObjetGroupImage(path="C2RMF77463/KOA68").file_name == "KOA68.tiff"
        assert RunObjetGroupImage(path="FZ77463/KOA68").file_name == "KOA68.tiff"
        assert RunObjetGroupImage(path="FBLABLA/KOA68").file_name == "KOA68.tiff"
        assert (
            RunObjetGroupImage(
                path="/project-test/images/object-groups/163/abcdefghif.jpg"
            ).file_name
            == "abcdefghif.jpg"
        )
