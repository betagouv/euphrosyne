from unittest import mock

from django.test import TestCase

from lab.measuring_points.models import MeasuringPoint
from lab.tests import factories as lab_factories


class MeasuringPointModelTestCase(TestCase):
    def test_is_meaningful__with_comments_only(self):
        """Test is_meaningful returns True when point has comments only"""
        point = MeasuringPoint(
            name="Test Point",
            comments="This is a test comment",
            object_group=None,
        )

        self.assertTrue(point.is_meaningful)

    def test_is_meaningful__with_object_group_only(self):
        """Test is_meaningful returns True when point has object_group only"""
        object_group = lab_factories.ObjectGroupFactory()
        point = MeasuringPoint(
            name="Test Point",
            comments="",
            object_group=object_group,
        )

        self.assertTrue(point.is_meaningful)

    def test_is_meaningful__with_standard_only(self):
        """Test is_meaningful returns True when point has standard only"""
        run = lab_factories.RunFactory()

        # Create an instance that will be saved to the DB so Django's
        # model relationships work properly
        with mock.patch.object(
            MeasuringPoint, "standard", new_callable=mock.PropertyMock
        ):
            point = MeasuringPoint.objects.create(
                name="Test Point",
                run=run,
                comments="",
                object_group=None,
            )
            self.assertTrue(point.is_meaningful)

    def test_is_meaningful__with_nothing(self):
        """Test is_meaningful returns False when point has no meaningful data"""
        run = lab_factories.RunFactory()

        # Create a real instance with no comments, no object_group, and no standard
        point = MeasuringPoint.objects.create(
            name="Test Point",
            run=run,
            comments="",
            object_group=None,
        )

        # Since we don't assign a standard, it should be False
        self.assertFalse(point.is_meaningful)

    def test_is_meaningful__with_whitespace_comments(self):
        """Test is_meaningful returns False when comments contain only whitespace"""
        point = MeasuringPoint(
            name="Test Point",
            comments="   \n\t   ",
            object_group=None,
        )

        self.assertFalse(point.is_meaningful)
