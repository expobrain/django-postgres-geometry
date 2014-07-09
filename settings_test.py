DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django-postgres-geometry',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': 'postgres'
    },
}

SECRET_KEY = 'my-little-secret-key'

INSTALLED_APPS = (
    'postgres_geometry',
)
