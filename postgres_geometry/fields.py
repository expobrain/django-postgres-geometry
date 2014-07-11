import re
import collections
import functools

from django.core.exceptions import FieldError
from django.utils.six import with_metaclass
from django.db import models


def require_postgres(fn):

    def wrapper(self, connection):
        if 'psycopg2' not in connection.settings_dict['ENGINE']:
            raise FieldError("Current database is not a PostgreSQL instance")

        return fn(self, connection)

    return wrapper


@functools.total_ordering
class Point(object):

    _FLOAT_RE = r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'

    POINT_RE = re.compile(r'\((?P<x>{0}),(?P<y>{0})\)'.format(_FLOAT_RE))

    @staticmethod
    def from_string(value):
        match = Point.POINT_RE.match(value)

        if not match:
            raise ValueError("Value {} is not a valid point".format(value))

        values = match.groupdict()

        return Point(float(values['x']), float(values['y']))

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __repr__(self):
        return '<Point({0.x},{0.y})>'.format(self)

    def __str__(self):
        return '({0.x},{0.y})'.format(self)

    def __unicode__(self):
        return unicode(self.__str__())

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.x == other.x
                and self.y == other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        # import ipdb; ipdb.set_trace()
        return (isinstance(other, self.__class__)
                and self.x <= other.x
                and self.y <= other.y)


class PointMixin(object):

    SPLIT_RE = re.compile(r"\((?!\().*?\)")

    def to_python(self, values):
        if values is None:
            return None

        if not isinstance(values, collections.Iterable):
            raise TypeError("Value {} is not iterable".format(values))

        if all(isinstance(v, Point) for v in values):
            return values

        return list(Point.from_string(v) for v in self.SPLIT_RE.findall(values))

    def _get_prep_value(self, values):
        return ','.join(str(v) for v in values) if values else None


class SegmentPathField(PointMixin,
                       with_metaclass(models.SubfieldBase, models.Field)):

    @require_postgres
    def db_type(self, connection):
        return 'path'

    def get_prep_value(self, values):
        values = self._get_prep_value(values)

        return '[{}]'.format(values) if values else None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class PolygonField(PointMixin,
                   with_metaclass(models.SubfieldBase, models.Field)):

    @require_postgres
    def db_type(self, connection):
        return 'polygon'

    def get_prep_value(self, values):
        if values:
            values = tuple(values)

            if values[0] != values[-1]:
                raise ValueError('Not self-closing polygon')

        values = self._get_prep_value(values)

        return '({})'.format(values) if values else None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class PointField(with_metaclass(models.SubfieldBase, models.Field)):

    @require_postgres
    def db_type(self, connection):
        return 'point'

    def to_python(self, value):
        if isinstance(value, Point) or value is None:
            return value

        return Point.from_string(value)

    def get_prep_value(self, value):
        return '({0.x},{0.y})'.format(value) if value else None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class SegmentField(PointMixin,
                   with_metaclass(models.SubfieldBase, models.Field)):

    @require_postgres
    def db_type(self, connection):
        return 'lseg'

    def get_prep_value(self, value):
        if value and len(value) != 2:
            raise ValueError("Segment needs exactly two points")

        return self._get_prep_value(value)

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class BoxField(PointMixin, with_metaclass(models.SubfieldBase, models.Field)):

    @require_postgres
    def db_type(self, connection):
        return 'box'

    def get_prep_value(self, value):
        if value and len(value) != 2:
            raise ValueError("Box needs exactly two points")

        return self._get_prep_value(value)

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)
