import os
import yaml

from django.utils.crypto import get_random_string

DEBUG = False
LOGIN_URL = '/admin/login/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/lib/django-ca/db.sqlite3',
    },
}
STATIC_ROOT = '/usr/share/django-ca/'
ALLOWED_HOSTS = [
    '*'
]

# This is overwritten by file below generated by the start script
SECRET_KEY = 'default'

# We generate SECRET_KEY on first invocation
_secret_key_path = '/var/lib/django-ca/secret_key'
if os.path.exists(_secret_key_path):
    with open(_secret_key_path) as stream:
        SECRET_KEY = stream.read()

CA_DIR = '/var/lib/django-ca/certs'

_CA_SETTINGS_FILE = os.environ.get('DJANGO_CA_SETTINGS')
if _CA_SETTINGS_FILE:
    with open(_CA_SETTINGS_FILE) as stream:
        data = yaml.load(stream)
    for key, value in data.items():
        globals()[key] = value

# Also use DJANGO_CA_ environment variables
for key, value in {k[10:]: v for k, v in os.environ.items() if k.startswith('DJANGO_CA_')}.items():
    if key == 'SETTINGS':
        continue
    globals()[key] = value