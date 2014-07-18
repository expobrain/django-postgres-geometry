from django.test import TestCase, SimpleTestCase
from django.utils import six
from django.db import models, connection
from django.core.exceptions import FieldError
from mock import Mock

from .fields import (Point, Circle, PointField, SegmentPathField, PolygonField,
                     SegmentField, BoxField, CircleField)


class TestModel(models.Model):

    point = PointField(null=True)
    segment_path = SegmentPathField(null=True)
    polygon = PolygonField(null=True)
    segment = SegmentField(null=True)
    box = BoxField(null=True)


class CircleTests(SimpleTestCase):

    def test_from_string(self):
        values = (
            ('<(1,1), 1>', Circle(1, 1, 1)),
            ('<(1,1), -1>', Circle(1, 1, -1)),

            ('<(1,1), 1.5>', Circle(1, 1, 1.5)),
            ('<(1,1), -1.5>', Circle(1, 1, -1.5)),

            ('<(1,1), .5>', Circle(1, 1, 0.5)),
            ('<(1,1), -.5>', Circle(1, 1, -0.5)),
        )

        for value_str, expected in values:
            value = Circle.from_string(value_str)

            self.assertEqual(value, expected, (value_str, value, expected))

    def test_constructor_radius(self):
        circle = Circle(1)

        self.assertEqual(circle.center, Point())
        self.assertEqual(circle.radius, 1)

    def test_constructor_point_radius(self):
        center = Point(1, 2)
        circle = Circle(center, 1)

        self.assertEqual(circle.center, center)
        self.assertEqual(circle.radius, 1)

    def test_constructor_center_radius(self):
        circle = Circle(1, 2, 3)

        self.assertEqual(circle.center, Point(1, 2))
        self.assertEqual(circle.radius, 3)

    def test_eq(self):
        self.assertTrue(Point(1, 1) == Point(1, 1))
        self.assertFalse(Point(1, 1) != Point(1, 1))
        self.assertTrue(Point(1, 1) != Point(2, 1))
        self.assertTrue(Point(1, 1) != Point(1, 2))
        self.assertTrue(Point(1, 1) != Point(2, 2))
        self.assertTrue(Point(1, 1) == Point(1.0, 1.0))


class PointTests(SimpleTestCase):

    def test_from_string(self):
        values = (
            ('(1,1)', Point(1, 1)),
            ('(-1,1)', Point(-1, 1)),
            ('(1,-1)', Point(1, -1)),
            ('(-1,-1)', Point(-1, -1)),

            ('(1.5,1.5)', Point(1.5, 1.5)),
            ('(-1.5,1.5)', Point(-1.5, 1.5)),
            ('(1.5,-1.5)', Point(1.5, -1.5)),
            ('(-1.5,-1.5)', Point(-1.5, -1.5)),

            ('(.5,.5)', Point(0.5, 0.5)),
            ('(-.5,.5)', Point(-0.5, 0.5)),
            ('(.5,-.5)', Point(0.5, -0.5)),
            ('(-.5,-.5)', Point(-0.5, -0.5)),
        )

        for value_str, expected in values:
            value = Point.from_string(value_str)

            self.assertEqual(value, expected, (value_str, value, expected))

    def test_default_values(self):
        point = Point()

        self.assertEqual(point.x, 0)
        self.assertEqual(point.y, 0)

    def test_eq(self):
        self.assertTrue(Point(1, 1) == Point(1, 1))
        self.assertFalse(Point(1, 1) != Point(1, 1))
        self.assertTrue(Point(1, 1) != Point(2, 1))
        self.assertTrue(Point(1, 1) != Point(1, 2))
        self.assertTrue(Point(1, 1) != Point(2, 2))
        self.assertTrue(Point(1, 1) == Point(1.0, 1.0))

    def test_less_than(self):
        self.assertTrue(Point() < Point(1, 1))
        self.assertTrue(Point() <= Point(1, 1))
        self.assertFalse(Point() > Point(1, 1))
        self.assertFalse(Point() >= Point(1, 1))


class GeometryFieldTestsMixin(object):

    def test_db_type(self):
        self.assertEqual(self.field().db_type(connection), self.db_type)

    def test_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'psycopg2'}

        self.assertIsInstance(
            self.field().db_type(m_connection), six.string_types)

    def test_non_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'sqlite'}

        self.assertRaises(FieldError, self.field().db_type, m_connection)


class SegmentPathFieldTests(GeometryFieldTestsMixin, TestCase):

    field = SegmentPathField
    db_type = 'path'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2)]

        model = TestModel()
        model.segment_path = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertIsInstance(model.segment_path, list)
        self.assertEqual(model.segment_path, value)

    def test_minimum_points(self):
        model = TestModel()
        model.segment_path = [Point()]

        with self.assertRaisesRegexp(ValueError, "Needs at minimum 2 points"):
            model.save()


class PolygonFieldTests(GeometryFieldTestsMixin, TestCase):

    field = PolygonField
    db_type = 'polygon'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2), Point(1, 1)]

        model = TestModel()
        model.polygon = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertIsInstance(model.polygon, list)
        self.assertEqual(model.polygon, value)

    def test_non_closed_polygon(self):
        """
        First and last points on a polygon must be equal
        """
        model = TestModel()
        model.polygon = [Point(), Point(1, 1), Point(2, 2)]

        with self.assertRaisesRegexp(ValueError, 'Not self-closing polygon'):
            model.save()

    def test_minimum_points(self):
        model = TestModel()
        model.polygon = [Point(), Point()]

        with self.assertRaisesRegexp(ValueError, "Needs at minimum 3 points"):
            model.save()


class PointFieldTests(GeometryFieldTestsMixin, TestCase):

    field = PointField
    db_type = 'point'

    def test_store_field(self):
        value = Point(1, 1)

        model = TestModel()
        model.point = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.point, value)


class SegmentFieldTests(GeometryFieldTestsMixin, TestCase):

    field = SegmentField
    db_type = 'lseg'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2)]

        model = TestModel()
        model.segment = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.segment, value)

    def test_less_than_2_points(self):
        model = TestModel()
        model.segment = [Point(1, 1)]

        with self.assertRaisesRegexp(ValueError, "Segment needs exactly two points"):
            model.save()

    def test_more_than_2_points(self):
        model = TestModel()
        model.segment = [Point(1, 1), Point(2, 2), Point(3, 3)]

        with self.assertRaisesRegexp(ValueError, "Segment needs exactly two points"):
            model.save()


class BoxFieldTests(GeometryFieldTestsMixin, TestCase):

    field = BoxField
    db_type = 'box'

    def test_store_field(self):
        value = [Point(2, 2), Point(1, 1)]

        model = TestModel()
        model.box = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.box, sorted(value, reverse=True))

    def test_upper_right_lower_left(self):
        value = [Point(1, 2), Point(2, 1)]  # Upper-left, Lower-right

        model = TestModel()
        model.box = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.box, [Point(2, 2), Point(1, 1)])

    def test_less_than_2_points(self):
        model = TestModel()
        model.box = [Point(1, 1)]

        with self.assertRaisesRegexp(ValueError, "Box needs exactly two points"):
            model.save()

    def test_more_than_2_points(self):
        model = TestModel()
        model.box = [Point(1, 1), Point(2, 2), Point(3, 3)]

        with self.assertRaisesRegexp(ValueError, "Box needs exactly two points"):
            model.save()


class CircleFieldTests(GeometryFieldTestsMixin, TestCase):

    field = CircleField
    db_type = 'circle'

    def test_store_field(self):
        value = [Point(1, 1), Point(2, 2)]

        model = TestModel()
        model.segment = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.segment, value)

    def test_less_than_2_points(self):
        model = TestModel()
        model.segment = [Point(1, 1)]

        with self.assertRaisesRegexp(ValueError, "Segment needs exactly two points"):
            model.save()

    def test_more_than_2_points(self):
        model = TestModel()
        model.segment = [Point(1, 1), Point(2, 2), Point(3, 3)]

        with self.assertRaisesRegexp(ValueError, "Segment needs exactly two points"):
            model.save()
