django-postgres-geometry
========================

Exposes [Postgres geometry types][1] into Django model's fields. This package
doesn't need any extra PostgreSQL extensions to be installed, it uses just the
built-in geometry types.


Installation
------------

Install the package with:

    pip install git+https://github.com/expobrain/django-postgres-geometry


Usage
-----

This packages provides the following type of fields:

- `PointField` a single point in the plane
- `SegmentField` a two-points segment
- `SegmentPathField` a path defined by two or more points
- `PolygonField` a self closing polygon defined by two or more points; the first
   and last point must be equal
- `BoxField` a box defined by te upper-right and lower-left corners ins this;
   the box can be defined by any pair of corners but on retrieve the box will be
   always re-calculated as upper-right and lower-left corners
- `CircleField` a circle defined by a center and a radius

All fields returns `Point` instances except for `CircleField` which return a
`Circle` instance.

The fields acts like a common Django's field with the same set of arguments and
keywords. See the Django's [model field reference][2].


Tests
-----

To run the unit tests you need a PostgreSQL instance up and running on your
localhost. Update the `settings_tests.py` file to accomodate your needs. The
tests can be run with:

    python manage.py test --settings=settings_test


Todo
====

- implement `get_prep_lookup()` functions
- do not require a PostgreSQL instance to run the unit tests
- extend the support of geometry types to other backends as well (SQLite, MySQL,
  etc.)


Changelog
=========

0.1.1
-----

- Fixed Polygon field validation: a polygon must have a minimum of 3 points and
  removed check of last point is equal to the first point 

0.1
---

- First release with all the PostgreSQL geometrics types implemented except the
  SQL filtering support


[1]: http://www.postgresql.org/docs/9.3/static/datatype-geometric.html
[2]: https://docs.djangoproject.com/en/dev/ref/models/fields/
