from setuptools import setup, find_packages


setup(
    name="django-posgtres-geometry",
    version="0.1.1",
    packages=find_packages(),
    install_requires=['django', 'psycopg2'],
    description="Django ORM field for Postgres geometry types",
    author="Daniele Esposti",
    author_email="expo@expobrain.net",
    maintainer="Daniele Esposti",
    maintainer_email="expo@expobrain.net",
    url="http://github.com/expobrain/django-postgres-geometry",
)
