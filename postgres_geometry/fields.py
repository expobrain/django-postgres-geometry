import re
import collections
import functools

from django.core.exceptions import FieldError
from django.utils.six import with_metaclass
from django.db import models


_FLOAT_RE = r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'


def require_postgres(fn):
    """
    Decorator that checks if the target backend engine is a PostgreSQL instance

    :raises: FieldError
    """

    def wrapper(self, connection):
        if 'psycopg2' not in connection.settings_dict['ENGINE']:
            raise FieldError("Current database is not a PostgreSQL instance")

        return fn(self, connection)

    return wrapper


@functools.total_ordering
class Point(object):
    """
    Describe a point in the space.
    """

    POINT_RE = r'\((?P<x>{0}),(?P<y>{0})\)'.format(_FLOAT_RE)

    @staticmethod
    def from_string(value):
        """
        Convert a string describing a point into a `Point` instance.

        The representation of a point as a string:

            (x, y)

        where `x` and `y` can be signed or unsigned integers or floats

        :param value: The string representation of the point
        :rtype: Point
        :raise: ValueError if the given string is not a valid point's
                representation
        """
        match = re.match(Point.POINT_RE, value)

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
        return (isinstance(other, self.__class__)
                and self.x <= other.x
                and self.y <= other.y)


class Circle(object):
    """
    Describe a circle with center and radius
    """

    CIRCLE_RE = r'<{0},\s(?P<r>{1})>'.format(Point.POINT_RE, _FLOAT_RE)

    @staticmethod
    def from_string(value):
        """
        Convert a string describing a circle into a `Circle` instance.

        The representation of a circle as a string:

            <(x, y), r>

        where `x`, 'y' and `r` can be signed or unsigned integers or floats; 'x'
        and 'y' defines the center of the circle and 'r' the radius.

        :param value: The string representation of the circle
        :rtype: Circle
        :raise: ValueError if the given string is not a valid circle's
                representation
        """
        match = re.match(Circle.CIRCLE_RE, value)

        if not match:
            raise ValueError("Value {} is not a valid circle".format(value))

        values = match.groupdict()

        return Circle(
            float(values['x']), float(values['y']), float(values['r']))

    def __init__(self, *args):
        """
        Constructor accept up to 3 arguments with the following signatures:

        * `Circle(r)` creates a circle in the origin with radius r`
        * `Circle(<Point>, r)` creates a circle with center in the given point
          and radius `r`
        * `Circle(x, y, r)` creates a circle with center in the given `x` and
          `y` coordinates and radius `r`
        """
        argc = len(args)

        if argc == 1:
            self.center = Point()
            self.radius = args[0]

        elif argc == 2 and isinstance(args[0], Point):
            self.center = args[0]
            self.radius = args[1]

        elif argc == 3:
            self.center = Point(*args[:2])
            self.radius = args[2]

        else:
            raise TypeError("Invalid set of arguments {}".format(args))

    def __eq__(self, other):
        return (isinstance(other, Circle)
                and self.center == other.center
                and self.radius == other.radius)


class PointMixin(object):

    SPLIT_RE = re.compile(r"\((?!\().*?\)")

    def to_python(self, values):
        if values is None:
            return None

        if not isinstance(values, collections.Iterable):
            raise TypeError("Value {} is not iterable".format(values))

        if all(isinstance(v, Point) for v in values):
            return values

        return list(
            Point.from_string(v) for v in re.findall(self.SPLIT_RE, values))

    def _get_prep_value(self, values):
        return ','.join(str(v) for v in values) if values else None


class SegmentPathField(PointMixin,
                       with_metaclass(models.SubfieldBase, models.Field)):
    """
    Field to store a path; needs at least two set of points
    """

    @require_postgres
    def db_type(self, connection):
        return 'path'

    def get_prep_value(self, values):
        if values:
            values = tuple(values)

            if len(values) < 2:
                raise ValueError("Needs at minimum 2 points")

        values = self._get_prep_value(values)

        return '[{}]'.format(values) if values else None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class PolygonField(PointMixin,
                   with_metaclass(models.SubfieldBase, models.Field)):
    """
    Field to store a polygon; needs at least three set of points and the first
    and last points must be equal
    """

    @require_postgres
    def db_type(self, connection):
        return 'polygon'

    def get_prep_value(self, values):
        if values:
            values = tuple(values)

            if len(values) < 3:
                raise ValueError("Needs at minimum 3 points")

            if values[0] != values[-1]:
                raise ValueError('Not self-closing polygon')

        values = self._get_prep_value(values)

        return '({})'.format(values) if values else None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class PointField(with_metaclass(models.SubfieldBase, models.Field)):
    """
    Field to store a single point in space
    """

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
    """
    Field to store a path; needs exactly two set of points
    """

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
    """
    Field to store a box's definition.

    Needs two set of points defining the opposite corners of box. Any pair of
    opposite corners can be set to this field but on retrieve the upper-right
    and lower-left corners will be given back in this order.
    """

    @require_postgres
    def db_type(self, connection):
        return 'box'

    def get_prep_value(self, value):
        if value and len(value) != 2:
            raise ValueError("Box needs exactly two points")

        return self._get_prep_value(value)

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


class CircleField(with_metaclass(models.SubfieldBase, models.Field)):
    """
    Field to store a circle's definition
    """

    @require_postgres
    def db_type(self, connection):
        return 'circle'

    def to_python(self, value):
        if value is None or isinstance(value, Circle):
            return value

        return Circle.from_string(value)

    def get_prep_value(self, value):
        if value:
            return "<{0.center.x}, {0.center.y}}, {0.radius}>".format(value)

        return None

    def get_prep_lookup(self, lookup_type, value):
        return NotImplementedError(self)


# Try to load South's model inspector
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^postgres_geometry\.fields\.\w+Field'])

except ImportError:
    pass
