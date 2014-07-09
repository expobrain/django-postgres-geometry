from django.test import TestCase, SimpleTestCase
from django.utils import six
from django.db import models, connection
from django.core.exceptions import FieldError
from mock import Mock

from .fields import Point, PointField


class TestModel(models.Model):

    point = PointField(null=True)


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


class GeometryFieldTestsMixin(object):

    def test_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'psycopg2'}

        self.assertIsInstance(
            self.field.db_type(m_connection), six.string_types)

    def test_non_postgres_connection(self):
        m_connection = Mock()
        m_connection.settings_dict = {'ENGINE': 'sqlite'}

        self.assertRaises(FieldError, self.field.db_type, m_connection)


class PointFieldTests(GeometryFieldTestsMixin, TestCase):

    def setUp(self):
        self.field = PointField()

    def test_db_type(self):
        self.assertEqual(self.field.db_type(connection), 'point')

    def test_store_field(self):
        value = Point(1, 1)

        model = TestModel.objects.create()
        model.point = value
        model.save()

        model = TestModel.objects.get(pk=model.pk)

        self.assertEqual(model.point, value)
