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

import tempfile

from django.test import TestCase

from .. import ca_settings
from ..extensions import AuthorityInformationAccess
from ..extensions import AuthorityKeyIdentifier
from ..extensions import BasicConstraints
from ..extensions import CRLDistributionPoints
from ..extensions import ExtendedKeyUsage
from ..extensions import FreshestCRL
from ..extensions import InhibitAnyPolicy
from ..extensions import IssuerAlternativeName
from ..extensions import KeyUsage
from ..extensions import NameConstraints
from ..extensions import OCSPNoCheck
from ..extensions import PolicyConstraints
from ..extensions import PrecertPoison
from ..extensions import SubjectAlternativeName
from ..extensions import TLSFeature
from .base import DjangoCATestCase
from .base import DjangoCAWithCATestCase
from .base import certs
from .base import override_settings
from .base import override_tmpcadir


class TestDjangoCATestCase(DjangoCATestCase):
    # test the base test-class

    @override_tmpcadir()
    def test_override_tmpcadir(self):
        ca_dir = ca_settings.CA_DIR
        self.assertTrue(ca_dir.startswith(tempfile.gettempdir()))

    def test_tmpcadir(self):
        old_ca_dir = ca_settings.CA_DIR

        with self.tmpcadir():
            ca_dir = ca_settings.CA_DIR
            self.assertNotEqual(ca_dir, old_ca_dir)
            self.assertTrue(ca_dir.startswith(tempfile.gettempdir()))

        self.assertEqual(ca_settings.CA_DIR, old_ca_dir)  # ensure that they're equal again

    @override_tmpcadir()
    def test_assert_extensions(self):
        self.load_usable_cas()
        self.load_generated_certs()

        self.assertExtensions(self.certs['no-extensions'], [], expect_defaults=False)
        self.assertExtensions(self.certs['no-extensions'].x509, [], expect_defaults=False)

        cert_key = 'all-extensions'
        cert = self.certs[cert_key]
        data = certs[cert_key]
        all_extensions = [
            OCSPNoCheck(),
            PrecertPoison(),
            data[ExtendedKeyUsage.key],
            data[FreshestCRL.key],
            data[InhibitAnyPolicy.key],
            data[IssuerAlternativeName.key],
            data[KeyUsage.key],
            data[NameConstraints.key],
            data[PolicyConstraints.key],
            data[SubjectAlternativeName.key],
            data[TLSFeature.key],
        ]

        self.maxDiff = None
        self.assertExtensions(cert, all_extensions)

        # when we pass an x509 with a signer, we still have a default AuthorityKeyIdentifier extension
        all_extensions += [
            BasicConstraints(),
            data[CRLDistributionPoints.key],
            data[AuthorityInformationAccess.key],
        ]
        self.assertExtensions(cert.x509, all_extensions, signer=cert.ca)

        # Now, we need even the AuthorityKeyIdentifier extension
        all_extensions += [
            data[AuthorityKeyIdentifier.key],
        ]
        self.assertExtensions(cert.x509, all_extensions)

        # now test root and child ca
        cert_key = 'root'
        ca = self.cas[cert_key]
        data = certs[cert_key]

        root_extensions = [
            data[BasicConstraints.key],
            data[KeyUsage.key],
        ]
        self.assertExtensions(ca, root_extensions)

        cert_key = 'child'
        ca = self.cas[cert_key]
        data = certs[cert_key]

        root_extensions = [
            data[AuthorityInformationAccess.key],
            data[BasicConstraints.key],
            data[CRLDistributionPoints.key],
            data[KeyUsage.key],
        ]
        self.assertExtensions(ca, root_extensions)


class OverrideSettingsFuncTestCase(TestCase):
    @override_settings(CA_MIN_KEY_SIZE=256)
    def test_basic(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 256)


@override_settings(CA_MIN_KEY_SIZE=512)
class OverrideSettingsClassOnlyTestCase(DjangoCATestCase):
    def test_basic(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 512)

    def test_second(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 512)


@override_settings(CA_MIN_KEY_SIZE=128)
class OverrideSettingsClassTestCase(DjangoCATestCase):
    def test_basic(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 128)

    @override_settings(CA_MIN_KEY_SIZE=256)
    def test_double(self):
        self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 256)

        with self.settings(CA_MIN_KEY_SIZE=512):
            self.assertEqual(ca_settings.CA_MIN_KEY_SIZE, 512)


class OverrideCaDirForFuncTestCase(DjangoCATestCase):
    @classmethod
    def setUpClass(cls):
        super(OverrideCaDirForFuncTestCase, cls).setUpClass()
        cls.seen_dirs = set()

    @override_tmpcadir()
    def test_a(self):
        # add three tests to make sure that every test case sees a different dir
        self.assertTrue(ca_settings.CA_DIR.startswith(tempfile.gettempdir()), ca_settings.CA_DIR)
        self.assertNotIn(ca_settings.CA_DIR, self.seen_dirs)
        self.seen_dirs.add(ca_settings.CA_DIR)

    @override_tmpcadir()
    def test_b(self):
        self.assertTrue(ca_settings.CA_DIR.startswith(tempfile.gettempdir()), ca_settings.CA_DIR)
        self.assertNotIn(ca_settings.CA_DIR, self.seen_dirs)
        self.seen_dirs.add(ca_settings.CA_DIR)

    @override_tmpcadir()
    def test_c(self):
        self.assertTrue(ca_settings.CA_DIR.startswith(tempfile.gettempdir()), ca_settings.CA_DIR)
        self.assertNotIn(ca_settings.CA_DIR, self.seen_dirs)
        self.seen_dirs.add(ca_settings.CA_DIR)

    def test_no_classes(self):
        msg = r'^Only functions can use override_tmpcadir\(\)$'
        with self.assertRaisesRegex(ValueError, msg):
            @override_tmpcadir()
            class Foo():
                pass


class CommandTestCase(DjangoCAWithCATestCase):
    def test_basic(self):
        self.cmd_e2e(['list_cas'])
