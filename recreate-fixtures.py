#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of django-ca (https://github.com/mathiasertl/django-ca).
#
# django-ca is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# django-ca is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-ca.  If not,
# see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time

#from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
#from cryptography.hazmat.primitives.serialization import Encoding
#from cryptography.hazmat.primitives.serialization import NoEncryption
#from cryptography.hazmat.primitives.serialization import PrivateFormat
_rootdir = os.path.dirname(os.path.realpath(__file__))  # NOQA
sys.path.insert(0, os.path.join(_rootdir, 'ca'))  # NOQA
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'ca.test_settings')  # NOQA
import django  # NOQA
django.setup()  # NOQA

from django.conf import settings
from django.core.management import call_command as manage
from django.test.utils import override_settings
from django.utils.six.moves import reload_module
from django.urls import reverse

from django_ca import ca_settings
from django_ca.models import Certificate
from django_ca.models import CertificateAuthority
from django_ca.profiles import get_cert_profile_kwargs
from django_ca.utils import bytes_to_hex
from django_ca.utils import ca_storage

now = datetime.utcnow().replace(second=0, minute=0)
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:  # pragma: only py2
    from mock import patch
else:
    from unittest.mock import patch

manage('migrate', verbosity=0)

# Some variables used in various places throughout the code
key_size = 1024  # Size for private keys
ca_base_cn = 'ca.example.com'
root_pathlen = None
child_pathlen = 0
ecc_pathlen = 1
pwd_pathlen = 2
dsa_pathlen = 3
dsa_algorithm = 'SHA1'
testserver = 'http://testserver'


class override_tmpcadir(override_settings):
    """Simplified copy of the same decorator in tests.base."""

    def enable(self):
        self.options['CA_DIR'] = tempfile.mkdtemp()
        self.mock = patch.object(ca_storage, 'location', self.options['CA_DIR'])
        self.mock_ = patch.object(ca_storage, '_location', self.options['CA_DIR'])
        self.mock.start()
        self.mock_.start()

        super(override_tmpcadir, self).enable()
        reload_module(ca_settings)

    def disable(self):
        super(override_tmpcadir, self).disable()
        self.mock.stop()
        self.mock_.stop()
        shutil.rmtree(self.options['CA_DIR'])
        reload_module(ca_settings)


def update_cert_data(cert, data):
    data['serial'] = cert.serial
    data['hpkp'] = cert.hpkp_pin
    data['authority_key_identifier'] = bytes_to_hex(cert.authority_key_identifier.value)
    data['subject_key_identifier'] = bytes_to_hex(cert.subject_key_identifier.value)
    data['valid_from'] = cert.x509.not_valid_before.strftime('%Y-%m-%d %H:%M:%S')
    data['valid_until'] = cert.x509.not_valid_after.strftime('%Y-%m-%d %H:%M:%S')

    data['md5'] = cert.get_digest('md5')
    data['sha1'] = cert.get_digest('sha1')
    data['sha256'] = cert.get_digest('sha256')
    data['sha512'] = cert.get_digest('sha512')

    ku = cert.key_usage
    if ku is not None:
        data['key_usage'] = ku.serialize()

    aia = cert.authority_information_access
    if aia is not None:
        data['authority_information_access'] = aia.serialize()

    san = cert.subject_alternative_name
    if san is not None:
        data['subject_alternative_name'] = san.serialize()

    ian = cert.issuer_alternative_name
    if ian is not None:
        data['issuer_alternative_name'] = ian.serialize()

    eku = cert.extended_key_usage
    if eku is not None:
        data['extended_key_usage'] = eku.serialize()


def write_ca(cert, data, password=None):
    key_dest = os.path.join(settings.FIXTURES_DIR, data['key'])
    pub_dest = os.path.join(settings.FIXTURES_DIR, data['pub'])
    #key_der_dest = os.path.join(settings.FIXTURES_DIR, data['key-der'])
    #pub_der_dest = os.path.join(settings.FIXTURES_DIR, data['pub-der'])

    # write files to dest
    shutil.copy(ca_storage.path(cert.private_key_path), key_dest)
    with open(pub_dest, 'w') as stream:
        stream.write(cert.pub)

    #if password is None:
    #    encryption = NoEncryption()
    #else:
    #    encryption = BestAvailableEncryption(password)

    #key_der = cert.key(password=password).private_bytes(
    #   encoding=Encoding.DER, format=PrivateFormat.PKCS8, encryption_algorithm=encryption)
    #with open(key_der_dest, 'wb') as stream:
    #    stream.write(key_der)
    #with open(pub_der_dest, 'wb') as stream:
    #    stream.write(cert.dump_certificate(Encoding.DER))

    # These keys are only present in CAs:
    data['issuer_url'] = ca.issuer_url
    data['crl_url'] = ca.crl_url
    data['ca_crl_url'] = '%s%s' % (testserver, reverse('django_ca:ca-crl', kwargs={'serial': ca.serial}))

    # Update common data for CAs and certs
    update_cert_data(cert, data)


def copy_cert(cert, data, key_path, csr_path):
    key_dest = os.path.join(settings.FIXTURES_DIR, data['key'])
    csr_dest = os.path.join(settings.FIXTURES_DIR, data['csr'])
    pub_dest = os.path.join(settings.FIXTURES_DIR, data['pub'])
    shutil.copy(key_path, key_dest)
    shutil.copy(csr_path, csr_dest)
    with open(pub_dest, 'w') as stream:
        stream.write(cert.pub)

    data['crl'] = cert.ca.crl_url

    update_cert_data(cert, data)


data = {
    'root': {
        'type': 'ca',
        'password': None,
        'subject': '/C=AT/ST=Vienna/CN=%s' % ca_base_cn,
        'pathlen': root_pathlen,

        'basic_constraints': 'critical,CA:TRUE',
        'key_usage': 'critical,cRLSign,keyCertSign',
    },
    'child': {
        'type': 'ca',
        'delta': timedelta(days=3),
        'parent': 'root',
        'password': None,
        'subject': '/C=AT/ST=Vienna/CN=child.%s' % ca_base_cn,

        'basic_constraints': 'critical,CA:TRUE,pathlen=%s' % child_pathlen,
        'pathlen': child_pathlen,
        'name_constraints': [['DNS:.org'], ['DNS:.net']],
    },
    'ecc': {
        'type': 'ca',
        'password': None,
        'subject': '/C=AT/ST=Vienna/CN=ecc.%s' % ca_base_cn,

        'basic_constraints': 'critical,CA:TRUE,pathlen=%s' % ecc_pathlen,
        'pathlen': ecc_pathlen,
    },
    'dsa': {
        'type': 'ca',
        'algorithm': dsa_algorithm,
        'password': None,
        'subject': '/C=AT/ST=Vienna/CN=dsa.%s' % ca_base_cn,

        'basic_constraints': 'critical,CA:TRUE,pathlen=%s' % dsa_pathlen,
        'pathlen': dsa_pathlen,
    },
    'pwd': {
        'type': 'ca',
        'password': b'testpassword',
        'subject': '/C=AT/ST=Vienna/CN=pwd.%s' % ca_base_cn,

        'basic_constraints': 'critical,CA:TRUE,pathlen=%s' % pwd_pathlen,
        'pathlen': pwd_pathlen,
    },

    'root-cert': {
        'ca': 'root',
        'delta': timedelta(days=5),
        'pathlen': root_pathlen,
        'csr': True,
        'basic_constraints': 'critical,CA:FALSE',
    },
    'child-cert': {
        'ca': 'child',
        'delta': timedelta(days=5),
        'csr': True,
        'basic_constraints': 'critical,CA:FALSE',
    },
    'ecc-cert': {
        'ca': 'ecc',
        'delta': timedelta(days=5),
        'csr': True,
        'basic_constraints': 'critical,CA:FALSE',
    },
    'pwd-cert': {
        'ca': 'pwd',
        'delta': timedelta(days=5),
        'csr': True,
        'basic_constraints': 'critical,CA:FALSE',
    },
    'dsa-cert': {
        'ca': 'dsa',
        'delta': timedelta(days=5),
        'algorithm': dsa_algorithm,
        'csr': True,
        'basic_constraints': 'critical,CA:FALSE',
    },
}

# Autocompute some values (name, filenames, ...) based on the dict key
for cert, cert_values in data.items():
    cert_values['name'] = cert
    cert_values.setdefault('algorithm', 'SHA256')
    cert_values['key'] = '%s.key' % cert_values['name']
    cert_values['pub'] = '%s.pem' % cert_values['name']
    cert_values.setdefault('key_size', key_size)
    cert_values.setdefault('key_type', 'RSA')
    cert_values.setdefault('delta', timedelta())
    if cert_values.pop('csr', False):
        cert_values['csr'] = '%s.csr' % cert_values['name']

    if cert_values.get('type') == 'ca':
        data[cert]['ca_ocsp_url'] = '%s/ca/ocsp/%s/' % (testserver, data[cert]['name'])
    else:
        data[cert]['cn'] = '%s.example.com' % cert

ca_names = [v['name'] for k, v in data.items() if v.get('type') == 'ca']
ca_instances = []

with override_tmpcadir():
    # Create CAs
    for name in ca_names:
        kwargs = {}

        # Get some data from the parent, if present
        parent = data[name].get('parent')
        if parent:
            kwargs['parent'] = CertificateAuthority.objects.get(name=parent)
            kwargs['ca_crl_url'] = data[parent]['ca_crl_url']
            kwargs['ca_issuer_url'] = data[parent]['issuer_url']
            kwargs['ca_ocsp_url'] = data[parent]['ca_ocsp_url']

            # also update data
            data[name]['crl'] = data[parent]['ca_crl_url']

        with freeze_time(now + data[name]['delta']):
            ca = CertificateAuthority.objects.init(
                name=data[name]['name'], password=data[name]['password'], subject=data[name]['subject'],
                key_type=data[name]['key_type'], key_size=data[name]['key_size'],
                algorithm=data[name]['algorithm'],
                pathlen=data[name]['pathlen'], **kwargs
            )
        ca.crl_url = '%s%s' % (testserver, reverse('django_ca:crl', kwargs={'serial': ca.serial}))
        ca.ocsp_url = '%s%s' % (testserver, reverse('django_ca:ocsp-post-%s' % name))
        ca.issuer_url = '%s/%s.der' % (testserver, name)
        ca.save()
        ca_instances.append(ca)

        write_ca(ca, data[name])

    # add parent/child relationships
    data['root']['children'] = [
        [data['child']['name'], data['child']['serial']],
    ]

    # let's create a standard certificate for every CA
    for ca in ca_instances:
        name = '%s-cert' % ca.name
        key_path = os.path.join(ca_settings.CA_DIR, '%s.key' % name)
        csr_path = os.path.join(ca_settings.CA_DIR, '%s.csr' % name)

        if PY2:
            # PY2 does not have subprocess.DEVNULL
            with open(os.devnull, 'w') as devnull:
                subprocess.call(['openssl', 'genrsa', '-out', key_path, str(key_size)], stderr=devnull)
        else:
            subprocess.call(['openssl', 'genrsa', '-out', key_path, str(key_size)], stderr=subprocess.DEVNULL)

        subprocess.call(['openssl', 'req', '-new', '-key', key_path, '-out', csr_path, '-utf8', '-batch'])
        kwargs = get_cert_profile_kwargs('server')
        kwargs['subject'].append(('CN', data[name]['cn']))
        with open(csr_path) as stream:
            csr = stream.read()

        pwd = data[data[name]['ca']]['password']

        with freeze_time(now + data[name]['delta']):
            cert = Certificate.objects.init(ca=ca, csr=csr, algorithm=data[name]['algorithm'],
                                            password=pwd, **kwargs)
        copy_cert(cert, data[name], key_path, csr_path)

for name, cert_data in data.items():
    del cert_data['delta']

    if cert_data.get('password'):
        cert_data['password'] = cert_data['password'].decode('utf-8')

fixture_data = {
    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
    'certs': data,
}

with open(os.path.join(settings.FIXTURES_DIR, 'cert-data.json'), 'w') as stream:
    json.dump(fixture_data, stream, indent=4)