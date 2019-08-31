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

from __future__ import unicode_literals

import doctest
import unittest

import six

from cryptography import x509
from cryptography.x509 import TLSFeatureType
from cryptography.x509.oid import AuthorityInformationAccessOID
from cryptography.x509.oid import ExtendedKeyUsageOID
from cryptography.x509.oid import ExtensionOID
from cryptography.x509.oid import NameOID
from cryptography.x509.oid import ObjectIdentifier

from django.test import TestCase
from django.utils.functional import cached_property

from .. import ca_settings
from ..extensions import AuthorityInformationAccess
from ..extensions import AuthorityKeyIdentifier
from ..extensions import BasicConstraints
from ..extensions import CertificatePolicies
from ..extensions import CRLDistributionPoints
from ..extensions import DistributionPoint
from ..extensions import ExtendedKeyUsage
from ..extensions import Extension
from ..extensions import IssuerAlternativeName
from ..extensions import KeyUsage
from ..extensions import KnownValuesExtension
from ..extensions import ListExtension
from ..extensions import NameConstraints
from ..extensions import OCSPNoCheck
from ..extensions import PolicyInformation
from ..extensions import PrecertificateSignedCertificateTimestamps
from ..extensions import PrecertPoison
from ..extensions import SubjectAlternativeName
from ..extensions import SubjectKeyIdentifier
from ..extensions import TLSFeature
from ..extensions import UnrecognizedExtension
from ..models import X509CertMixin
from .base import DjangoCATestCase
from .base import DjangoCAWithCertTestCase
from .base import certs


def dns(d):  # just a shortcut
    return x509.DNSName(d)


def uri(u):  # just a shortcut
    return x509.UniformResourceIdentifier(u)


def load_tests(loader, tests, ignore):
    if six.PY3:  # pragma: only py3
        # unicode strings make this very hard to test doctests in both py2 and py3
        tests.addTests(doctest.DocTestSuite('django_ca.extensions'))
    return tests


class ExtensionTestMixin:
    def test_config(self):
        self.assertTrue(issubclass(self.ext_class, Extension))
        self.assertIsInstance(self.ext_class.key, six.string_types)
        self.assertGreater(len(self.ext_class.key), 1)

        # test that the model matches
        self.assertEqual(X509CertMixin.OID_MAPPING[self.ext_class.oid], self.ext_class.key)
        self.assertTrue(hasattr(X509CertMixin, self.ext_class.key))
        self.assertIsInstance(getattr(X509CertMixin, self.ext_class.key), cached_property)

    def test_as_extension(self):
        for e, x in zip(self.exts, self.xs):
            self.assertEqual(e.as_extension(), x)

    def test_as_text(self):
        raise NotImplementedError

    def test_hash(self):
        raise NotImplementedError

    def test_eq(self):
        for e in self.exts:
            self.assertEqual(e, e)

    def test_extension_type(self):
        for e, x in zip(self.exts, self.xs):
            self.assertEqual(e.extension_type, x.value)

    def test_for_builder(self):
        for e, x in zip(self.exts, self.xs):
            self.assertEqual(e.for_builder(), {'critical': x.critical, 'extension': x.value})

    def test_from_extension(self):
        for e, x in zip(self.exts, self.xs):
            self.assertEqual(e, self.ext_class(x))

    def test_ne(self):
        raise NotImplementedError

    def test_repr(self):
        raise NotImplementedError

    def test_serialize(self):
        raise NotImplementedError

    def test_str(self):
        raise NotImplementedError


class ListExtensionTestMixin(ExtensionTestMixin):
    def test_count(self):
        raise NotImplementedError

    def test_del(self):
        raise NotImplementedError

    def test_extend(self):
        raise NotImplementedError

    def test_from_list(self):
        raise NotImplementedError

    def test_getitem(self):
        raise NotImplementedError

    def test_getitem_slices(self):
        raise NotImplementedError

    def test_in(self):
        raise NotImplementedError

    def test_insert(self):
        raise NotImplementedError

    def test_len(self):
        raise NotImplementedError

    def test_not_in(self):
        raise NotImplementedError

    def test_pop(self):
        raise NotImplementedError

    def test_remove(self):
        raise NotImplementedError

    def test_setitem(self):
        raise NotImplementedError

    def test_setitem_slices(self):
        raise NotImplementedError


class KnownValuesExtensionTestMixin(ListExtensionTestMixin):
    def test_eq_order(self):
        raise NotImplementedError

    def test_hash_order(self):
        raise NotImplementedError

    def test_unknown_values(self):
        raise NotImplementedError

    # Currently overwritten b/c KnownValues should behave like a set, not like a list
    def test_del(self):
        pass

    def test_extend(self):
        pass

    def test_getitem(self):
        pass

    def test_getitem_slices(self):
        pass

    def test_insert(self):
        pass

    def test_pop(self):
        pass

    def test_remove(self):
        pass

    def test_setitem(self):
        pass

    def test_setitem_slices(self):
        pass


class ExtensionTestCase(ExtensionTestMixin, TestCase):
    value = 'foobar'

    def test_config(self):
        return  # not useful here

    def assertExtension(self, ext, critical=True):
        self.assertEqual(ext.value, self.value)
        self.assertEqual(ext.critical, critical)

    def test_as_extension(self):
        with self.assertRaises(NotImplementedError):
            Extension(self.value).as_extension()

    def test_extension_type(self):
        with self.assertRaises(NotImplementedError):
            Extension(self.value).extension_type

    def test_eq(self):
        ext = Extension({'value': self.value, 'critical': True})
        self.assertEqual(ext, Extension('critical,%s' % self.value))

    def test_for_builder(self):
        with self.assertRaises(NotImplementedError):
            Extension(self.value).for_builder()

    def test_from_extension(self):
        with self.assertRaises(NotImplementedError):
            Extension(self.value).from_extension(None)

    def test_hash(self):
        self.assertEqual(hash(Extension(self.value)), hash(Extension(self.value)))
        self.assertEqual(hash(Extension({'critical': False, 'value': self.value})),
                         hash(Extension({'critical': False, 'value': self.value})))

        self.assertNotEqual(hash(Extension({'critical': True, 'value': self.value})),
                            hash(Extension({'critical': False, 'value': self.value})))
        self.assertNotEqual(hash(Extension({'critical': False, 'value': self.value[::-1]})),
                            hash(Extension({'critical': False, 'value': self.value})))

    def test_ne(self):
        ext = Extension({'value': self.value, 'critical': True})
        self.assertNotEqual(ext, Extension(self.value))
        self.assertNotEqual(ext, Extension('critical,other'))
        self.assertNotEqual(ext, Extension('other'))

    def test_repr(self):
        self.assertEqual(repr(Extension('critical,%s' % self.value)),
                         '<Extension: %s, critical=True>' % self.value)
        self.assertEqual(repr(Extension(self.value)), '<Extension: %s, critical=False>' % self.value)

    def test_serialize(self):
        value = self.value
        ext = Extension(value)
        self.assertEqual(ext.serialize(), {'critical': False, 'value': value})
        self.assertEqual(ext, Extension(ext.serialize()))

        value = 'critical,%s' % self.value
        ext = Extension(value)
        self.assertEqual(ext.serialize(), {'value': self.value, 'critical': True})
        self.assertEqual(ext, Extension(ext.serialize()))

    def test_str(self):
        self.assertEqual(str(Extension('critical,%s' % self.value)), '%s/critical' % self.value)
        self.assertEqual(str(Extension(self.value)), self.value)

    def test_basic(self):
        self.assertExtension(Extension('critical,%s' % self.value))
        self.assertExtension(Extension({'critical': True, 'value': self.value}))

        self.assertExtension(Extension(self.value), critical=False)
        self.assertExtension(Extension({'critical': False, 'value': self.value}), critical=False)
        self.assertExtension(Extension({'value': self.value}), critical=False)

    def test_as_text(self):
        self.assertEqual(Extension('critical,%s' % self.value).as_text(), self.value)

    def test_error(self):
        with self.assertRaisesRegex(ValueError, r'^None: Invalid critical value passed$'):
            Extension({'critical': None, 'value': ['cRLSign']})

        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type object$'):
            Extension(object())

        with self.assertRaises(NotImplementedError):
            Extension(x509.extensions.Extension(ExtensionOID.BASIC_CONSTRAINTS, True, b''))

        # Test that methods that should be implemented by sub-classes raise NotImplementedError
        ext = Extension('critical,%s' % self.value)
        with self.assertRaises(NotImplementedError):
            ext.extension_type

        with self.assertRaises(NotImplementedError):
            ext.for_builder()

        # These do not work because base class does not define an OID
        with self.assertRaises(AttributeError):
            ext.name


class ListExtensionTestCase(TestCase):
    def test_hash(self):
        self.assertEqual(hash(ListExtension(['foo'])), hash(ListExtension(['foo'])))
        self.assertNotEqual(hash(ListExtension({'value': 'foo', 'critical': False})),
                            hash(ListExtension({'value': 'bar', 'critical': False})))
        self.assertNotEqual(hash(ListExtension({'value': 'foo', 'critical': False})),
                            hash(ListExtension({'value': 'foo', 'critical': True})))

    def test_operators(self):
        ext = ListExtension(['foo'])
        self.assertIn('foo', ext)
        self.assertNotIn('bar', ext)

    def test_list_funcs(self):
        ext = ListExtension(['foo'])
        ext.append('bar')
        self.assertEqual(ext.value, ['foo', 'bar'])
        self.assertEqual(ext.count('foo'), 1)
        self.assertEqual(ext.count('bar'), 1)
        self.assertEqual(ext.count('bla'), 0)

        ext.clear()
        self.assertEqual(ext.value, [])
        self.assertEqual(ext.count('foo'), 0)

        ext.extend(['bar', 'bla'])
        self.assertEqual(ext.value, ['bar', 'bla'])
        ext.extend(['foo'])
        self.assertEqual(ext.value, ['bar', 'bla', 'foo'])

        self.assertEqual(ext.pop(), 'foo')
        self.assertEqual(ext.value, ['bar', 'bla'])

        self.assertIsNone(ext.remove('bar'))
        self.assertEqual(ext.value, ['bla'])

        ext.insert(0, 'foo')
        self.assertEqual(ext.value, ['foo', 'bla'])

    def test_slices(self):
        val = ['foo', 'bar', 'bla']
        ext = ListExtension(val)
        self.assertEqual(ext[0], val[0])
        self.assertEqual(ext[1], val[1])
        self.assertEqual(ext[0:], val[0:])
        self.assertEqual(ext[1:], val[1:])
        self.assertEqual(ext[:1], val[:1])
        self.assertEqual(ext[1:2], val[1:2])

        ext[0] = 'test'
        val[0] = 'test'
        self.assertEqual(ext.value, val)
        ext[1:2] = ['x', 'y']
        val[1:2] = ['x', 'y']
        self.assertEqual(ext.value, val)
        ext[1:] = ['a', 'b']
        val[1:] = ['a', 'b']
        self.assertEqual(ext.value, val)

        del ext[0]
        del val[0]
        self.assertEqual(ext.value, val)

    def test_serialize(self):
        val = ['foo', 'bar', 'bla']
        ext = ListExtension({'value': val, 'critical': False})
        self.assertEqual(ext, ListExtension(ext.serialize()))
        ext = ListExtension({'value': val, 'critical': True})
        self.assertEqual(ext, ListExtension(ext.serialize()))


class KnownValuesExtensionTestCase(TestCase):
    def setUp(self):
        self.known = {'foo', 'bar', }

        class TestExtension(KnownValuesExtension):
            KNOWN_VALUES = self.known

        self.cls = TestExtension

    def assertExtension(self, ext, value, critical=True):
        self.assertEqual(ext.critical, critical)
        self.assertCountEqual(ext.value, value)
        self.assertEqual(len(ext), len(value))
        for v in value:
            self.assertIn(v, ext)

    def test_basic(self):
        self.assertExtension(self.cls('critical,'), [])
        self.assertExtension(self.cls('critical,foo'), ['foo'])
        self.assertExtension(self.cls('critical,bar'), ['bar'])
        self.assertExtension(self.cls('critical,foo,bar'), ['foo', 'bar'])

        self.assertExtension(self.cls({'value': 'foo'}), ['foo'], critical=False)
        self.assertExtension(self.cls({'critical': True, 'value': ['foo']}), ['foo'])

        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): hugo$'):
            self.cls({'value': 'hugo'})

        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): bla, hugo$'):
            self.cls({'value': ['bla', 'hugo']})

    def test_eq(self):
        self.assertEqual(self.cls('foo'), self.cls('foo'))
        self.assertEqual(self.cls('foo,bar'), self.cls('foo,bar'))
        self.assertEqual(self.cls('foo,bar'), self.cls('bar,foo'))

        self.assertEqual(self.cls('critical,foo'), self.cls('critical,foo'))
        self.assertEqual(self.cls('critical,foo,bar'), self.cls('critical,foo,bar'))
        self.assertEqual(self.cls('critical,foo,bar'), self.cls('critical,bar,foo'))

    def test_ne(self):
        self.assertNotEqual(self.cls('foo'), self.cls('bar'))
        self.assertNotEqual(self.cls('foo'), self.cls('critical,foo'))

    def test_operators(self):
        ext = self.cls('foo')

        # in operator
        self.assertIn('foo', ext)
        self.assertNotIn('bar', ext)
        self.assertNotIn('something else', ext)

        # equality
        self.assertEqual(ext, self.cls('foo'))
        self.assertNotEqual(ext, self.cls('critical,foo'))
        self.assertNotEqual(ext, self.cls('foo,bar'))
        self.assertNotEqual(ext, self.cls('bar'))

        # as_text
        self.assertEqual(ext.as_text(), '* foo')
        self.assertEqual(self.cls('foo,bar').as_text(), '* foo\n* bar')
        self.assertEqual(self.cls('bar,foo').as_text(), '* bar\n* foo')
        self.assertEqual(self.cls('bar').as_text(), '* bar')
        self.assertEqual(self.cls('critical,bar').as_text(), '* bar')

        # str()
        self.assertEqual(str(ext), 'foo')
        self.assertEqual(str(self.cls('foo,bar')), 'bar,foo')
        self.assertEqual(str(self.cls('bar,foo')), 'bar,foo')
        self.assertEqual(str(self.cls('bar')), 'bar')
        self.assertEqual(str(self.cls('critical,bar')), 'bar/critical')
        self.assertEqual(str(self.cls('critical,foo,bar')), 'bar,foo/critical')
        self.assertEqual(str(self.cls('critical,bar,foo')), 'bar,foo/critical')


class AuthorityInformationAccessTestCase(ExtensionTestMixin, TestCase):
    ext_class = AuthorityInformationAccess

    x1 = x509.extensions.Extension(
        oid=ExtensionOID.AUTHORITY_INFORMATION_ACCESS, critical=False,
        value=x509.AuthorityInformationAccess(descriptions=[])
    )
    x2 = x509.extensions.Extension(
        oid=ExtensionOID.AUTHORITY_INFORMATION_ACCESS, critical=False,
        value=x509.AuthorityInformationAccess(descriptions=[
            x509.AccessDescription(AuthorityInformationAccessOID.CA_ISSUERS,
                                   uri('https://example.com')),
        ])
    )
    x3 = x509.extensions.Extension(
        oid=ExtensionOID.AUTHORITY_INFORMATION_ACCESS, critical=False,
        value=x509.AuthorityInformationAccess(descriptions=[
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP,
                                   uri('https://example.com')),
        ])
    )
    x4 = x509.extensions.Extension(
        oid=ExtensionOID.AUTHORITY_INFORMATION_ACCESS, critical=False,
        value=x509.AuthorityInformationAccess(descriptions=[
            x509.AccessDescription(AuthorityInformationAccessOID.CA_ISSUERS,
                                   uri('https://example.com')),
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP,
                                   uri('https://example.net')),
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP,
                                   uri('https://example.org')),
        ])
    )
    x5 = x509.extensions.Extension(
        oid=ExtensionOID.AUTHORITY_INFORMATION_ACCESS, critical=True,
        value=x509.AuthorityInformationAccess(descriptions=[
            x509.AccessDescription(AuthorityInformationAccessOID.CA_ISSUERS,
                                   uri('https://example.com')),
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP,
                                   uri('https://example.net')),
            x509.AccessDescription(AuthorityInformationAccessOID.OCSP,
                                   uri('https://example.org')),
        ])
    )
    xs = [x1, x2, x3, x4, x5]

    def setUp(self):
        super(AuthorityInformationAccessTestCase, self).setUp()
        self.ext1 = AuthorityInformationAccess(self.x1)
        self.ext2 = AuthorityInformationAccess(self.x2)
        self.ext3 = AuthorityInformationAccess(self.x3)
        self.ext4 = AuthorityInformationAccess(self.x4)
        self.ext5 = AuthorityInformationAccess(self.x5)
        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4, self.ext5]

    def test_as_text(self):
        self.assertEqual(self.ext1.as_text(),
                         '')
        self.assertEqual(self.ext2.as_text(),
                         'CA Issuers:\n  * URI:https://example.com\n')
        self.assertEqual(self.ext3.as_text(),
                         'OCSP:\n  * URI:https://example.com\n')
        self.assertEqual(self.ext4.as_text(),
                         'CA Issuers:\n'
                         '  * URI:https://example.com\n'
                         'OCSP:\n'
                         '  * URI:https://example.net\n'
                         '  * URI:https://example.org\n')
        self.assertEqual(self.ext5.as_text(),
                         'CA Issuers:\n'
                         '  * URI:https://example.com\n'
                         'OCSP:\n'
                         '  * URI:https://example.net\n'
                         '  * URI:https://example.org\n')

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))
        self.assertEqual(hash(self.ext4), hash(self.ext4))
        self.assertEqual(hash(self.ext5), hash(self.ext5))

        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext1), hash(self.ext4))
        self.assertNotEqual(hash(self.ext1), hash(self.ext5))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext4))
        self.assertNotEqual(hash(self.ext2), hash(self.ext5))
        self.assertNotEqual(hash(self.ext3), hash(self.ext4))
        self.assertNotEqual(hash(self.ext3), hash(self.ext5))
        self.assertNotEqual(hash(self.ext4), hash(self.ext5))

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext1, self.ext4)
        self.assertNotEqual(self.ext1, self.ext5)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext2, self.ext4)
        self.assertNotEqual(self.ext2, self.ext5)
        self.assertNotEqual(self.ext3, self.ext4)
        self.assertNotEqual(self.ext3, self.ext5)
        self.assertNotEqual(self.ext4, self.ext5)

    def test_repr(self):
        self.assertEqual(
            repr(self.ext1),
            '<AuthorityInformationAccess: issuers=[], ocsp=[], critical=False>')
        self.assertEqual(
            repr(self.ext2),
            '<AuthorityInformationAccess: issuers=[\'URI:https://example.com\'], ocsp=[], critical=False>')
        self.assertEqual(
            repr(self.ext3),
            "<AuthorityInformationAccess: issuers=[], ocsp=['URI:https://example.com'], critical=False>")
        self.assertEqual(
            repr(self.ext4),
            "<AuthorityInformationAccess: issuers=['URI:https://example.com'], "
            "ocsp=['URI:https://example.net', 'URI:https://example.org'], critical=False>")
        self.assertEqual(
            repr(self.ext5),
            "<AuthorityInformationAccess: issuers=['URI:https://example.com'], "
            "ocsp=['URI:https://example.net', 'URI:https://example.org'], critical=True>")

    def test_serialize(self):
        extensions = [
            AuthorityInformationAccess(self.x1),
            AuthorityInformationAccess(self.x2),
            AuthorityInformationAccess(self.x3),
            AuthorityInformationAccess(self.x4),
            AuthorityInformationAccess(self.x5),
        ]
        for ext in extensions:
            self.assertEqual(AuthorityInformationAccess(ext.serialize()), ext)

    #################
    # Old functions #
    #################

    # test the constructor with some list values
    def test_from_list(self):
        ext = AuthorityInformationAccess([['https://example.com'], []])
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x2)

        ext = AuthorityInformationAccess([[], ['https://example.com']])
        self.assertEqual(ext.issuers, [])
        self.assertEqual(ext.ocsp, [uri('https://example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x3)

        ext = AuthorityInformationAccess([[uri('https://example.com')], []])
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x2)

        ext = AuthorityInformationAccess([[], [uri('https://example.com')]])
        self.assertEqual(ext.ocsp, [uri('https://example.com')])
        self.assertEqual(ext.issuers, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x3)

        ext = AuthorityInformationAccess([['https://example.com'], ['https://example.net',
                                                                    'https://example.org']])
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [uri('https://example.net'), uri('https://example.org')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x4)

    def test_from_dict(self):
        ext = AuthorityInformationAccess({'value': {'issuers': ['https://example.com']}})
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x2)

        ext = AuthorityInformationAccess({'value': {'ocsp': ['https://example.com']}})
        self.assertEqual(ext.issuers, [])
        self.assertEqual(ext.ocsp, [uri('https://example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x3)

        ext = AuthorityInformationAccess({'value': {'issuers': [uri('https://example.com')]}})
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x2)

        ext = AuthorityInformationAccess({'value': {'ocsp': [uri('https://example.com')]}})
        self.assertEqual(ext.ocsp, [uri('https://example.com')])
        self.assertEqual(ext.issuers, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x3)

        ext = AuthorityInformationAccess({'value': {
            'issuers': ['https://example.com'],
            'ocsp': ['https://example.net', 'https://example.org']
        }})
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [uri('https://example.net'), uri('https://example.org')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x4)

    def test_from_extension(self):
        ext = AuthorityInformationAccess(self.x2)
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x2)

        ext = AuthorityInformationAccess(self.x3)
        self.assertEqual(ext.issuers, [])
        self.assertEqual(ext.ocsp, [uri('https://example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x3)

        ext = AuthorityInformationAccess(self.x4)
        self.assertEqual(ext.issuers, [uri('https://example.com')])
        self.assertEqual(ext.ocsp, [uri('https://example.net'), uri('https://example.org')])
        self.assertFalse(ext.critical)
        self.assertEqual(ext.as_extension(), self.x4)

    def test_empty_value(self):
        for val in [self.x1, [[], []], {}, {'issuers': [], 'ocsp': []}]:
            ext = AuthorityInformationAccess(val)
            self.assertEqual(ext.ocsp, [], val)
            self.assertEqual(ext.issuers, [], val)
            self.assertFalse(ext.critical)
            self.assertEqual(ext.as_extension(), self.x1)

    def test_unsupported(self):
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type NoneType$'):
            AuthorityInformationAccess(None)
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type bool$'):
            AuthorityInformationAccess(False)
        with self.assertRaises(NotImplementedError):
            AuthorityInformationAccess('')

    def test_bool(self):
        self.assertEqual(bool(AuthorityInformationAccess(self.x1)), False)
        self.assertEqual(bool(AuthorityInformationAccess([[], []])), False)
        self.assertEqual(bool(AuthorityInformationAccess(self.x1)), False)

        self.assertEqual(bool(AuthorityInformationAccess(self.x2)), True)
        self.assertEqual(bool(AuthorityInformationAccess(self.x3)), True)
        self.assertEqual(bool(AuthorityInformationAccess(self.x4)), True)

    def test_str(self):  # various methods converting to str
        self.assertEqual(repr(AuthorityInformationAccess(self.x1)),
                         '<AuthorityInformationAccess: issuers=[], ocsp=[], critical=False>')
        self.assertEqual(str(AuthorityInformationAccess(self.x1)),
                         'AuthorityInformationAccess(issuers=[], ocsp=[], critical=False)')
        self.assertEqual(
            str(AuthorityInformationAccess(self.x2)),
            "AuthorityInformationAccess(issuers=['URI:https://example.com'], ocsp=[], critical=False)")
        self.assertEqual(
            str(AuthorityInformationAccess(self.x3)),
            "AuthorityInformationAccess(issuers=[], ocsp=['URI:https://example.com'], critical=False)")
        self.assertEqual(
            str(AuthorityInformationAccess(self.x4)),
            "AuthorityInformationAccess(issuers=['URI:https://example.com'], ocsp=['URI:https://example.net', 'URI:https://example.org'], critical=False)") # NOQA

        self.assertEqual(AuthorityInformationAccess(self.x1).as_text(), "")
        self.assertEqual(
            AuthorityInformationAccess(self.x2).as_text(),
            "CA Issuers:\n  * URI:https://example.com\n")
        self.assertEqual(
            AuthorityInformationAccess(self.x3).as_text(),
            "OCSP:\n  * URI:https://example.com\n")
        self.assertEqual(
            AuthorityInformationAccess(self.x4).as_text(),
            "CA Issuers:\n  * URI:https://example.com\nOCSP:\n  * URI:https://example.net\n  * URI:https://example.org\n")  # NOQA


class AuthorityKeyIdentifierTestCase(ExtensionTestMixin, TestCase):
    ext_class = AuthorityKeyIdentifier

    hex1 = '33:33:33:33:33:33'
    hex2 = '44:44:44:44:44:44'
    hex3 = '55:55:55:55:55:55'

    b1 = b'333333'
    b2 = b'DDDDDD'
    b3 = b'UUUUUU'

    x1 = x509.Extension(
        oid=x509.ExtensionOID.AUTHORITY_KEY_IDENTIFIER, critical=False,
        value=x509.AuthorityKeyIdentifier(b1, None, None))
    x2 = x509.Extension(
        oid=x509.ExtensionOID.AUTHORITY_KEY_IDENTIFIER, critical=False,
        value=x509.AuthorityKeyIdentifier(b2, None, None))
    x3 = x509.Extension(
        oid=x509.ExtensionOID.AUTHORITY_KEY_IDENTIFIER, critical=True,
        value=x509.AuthorityKeyIdentifier(b3, None, None)
    )
    xs = [x1, x2, x3]

    def setUp(self):
        super(AuthorityKeyIdentifierTestCase, self).setUp()
        self.ext1 = AuthorityKeyIdentifier(self.x1)
        self.ext2 = AuthorityKeyIdentifier(self.x2)
        self.ext3 = AuthorityKeyIdentifier(self.x3)
        self.exts = [self.ext1, self.ext2, self.ext3]

    def test_as_text(self):
        self.assertEqual(self.ext1.as_text(), 'keyid:%s' % self.hex1)
        self.assertEqual(self.ext2.as_text(), 'keyid:%s' % self.hex2)
        self.assertEqual(self.ext3.as_text(), 'keyid:%s' % self.hex3)

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))
        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext3, AuthorityKeyIdentifier(self.hex3))  # ext3 is critical

    def test_repr(self):
        if six.PY2:  # pragma: only py2
            self.assertEqual(repr(self.ext1), '<AuthorityKeyIdentifier: 333333, critical=False>')
            self.assertEqual(repr(self.ext2), '<AuthorityKeyIdentifier: DDDDDD, critical=False>')
            self.assertEqual(repr(self.ext3), '<AuthorityKeyIdentifier: UUUUUU, critical=True>')
        else:
            self.assertEqual(repr(self.ext1), '<AuthorityKeyIdentifier: b\'333333\', critical=False>')
            self.assertEqual(repr(self.ext2), '<AuthorityKeyIdentifier: b\'DDDDDD\', critical=False>')
            self.assertEqual(repr(self.ext3), '<AuthorityKeyIdentifier: b\'UUUUUU\', critical=True>')

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': self.hex1})
        self.assertEqual(self.ext2.serialize(), {'critical': False, 'value': self.hex2})
        self.assertEqual(self.ext3.serialize(), {'critical': True, 'value': self.hex3})
        self.assertEqual(self.ext1.serialize(), AuthorityKeyIdentifier(self.hex1).serialize())
        self.assertNotEqual(self.ext1.serialize(), self.ext2.serialize())

    def test_str(self):
        ext = AuthorityKeyIdentifier(self.hex1)
        self.assertEqual(str(ext), 'keyid:%s' % self.hex1)

    @unittest.skipUnless(six.PY3, 'bytes only work in python3')
    def test_from_bytes(self):
        ext = AuthorityKeyIdentifier(self.b1)
        self.assertEqual(ext.as_text(), 'keyid:%s' % self.hex1)
        self.assertEqual(ext.as_extension(), self.x1)

    def test_subject_key_identifier(self):
        ski = SubjectKeyIdentifier(self.hex1)
        ext = AuthorityKeyIdentifier(ski)
        self.assertEqual(ext.as_text(), 'keyid:%s' % self.hex1)
        self.assertEqual(ext.extension_type.key_identifier, self.x1.value.key_identifier)

    def test_error(self):
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type NoneType$'):
            AuthorityKeyIdentifier(None)
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type bool$'):
            AuthorityKeyIdentifier(False)


class BasicConstraintsTestCase(ExtensionTestMixin, TestCase):
    ext_class = BasicConstraints

    x1 = x509.Extension(
        oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=True,
        value=x509.BasicConstraints(ca=False, path_length=None)
    )
    x2 = x509.Extension(
        oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=True,
        value=x509.BasicConstraints(ca=True, path_length=None)
    )
    x3 = x509.Extension(
        oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=True,
        value=x509.BasicConstraints(ca=True, path_length=0)
    )
    x4 = x509.Extension(
        oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=True,
        value=x509.BasicConstraints(ca=True, path_length=3)
    )
    # NOTE: Very unusual, BC is normally marked as critical
    x5 = x509.Extension(
        oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=False,
        value=x509.BasicConstraints(ca=False, path_length=None)
    )
    xs = [x1, x2, x3, x4, x5]

    def setUp(self):
        super(BasicConstraintsTestCase, self).setUp()
        self.ext1 = BasicConstraints({'value': {'ca': False}})
        self.ext2 = BasicConstraints({'value': {'ca': True}})
        self.ext3 = BasicConstraints({'value': {'ca': True, 'pathlen': 0}})
        self.ext4 = BasicConstraints({'value': {'ca': True, 'pathlen': 3}})
        self.ext5 = BasicConstraints({'value': {'ca': False}, 'critical': False})
        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4, self.ext5]

    def assertBC(self, bc, ca, pathlen, critical=True):
        self.assertEqual(bc.ca, ca)
        self.assertEqual(bc.pathlen, pathlen)
        self.assertEqual(bc.critical, critical)
        self.assertEqual(bc.value, (ca, pathlen))

    def test_as_text(self):
        self.assertEqual(BasicConstraints('CA=true').as_text(), 'CA:TRUE')
        self.assertEqual(BasicConstraints('CA= true , pathlen = 3').as_text(), 'CA:TRUE, pathlen:3')
        self.assertEqual(BasicConstraints('CA = FALSE').as_text(), 'CA:FALSE')

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))
        self.assertEqual(hash(self.ext4), hash(self.ext4))
        self.assertEqual(hash(self.ext5), hash(self.ext5))

        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext1, self.ext4)
        self.assertNotEqual(self.ext1, self.ext5)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext2, self.ext4)
        self.assertNotEqual(self.ext2, self.ext5)
        self.assertNotEqual(self.ext3, self.ext4)
        self.assertNotEqual(self.ext3, self.ext5)
        self.assertNotEqual(self.ext4, self.ext5)

    def test_repr(self):
        self.assertEqual(repr(self.ext1), "<BasicConstraints: 'CA:FALSE', critical=True>")
        self.assertEqual(repr(self.ext2), "<BasicConstraints: 'CA:TRUE', critical=True>")
        self.assertEqual(repr(self.ext3), "<BasicConstraints: 'CA:TRUE, pathlen:0', critical=True>")
        self.assertEqual(repr(self.ext4), "<BasicConstraints: 'CA:TRUE, pathlen:3', critical=True>")
        self.assertEqual(repr(self.ext5), "<BasicConstraints: 'CA:FALSE', critical=False>")

    def test_str(self):
        self.assertEqual(str(self.ext1), "CA:FALSE/critical")
        self.assertEqual(str(self.ext2), "CA:TRUE/critical")
        self.assertEqual(str(self.ext3), "CA:TRUE, pathlen:0/critical")
        self.assertEqual(str(self.ext4), "CA:TRUE, pathlen:3/critical")
        self.assertEqual(str(self.ext5), "CA:FALSE")

    # Old functions

    def test_from_extension(self):
        self.assertBC(BasicConstraints(x509.Extension(
            oid=x509.ExtensionOID.BASIC_CONSTRAINTS, critical=True,
            value=x509.BasicConstraints(ca=True, path_length=3))), True, 3, True)

    def test_dict(self):
        self.assertBC(BasicConstraints({'value': {'ca': True}}), True, None, True)
        self.assertBC(BasicConstraints({'value': {'ca': False}}), False, None, True)
        self.assertBC(BasicConstraints({'value': {'ca': True, 'pathlen': 3}}), True, 3, True)
        self.assertBC(BasicConstraints({'value': {'ca': True, 'pathlen': None}}), True, None, True)
        self.assertBC(BasicConstraints({'value': {'ca': True}, 'critical': False}), True, None, False)

    def test_consistency(self):
        # pathlen must be None if CA=False
        with self.assertRaisesRegex(ValueError, r'^pathlen must be None when ca is False$'):
            BasicConstraints('CA:FALSE, pathlen=3')

    def test_other(self):
        # test without pathlen
        self.assertBC(BasicConstraints('CA:FALSE'), False, None, False)
        self.assertBC(BasicConstraints('CA : FAlse '), False, None, False)
        self.assertBC(BasicConstraints('CA: true'), True, None, False)
        self.assertBC(BasicConstraints('CA=true'), True, None, False)

        # test adding a pathlen
        self.assertBC(BasicConstraints('CA:TRUE,pathlen=0'), True, 0, False)
        self.assertBC(BasicConstraints('CA:trUe,pathlen:1'), True, 1, False)
        self.assertBC(BasicConstraints('CA: true , pathlen = 2 '), True, 2, False)

        with self.assertRaisesRegex(ValueError, r'^Could not parse pathlen: pathlen=foo$'):
            BasicConstraints('CA:FALSE, pathlen=foo')

        with self.assertRaisesRegex(ValueError, r'^Could not parse pathlen: pathlen=$'):
            BasicConstraints('CA:FALSE, pathlen=')

        with self.assertRaisesRegex(ValueError, r'^Could not parse pathlen: foobar$'):
            BasicConstraints('CA:FALSE, foobar')

    def test_serialize(self):
        exts = [
            BasicConstraints({'value': {'ca': True}}),
            BasicConstraints({'value': {'ca': False}}),
            BasicConstraints({'value': {'ca': True, 'pathlen': 3}}),
            BasicConstraints({'value': {'ca': True, 'pathlen': None}}),
            BasicConstraints({'value': {'ca': True}, 'critical': False}),
        ]
        for ext in exts:
            self.assertEqual(BasicConstraints(ext.serialize()), ext)


class DistributionPointTestCase(TestCase):
    def test_init_basic(self):
        dp = DistributionPoint({})
        self.assertIsNone(dp.full_name)
        self.assertIsNone(dp.relative_name)
        self.assertIsNone(dp.crl_issuer)
        self.assertIsNone(dp.reasons)

        dp = DistributionPoint({
            'full_name': ['http://example.com'],
            'crl_issuer': ['http://example.net'],
        })
        self.assertEqual(dp.full_name, [uri('http://example.com')])
        self.assertIsNone(dp.relative_name)
        self.assertEqual(dp.crl_issuer, [uri('http://example.net')])
        self.assertIsNone(dp.reasons)

        dp = DistributionPoint({
            'full_name': 'http://example.com',
            'crl_issuer': 'http://example.net',
        })
        self.assertEqual(dp.full_name, [uri('http://example.com')])
        self.assertIsNone(dp.relative_name)
        self.assertEqual(dp.crl_issuer, [uri('http://example.net')])
        self.assertIsNone(dp.reasons)

    def test_init_errors(self):
        with self.assertRaisesRegex(ValueError, r'^data must be x509.DistributionPoint or dict$'):
            DistributionPoint('foobar')

        with self.assertRaisesRegex(ValueError, r'^full_name and relative_name cannot both have a value$'):
            DistributionPoint({
                'full_name': ['http://example.com'],
                'relative_name': '/CN=example.com',
            })


class CRLDistributionPointsTestCase(ListExtensionTestMixin, TestCase):
    ext_class = CRLDistributionPoints

    dp1 = x509.DistributionPoint(
        full_name=[
            x509.UniformResourceIdentifier('http://ca.example.com/crl'),
        ],
        relative_name=None,
        crl_issuer=None,
        reasons=None
    )
    dp2 = x509.DistributionPoint(
        full_name=[
            x509.UniformResourceIdentifier('http://ca.example.com/crl'),
            x509.DirectoryName(x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, u"AT")])),
        ],
        relative_name=None,
        crl_issuer=None,
        reasons=None
    )
    dp3 = x509.DistributionPoint(
        full_name=None,
        relative_name=x509.RelativeDistinguishedName([
            x509.NameAttribute(NameOID.COMMON_NAME, u'example.com'),
        ]),
        crl_issuer=None,
        reasons=None
    )
    dp4 = x509.DistributionPoint(
        full_name=[
            x509.UniformResourceIdentifier('http://ca.example.com/crl'),
        ],
        relative_name=None,
        crl_issuer=[
            x509.UniformResourceIdentifier('http://ca.example.com/'),
        ],
        reasons=frozenset([x509.ReasonFlags.key_compromise, x509.ReasonFlags.ca_compromise])
    )

    # serialized versions of dps above
    s1 = {'full_name': ['URI:http://ca.example.com/crl']}
    s2 = {'full_name': ['URI:http://ca.example.com/crl', 'dirname:/C=AT']}
    s3 = {'relative_name': '/CN=example.com'}
    s4 = {
        'full_name': ['URI:http://ca.example.com/crl'],
        'crl_issuer': ['URI:http://ca.example.com/'],
        'reasons': ['ca_compromise', 'key_compromise'],
    }

    # cryptography extensions
    x1 = x509.Extension(oid=ExtensionOID.CRL_DISTRIBUTION_POINTS, critical=False,
                        value=x509.CRLDistributionPoints([dp1]))
    x2 = x509.Extension(oid=ExtensionOID.CRL_DISTRIBUTION_POINTS, critical=False,
                        value=x509.CRLDistributionPoints([dp2]))
    x3 = x509.Extension(oid=ExtensionOID.CRL_DISTRIBUTION_POINTS, critical=False,
                        value=x509.CRLDistributionPoints([dp3]))
    x4 = x509.Extension(oid=ExtensionOID.CRL_DISTRIBUTION_POINTS, critical=False,
                        value=x509.CRLDistributionPoints([dp4]))
    x5 = x509.Extension(oid=ExtensionOID.CRL_DISTRIBUTION_POINTS, critical=True,
                        value=x509.CRLDistributionPoints([dp2, dp4]))
    xs = [x1, x2, x3, x4, x5]

    def setUp(self):
        super(CRLDistributionPointsTestCase, self).setUp()
        # django_ca extensions
        self.ext1 = CRLDistributionPoints(self.x1)
        self.ext2 = CRLDistributionPoints(self.x2)
        self.ext3 = CRLDistributionPoints(self.x3)
        self.ext4 = CRLDistributionPoints(self.x4)
        self.ext5 = CRLDistributionPoints(self.x5)
        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4, self.ext5]

    def test_as_text(self):
        self.assertEqual(self.ext1.as_text(), """* DistributionPoint:
  * Full Name:
    * URI:http://ca.example.com/crl""")
        self.assertEqual(self.ext2.as_text(), """* DistributionPoint:
  * Full Name:
    * URI:http://ca.example.com/crl
    * dirname:/C=AT""")
        self.assertEqual(self.ext3.as_text(), """* DistributionPoint:
  * Relative Name: /CN=example.com""")
        self.assertEqual(self.ext4.as_text(), """* DistributionPoint:
  * Full Name:
    * URI:http://ca.example.com/crl
  * CRL Issuer:
    * URI:http://ca.example.com/
  * Reasons: ca_compromise, key_compromise""")
        self.assertEqual(self.ext5.as_text(), """* DistributionPoint:
  * Full Name:
    * URI:http://ca.example.com/crl
    * dirname:/C=AT
* DistributionPoint:
  * Full Name:
    * URI:http://ca.example.com/crl
  * CRL Issuer:
    * URI:http://ca.example.com/
  * Reasons: ca_compromise, key_compromise""")

    def test_count(self):
        self.assertEqual(self.ext1.count(self.s1), 1)
        self.assertEqual(self.ext1.count(self.dp1), 1)
        self.assertEqual(self.ext1.count(DistributionPoint(self.s1)), 1)
        self.assertEqual(self.ext1.count(self.s2), 0)
        self.assertEqual(self.ext1.count(self.dp2), 0)
        self.assertEqual(self.ext1.count(DistributionPoint(self.s2)), 0)
        self.assertEqual(self.ext5.count(self.s2), 1)
        self.assertEqual(self.ext5.count(self.dp2), 1)
        self.assertEqual(self.ext5.count(DistributionPoint(self.s2)), 1)
        self.assertEqual(self.ext5.count(self.s4), 1)
        self.assertEqual(self.ext5.count(self.dp4), 1)
        self.assertEqual(self.ext5.count(DistributionPoint(self.s4)), 1)
        self.assertEqual(self.ext5.count(self.s3), 0)
        self.assertEqual(self.ext5.count(self.dp3), 0)
        self.assertEqual(self.ext5.count(DistributionPoint(self.s3)), 0)
        self.assertEqual(self.ext5.count(None), 0)

    def test_del(self):
        self.assertIn(self.dp1, self.ext1)
        del self.ext1[0]
        self.assertNotIn(self.dp1, self.ext1)
        self.assertEqual(len(self.ext1), 0)

        self.assertIn(self.dp2, self.ext5)
        self.assertIn(self.dp4, self.ext5)
        del self.ext5[1]
        self.assertIn(self.dp2, self.ext5)
        self.assertNotIn(self.dp4, self.ext5)
        self.assertEqual(len(self.ext5), 1)

        self.assertEqual(len(self.ext4), 1)
        with self.assertRaisesRegex(IndexError, '^list assignment index out of range$'):
            del self.ext4[1]
        self.assertEqual(len(self.ext4), 1)

    def test_extend(self):
        self.ext1.extend([self.s2])
        self.assertEqual(self.ext1, CRLDistributionPoints([
            DistributionPoint(self.dp1), DistributionPoint(self.dp2)]))
        self.ext1.extend([self.dp3])
        self.assertEqual(self.ext1, CRLDistributionPoints([
            DistributionPoint(self.dp1), DistributionPoint(self.dp2), DistributionPoint(self.dp3),
        ]))
        self.ext1.extend([DistributionPoint(self.dp4)])
        self.assertEqual(self.ext1, CRLDistributionPoints([
            DistributionPoint(self.dp1), DistributionPoint(self.dp2), DistributionPoint(self.dp3),
            DistributionPoint(self.dp4),
        ]))

    def test_from_list(self):
        self.assertEqual(self.ext1, CRLDistributionPoints([DistributionPoint(self.dp1)]))
        self.assertEqual(self.ext2, CRLDistributionPoints([DistributionPoint(self.dp2)]))
        self.assertEqual(self.ext3, CRLDistributionPoints([DistributionPoint(self.dp3)]))
        self.assertEqual(self.ext4, CRLDistributionPoints([DistributionPoint(self.dp4)]))

    def test_getitem(self):
        self.assertEqual(self.ext1[0], DistributionPoint(self.dp1))
        self.assertEqual(self.ext2[0], DistributionPoint(self.dp2))
        self.assertEqual(self.ext5[0], DistributionPoint(self.dp2))
        self.assertEqual(self.ext5[1], DistributionPoint(self.dp4))

        with self.assertRaisesRegex(IndexError, '^list index out of range$'):
            self.ext5[2]

    def test_getitem_slices(self):
        self.assertEqual(self.ext1[0:], [DistributionPoint(self.dp1)])
        self.assertEqual(self.ext1[1:], [])
        self.assertEqual(self.ext1[2:], [])
        self.assertEqual(self.ext5[0:], [DistributionPoint(self.dp2), DistributionPoint(self.dp4)])

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))
        self.assertEqual(hash(self.ext4), hash(self.ext4))
        self.assertEqual(hash(self.ext5), hash(self.ext5))

        self.assertEqual(hash(self.ext1), hash(CRLDistributionPoints(self.x1)))
        self.assertEqual(hash(self.ext2), hash(CRLDistributionPoints(self.x2)))
        self.assertEqual(hash(self.ext3), hash(CRLDistributionPoints(self.x3)))
        self.assertEqual(hash(self.ext4), hash(CRLDistributionPoints(self.x4)))
        self.assertEqual(hash(self.ext5), hash(CRLDistributionPoints(self.x5)))

        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext1), hash(self.ext4))
        self.assertNotEqual(hash(self.ext1), hash(self.ext5))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext4))
        self.assertNotEqual(hash(self.ext2), hash(self.ext5))
        self.assertNotEqual(hash(self.ext3), hash(self.ext4))
        self.assertNotEqual(hash(self.ext3), hash(self.ext5))

    def test_in(self):
        self.assertIn(self.s1, self.ext1)
        self.assertIn(self.s2, self.ext2)
        self.assertIn(self.s3, self.ext3)
        self.assertIn(self.s4, self.ext4)
        self.assertIn(self.s2, self.ext5)
        self.assertIn(self.s4, self.ext5)

        self.assertIn(self.dp1, self.ext1)
        self.assertIn(self.dp2, self.ext2)
        self.assertIn(self.dp3, self.ext3)
        self.assertIn(self.dp4, self.ext4)
        self.assertIn(self.dp2, self.ext5)
        self.assertIn(self.dp4, self.ext5)

    def test_insert(self):
        self.ext1.insert(0, self.dp2)
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.s2, self.s1]})
        self.ext1.insert(1, self.s3)
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.s2, self.s3, self.s1]})

    def test_len(self):
        self.assertEqual(len(self.ext1), 1)
        self.assertEqual(len(self.ext2), 1)
        self.assertEqual(len(self.ext3), 1)
        self.assertEqual(len(self.ext4), 1)
        self.assertEqual(len(self.ext5), 2)

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext3, self.ext4)
        self.assertNotEqual(self.ext4, self.ext5)
        self.assertNotEqual(self.ext1, self.ext5)

    def test_not_in(self):
        self.assertNotIn(self.s2, self.ext1)
        self.assertNotIn(self.s3, self.ext2)
        self.assertNotIn(self.dp2, self.ext1)
        self.assertNotIn(self.dp3, self.ext4)

    def test_pop(self):
        ext = CRLDistributionPoints({'value': [self.dp1, self.dp2, self.dp3]})
        self.assertEqual(ext.pop(), DistributionPoint(self.dp3))
        self.assertEqual(ext.serialize(), {'critical': False, 'value': [self.s1, self.s2]})

        self.assertEqual(ext.pop(0), DistributionPoint(self.dp1))
        self.assertEqual(ext.serialize(), {'critical': False, 'value': [self.s2]})

        with self.assertRaisesRegex(IndexError, '^pop index out of range'):
            ext.pop(3)

    def test_remove(self):
        ext = CRLDistributionPoints({'value': [self.dp1, self.dp2, self.dp3]})
        self.assertEqual(ext.serialize(), {'critical': False, 'value': [self.s1, self.s2, self.s3]})

        ext.remove(self.dp2)
        self.assertEqual(ext.serialize(), {'critical': False, 'value': [self.s1, self.s3]})

        ext.remove(self.s3)
        self.assertEqual(ext.serialize(), {'critical': False, 'value': [self.s1]})

    def test_repr(self):
        if six.PY3:
            self.assertEqual(
                repr(self.ext1),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=['URI:http://ca.example.com/crl']>], "
                "critical=False>"
            )
            self.assertEqual(
                repr(self.ext2),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=['URI:http://ca.example.com/crl', "
                "'dirname:/C=AT']>], critical=False>"
            )
            self.assertEqual(
                repr(self.ext3),
                "<CRLDistributionPoints: [<DistributionPoint: relative_name='/CN=example.com'>], "
                "critical=False>"
            )
            self.assertEqual(
                repr(self.ext4),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=['URI:http://ca.example.com/crl'], "
                "crl_issuer=['URI:http://ca.example.com/'], reasons=['ca_compromise', 'key_compromise']>], "
                "critical=False>"
            )
            self.assertEqual(
                repr(self.ext5),
                "<CRLDistributionPoints: ["
                "<DistributionPoint: full_name=['URI:http://ca.example.com/crl', 'dirname:/C=AT']>, "
                "<DistributionPoint: full_name=['URI:http://ca.example.com/crl'], "
                "crl_issuer=['URI:http://ca.example.com/'], reasons=['ca_compromise', 'key_compromise']>], "
                "critical=True>"
            )
        else:  # pragma: only py2
            self.assertEqual(
                repr(self.ext1),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=[u'URI:http://ca.example.com/crl']>],"
                " critical=False>"
            )
            self.assertEqual(
                repr(self.ext2),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=[u'URI:http://ca.example.com/crl', "
                "u'dirname:/C=AT']>], critical=False>"
            )
            self.assertEqual(
                repr(self.ext3),
                "<CRLDistributionPoints: [<DistributionPoint: relative_name='/CN=example.com'>], "
                "critical=False>"
            )
            self.assertEqual(
                repr(self.ext4),
                "<CRLDistributionPoints: [<DistributionPoint: full_name=[u'URI:http://ca.example.com/crl'], "
                "crl_issuer=[u'URI:http://ca.example.com/'], "
                "reasons=['ca_compromise', 'key_compromise']>], critical=False>"
            )
            self.assertEqual(
                repr(self.ext5),
                "<CRLDistributionPoints: [<DistributionPoint: "
                "full_name=[u'URI:http://ca.example.com/crl', u'dirname:/C=AT']>, "
                "<DistributionPoint: full_name=[u'URI:http://ca.example.com/crl'], "
                "crl_issuer=[u'URI:http://ca.example.com/'], reasons=['ca_compromise', 'key_compromise']>], "
                "critical=True>"
            )

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.s1]})
        self.assertEqual(self.ext2.serialize(), {'critical': False, 'value': [self.s2]})
        self.assertEqual(self.ext3.serialize(), {'critical': False, 'value': [self.s3]})
        self.assertEqual(self.ext4.serialize(), {'critical': False, 'value': [self.s4]})
        self.assertEqual(self.ext5.serialize(), {'critical': True, 'value': [self.s2, self.s4]})

    def test_setitem(self):
        self.ext1[0] = self.s2
        self.assertEqual(self.ext1, self.ext2)
        self.ext1[0] = self.s3
        self.assertEqual(self.ext1, self.ext3)
        self.ext1[0] = self.dp4
        self.assertEqual(self.ext1, self.ext4)

        with self.assertRaisesRegex(IndexError, r'^list assignment index out of range$'):
            self.ext1[1] = self.dp4

    def test_setitem_slices(self):
        expected = CRLDistributionPoints({'value': [self.dp1, self.dp2, self.dp3]})
        self.ext1[1:] = [self.dp2, self.dp3]
        self.assertEqual(self.ext1, expected)
        self.ext1[1:] = [self.s2, self.s3]
        self.assertEqual(self.ext1, expected)

    def test_str(self):
        if six.PY3:
            self.assertEqual(
                str(self.ext1),
                "CRLDistributionPoints([DistributionPoint(full_name=['URI:http://ca.example.com/crl'])], "
                "critical=False)"
            )
            self.assertEqual(
                str(self.ext2),
                "CRLDistributionPoints([DistributionPoint("
                "full_name=['URI:http://ca.example.com/crl', 'dirname:/C=AT'])], critical=False)"
            )
            self.assertEqual(
                str(self.ext3),
                "CRLDistributionPoints([DistributionPoint(relative_name='/CN=example.com')], critical=False)"
            )
            self.assertEqual(
                str(self.ext4),
                "CRLDistributionPoints([DistributionPoint(full_name=['URI:http://ca.example.com/crl'], "
                "crl_issuer=['URI:http://ca.example.com/'], reasons=['ca_compromise', 'key_compromise'])], "
                "critical=False)"
            )
            self.assertEqual(
                str(self.ext5),
                "CRLDistributionPoints([DistributionPoint("
                "full_name=['URI:http://ca.example.com/crl', 'dirname:/C=AT']), "
                "DistributionPoint(full_name=['URI:http://ca.example.com/crl'], "
                "crl_issuer=['URI:http://ca.example.com/'], "
                "reasons=['ca_compromise', 'key_compromise'])], critical=True)"
            )
        else:  # pragma: only py2
            self.assertEqual(
                str(self.ext1),
                "CRLDistributionPoints([DistributionPoint(full_name=[u'URI:http://ca.example.com/crl'])], "
                "critical=False)"
            )
            self.assertEqual(
                str(self.ext2),
                "CRLDistributionPoints([DistributionPoint("
                "full_name=[u'URI:http://ca.example.com/crl', u'dirname:/C=AT'])], critical=False)"
            )
            self.assertEqual(
                str(self.ext3),
                "CRLDistributionPoints([DistributionPoint(relative_name='/CN=example.com')], critical=False)"
            )
            self.assertEqual(
                str(self.ext4),
                "CRLDistributionPoints([DistributionPoint(full_name=[u'URI:http://ca.example.com/crl'], "
                "crl_issuer=[u'URI:http://ca.example.com/'], "
                "reasons=['ca_compromise', 'key_compromise'])], critical=False)"
            )
            self.assertEqual(
                str(self.ext5),
                "CRLDistributionPoints([DistributionPoint("
                "full_name=[u'URI:http://ca.example.com/crl', u'dirname:/C=AT']), "
                "DistributionPoint(full_name=[u'URI:http://ca.example.com/crl'], "
                "crl_issuer=[u'URI:http://ca.example.com/'], "
                "reasons=['ca_compromise', 'key_compromise'])], critical=True)"
            )


class PolicyInformationTestCase(DjangoCATestCase):
    oid = '2.5.29.32.0'

    # various qualifiers
    q1 = 'text1'
    q2 = x509.UserNotice(explicit_text='text2', notice_reference=None)
    q3 = x509.UserNotice(
        explicit_text=None,
        notice_reference=x509.NoticeReference(organization='text3', notice_numbers=[1])
    )
    q4 = 'text4'
    q5 = x509.UserNotice(
        explicit_text='text5',
        notice_reference=x509.NoticeReference(organization='text6', notice_numbers=[1, 2, 3])
    )

    x1 = x509.PolicyInformation(policy_identifier=ObjectIdentifier(oid),
                                policy_qualifiers=[q1])
    x2 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q2],
    )
    x3 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q3],
    )
    x4 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q4, q5],
    )
    s1 = {
        'policy_identifier': oid,
        'policy_qualifiers': ['text1'],
    }
    s2 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            {'explicit_text': 'text2', }
        ],
    }
    s3 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            {
                'notice_reference': {
                    'organization': 'text3',
                    'notice_numbers': [1, ],
                }
            }
        ],
    }
    s4 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            'text4',
            {
                'explicit_text': 'text5',
                'notice_reference': {
                    'organization': 'text6',
                    'notice_numbers': [1, 2, 3],
                }
            }
        ],
    }

    def setUp(self):
        super(PolicyInformationTestCase, self).setUp()

        self.pi1 = PolicyInformation(self.s1)
        self.pi2 = PolicyInformation(self.s2)
        self.pi3 = PolicyInformation(self.s3)
        self.pi4 = PolicyInformation(self.s4)
        self.pi_empty = PolicyInformation()

    def test_append(self):
        self.pi1.append(self.q2)
        self.pi1.append(self.s3['policy_qualifiers'][0])
        self.assertEqual(self.pi1, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q1, self.q2, self.q3],
        }))

        self.pi_empty.policy_identifier = self.oid
        self.pi_empty.append(self.q3)
        self.assertEqual(self.pi3, self.pi_empty)

    def test_as_text(self):
        self.assertEqual(self.pi1.as_text(), 'Policy Identifier: 2.5.29.32.0\n'
                                             'Policy Qualifiers:\n* text1')
        self.assertEqual(self.pi2.as_text(), 'Policy Identifier: 2.5.29.32.0\n'
                                             'Policy Qualifiers:\n'
                                             '* UserNotice:\n'
                                             '  * Explicit text: text2')
        self.assertEqual(self.pi3.as_text(),
                         'Policy Identifier: 2.5.29.32.0\n'
                         'Policy Qualifiers:\n'
                         '* UserNotice:\n'
                         '  * Reference:\n'
                         '    * Organiziation: text3\n'
                         '    * Notice Numbers: [1]')
        self.assertEqual(self.pi4.as_text(),
                         'Policy Identifier: 2.5.29.32.0\n'
                         'Policy Qualifiers:\n'
                         '* text4\n'
                         '* UserNotice:\n'
                         '  * Explicit text: text5\n'
                         '  * Reference:\n'
                         '    * Organiziation: text6\n'
                         '    * Notice Numbers: [1, 2, 3]')
        self.assertEqual(self.pi_empty.as_text(), 'Policy Identifier: None\nNo Policy Qualifiers')

        self.load_all_cas()
        self.load_all_certs()
        for name, cert in list(self.cas.items()) + list(self.certs.items()):
            try:
                ext = cert.x509.extensions.get_extension_for_oid(ExtensionOID.CERTIFICATE_POLICIES).value
            except x509.ExtensionNotFound:
                continue

            for index, policy in enumerate(ext):
                pi = PolicyInformation(policy)
                self.assertEqual(pi.as_text(), certs[name]['policy_texts'][index])

    def test_certs(self):
        self.load_all_cas()
        self.load_all_certs()
        for name, cert in list(self.cas.items()) + list(self.certs.items()):
            try:
                val = cert.x509.extensions.get_extension_for_oid(ExtensionOID.CERTIFICATE_POLICIES).value
            except x509.ExtensionNotFound:
                continue

            for policy in val:
                pi = PolicyInformation(policy)
                self.assertEqual(pi.for_extension_type, policy)

                # pass the serialized value to the constructor and see if it's still the same
                pi2 = PolicyInformation(pi.serialize())
                self.assertEqual(pi, pi2)
                self.assertEqual(pi.serialize(), pi2.serialize())
                self.assertEqual(pi2.for_extension_type, policy)

    def test_clear(self):
        self.pi1.clear()
        self.assertIsNone(self.pi1.policy_qualifiers)

    def test_constructor(self):
        # just some constructors that are otherwise not called
        pi = PolicyInformation()
        self.assertIsNone(pi.policy_identifier)
        self.assertIsNone(pi.policy_qualifiers)

        pi = PolicyInformation({
            'policy_identifier': '1.2.3',
            'policy_qualifiers': [
                x509.UserNotice(notice_reference=None, explicit_text='foobar'),
            ],
        })
        # todo: test pi

        pi = PolicyInformation({
            'policy_identifier': '1.2.3',
            'policy_qualifiers': [{
                'notice_reference': x509.NoticeReference(organization='foobar', notice_numbers=[1]),
            }],
        })
        # todo: test pi

    def test_constructor_errors(self):
        with self.assertRaisesRegex(
                ValueError, r'^PolicyInformation data must be either x509.PolicyInformation or dict$'):
            PolicyInformation(True)

        with self.assertRaisesRegex(ValueError, r'^PolicyQualifier must be string, dict or x509.UserNotice$'):
            PolicyInformation({'policy_identifier': '1.2.3', 'policy_qualifiers': [True]})

        with self.assertRaisesRegex(
                ValueError, r'^NoticeReference must be either None, a dict or an x509.NoticeReference$'):
            PolicyInformation({'policy_identifier': '1.2.3', 'policy_qualifiers': [{
                'notice_reference': True,
            }]})

    def test_contains(self):
        self.assertIn(self.q1, self.pi1)
        self.assertIn(self.q2, self.pi2)
        self.assertIn(self.q3, self.pi3)
        self.assertIn(self.q4, self.pi4)
        self.assertIn(self.q5, self.pi4)
        self.assertIn(self.s1['policy_qualifiers'][0], self.pi1)
        self.assertIn(self.s2['policy_qualifiers'][0], self.pi2)
        self.assertIn(self.s3['policy_qualifiers'][0], self.pi3)
        self.assertIn(self.s4['policy_qualifiers'][0], self.pi4)
        self.assertIn(self.s4['policy_qualifiers'][1], self.pi4)

        self.assertNotIn(self.q2, self.pi1)
        self.assertNotIn(self.q1, self.pi_empty)
        self.assertNotIn(self.s1['policy_qualifiers'][0], self.pi2)
        self.assertNotIn(self.s2['policy_qualifiers'][0], self.pi1)
        self.assertNotIn(self.s2['policy_qualifiers'][0], self.pi_empty)

    def test_count(self):
        self.assertEqual(self.pi1.count(self.s1['policy_qualifiers'][0]), 1)
        self.assertEqual(self.pi1.count(self.q1), 1)
        self.assertEqual(self.pi1.count(self.s2), 0)
        self.assertEqual(self.pi1.count(self.q2), 0)
        self.assertEqual(self.pi_empty.count(self.q2), 0)

    def test_delitem(self):
        del self.pi1[0]
        self.pi_empty.policy_identifier = self.oid
        self.assertEqual(self.pi1, self.pi_empty)

        self.assertEqual(len(self.pi4), 2)
        del self.pi4[0]
        self.assertEqual(len(self.pi4), 1)

        with self.assertRaisesRegex(IndexError, r'^list assignment index out of range$'):
            del self.pi1[0]

    def test_extend(self):
        self.pi1.extend([self.q2, self.q4])
        self.assertEqual(self.pi1, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q1, self.q2, self.q4],
        }))

        self.pi2.extend([self.s1['policy_qualifiers'][0]])
        self.assertEqual(self.pi2, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q2, self.q1],
        }))

    def test_getitem(self):
        self.assertEqual(self.pi1[0], self.s1['policy_qualifiers'][0])
        self.assertEqual(self.pi4[0], self.s4['policy_qualifiers'][0])
        self.assertEqual(self.pi4[1], self.s4['policy_qualifiers'][1])
        self.assertEqual(self.pi4[1:], [self.s4['policy_qualifiers'][1]])

        with self.assertRaisesRegex(IndexError, r'^list index out of range$'):
            self.pi_empty[0]
        with self.assertRaisesRegex(IndexError, r'^list index out of range$'):
            self.pi_empty[2:]

    def test_hash(self):
        self.assertEqual(hash(self.pi1), hash(self.pi1))
        self.assertEqual(hash(self.pi2), hash(self.pi2))
        self.assertEqual(hash(self.pi3), hash(self.pi3))
        self.assertEqual(hash(self.pi4), hash(self.pi4))
        self.assertEqual(hash(self.pi_empty), hash(self.pi_empty))

        self.assertEqual(hash(self.pi1), hash(PolicyInformation(self.s1)))
        self.assertEqual(hash(self.pi2), hash(PolicyInformation(self.s2)))
        self.assertEqual(hash(self.pi3), hash(PolicyInformation(self.s3)))
        self.assertEqual(hash(self.pi4), hash(PolicyInformation(self.s4)))
        self.assertEqual(hash(self.pi_empty), hash(PolicyInformation()))

        self.assertNotEqual(hash(self.pi1), hash(self.pi2))
        self.assertNotEqual(hash(self.pi1), hash(self.pi3))
        self.assertNotEqual(hash(self.pi1), hash(self.pi4))
        self.assertNotEqual(hash(self.pi2), hash(self.pi3))
        self.assertNotEqual(hash(self.pi2), hash(self.pi4))
        self.assertNotEqual(hash(self.pi3), hash(self.pi4))

    def test_insert(self):
        self.pi1.insert(0, self.q2)
        self.assertEqual(self.pi1, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q2, self.q1],
        }))
        self.pi1.insert(1, self.s3['policy_qualifiers'][0])
        self.assertEqual(self.pi1, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q2, self.q3, self.q1],
        }))

        self.pi_empty.insert(1, self.q2)
        self.pi_empty.policy_identifier = self.oid
        self.assertEqual(self.pi2, self.pi_empty)

    def test_len(self):
        self.assertEqual(len(self.pi1), 1)
        self.assertEqual(len(self.pi2), 1)
        self.assertEqual(len(self.pi3), 1)
        self.assertEqual(len(self.pi4), 2)
        self.assertEqual(len(self.pi_empty), 0)

    def test_policy_identifier_setter(self):
        value = '1.2.3'
        expected = ObjectIdentifier(value)
        pi = PolicyInformation({'policy_identifier': value})
        pi.policy_identifier = value
        self.assertEqual(pi.policy_identifier, expected)

        pi = PolicyInformation({'policy_identifier': expected})
        self.assertEqual(pi.policy_identifier, expected)

        new_value = '2.3.4'
        new_expected = ObjectIdentifier(new_value)
        pi.policy_identifier = new_value
        self.assertEqual(pi.policy_identifier, new_expected)

    def test_pop(self):
        self.pi_empty.policy_identifier = self.oid
        self.assertEqual(self.pi1.pop(), self.s1['policy_qualifiers'][0])
        self.assertEqual(self.pi1, self.pi_empty)

        self.assertEqual(self.pi4.pop(1), self.s4['policy_qualifiers'][1])
        self.assertEqual(self.pi4, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q4],
        }))

        self.assertEqual(self.pi4.pop(), self.s4['policy_qualifiers'][0])
        self.assertEqual(self.pi4, self.pi_empty)

        with self.assertRaisesRegex(IndexError, r'^pop from empty list$'):
            self.pi_empty.pop()

    def test_remove(self):
        self.pi_empty.policy_identifier = self.oid
        self.pi1.remove(self.q1)
        self.assertEqual(self.pi1, self.pi_empty)

        self.pi2.remove(self.s2['policy_qualifiers'][0])
        self.assertEqual(self.pi1, self.pi_empty)

        self.pi4.remove(self.q4)
        self.assertEqual(self.pi4, PolicyInformation({
            'policy_identifier': self.oid,
            'policy_qualifiers': [self.q5],
        }))

        with self.assertRaisesRegex(ValueError, r'^list\.remove\(x\): x not in list$'):
            self.pi_empty.remove(self.s3['policy_qualifiers'][0])

    def test_repr(self):
        if six.PY2:  # pragma: only py2
            self.assertEqual(repr(self.pi1), "<PolicyInformation(oid=2.5.29.32.0, qualifiers=[u'text1'])>")
            self.assertEqual(
                repr(self.pi2),
                "<PolicyInformation(oid=2.5.29.32.0, qualifiers=[{u'explicit_text': u'text2'}])>")
            self.assertEqual(repr(self.pi_empty), "<PolicyInformation(oid=None, qualifiers=None)>")
        else:
            self.assertEqual(repr(self.pi1), "<PolicyInformation(oid=2.5.29.32.0, qualifiers=['text1'])>")
            self.assertEqual(repr(self.pi2),
                             "<PolicyInformation(oid=2.5.29.32.0, qualifiers=[{'explicit_text': 'text2'}])>")
            self.assertEqual(repr(self.pi_empty), "<PolicyInformation(oid=None, qualifiers=None)>")

        # NOTE: order of dict is different here, so we do not test output, just make sure there's no exception
        repr(self.pi3)
        repr(self.pi4)

    def test_str(self):
        self.assertEqual(str(self.pi1), 'PolicyInformation(oid=2.5.29.32.0, 1 qualifier)')
        self.assertEqual(str(self.pi2), 'PolicyInformation(oid=2.5.29.32.0, 1 qualifier)')
        self.assertEqual(str(self.pi3), 'PolicyInformation(oid=2.5.29.32.0, 1 qualifier)')
        self.assertEqual(str(self.pi4), 'PolicyInformation(oid=2.5.29.32.0, 2 qualifiers)')
        self.assertEqual(str(self.pi_empty), 'PolicyInformation(oid=None, 0 qualifiers)')


class CertificatePoliciesTestCase(ListExtensionTestMixin, TestCase):
    ext_class = CertificatePolicies
    oid = '2.5.29.32.0'

    q1 = 'text1'
    q2 = x509.UserNotice(explicit_text='text2', notice_reference=None)
    q3 = x509.UserNotice(
        explicit_text=None,
        notice_reference=x509.NoticeReference(organization='text3', notice_numbers=[1])
    )
    q4 = 'text4'
    q5 = x509.UserNotice(
        explicit_text='text5',
        notice_reference=x509.NoticeReference(organization='text6', notice_numbers=[1, 2, 3])
    )

    xpi1 = x509.PolicyInformation(policy_identifier=ObjectIdentifier(oid),
                                  policy_qualifiers=[q1])
    xpi2 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q2],
    )
    xpi3 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q3],
    )
    xpi4 = x509.PolicyInformation(
        policy_identifier=ObjectIdentifier(oid),
        policy_qualifiers=[q4, q5],
    )
    spi1 = {
        'policy_identifier': oid,
        'policy_qualifiers': ['text1'],
    }
    spi2 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            {'explicit_text': 'text2', }
        ],
    }
    spi3 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            {
                'notice_reference': {
                    'organization': 'text3',
                    'notice_numbers': [1, ],
                }
            }
        ],
    }
    spi4 = {
        'policy_identifier': oid,
        'policy_qualifiers': [
            'text4',
            {
                'explicit_text': 'text5',
                'notice_reference': {
                    'organization': 'text6',
                    'notice_numbers': [1, 2, 3],
                }
            }
        ],
    }
    x1 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=False,
        value=x509.CertificatePolicies(policies=[xpi1])
    )
    x2 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=False,
        value=x509.CertificatePolicies(policies=[xpi2])
    )
    x3 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=False,
        value=x509.CertificatePolicies(policies=[xpi3])
    )
    x4 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=False,
        value=x509.CertificatePolicies(policies=[xpi4])
    )
    x5 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=False,
        value=x509.CertificatePolicies(policies=[xpi1, xpi2, xpi4])
    )
    x6 = x509.Extension(
        oid=ExtensionOID.CERTIFICATE_POLICIES, critical=True,
        value=x509.CertificatePolicies(policies=[])
    )
    xs = [x1, x2, x3, x4, x5, x6]

    def setUp(self):
        super(CertificatePoliciesTestCase, self).setUp()
        self.pi1 = PolicyInformation(self.xpi1)
        self.pi2 = PolicyInformation(self.xpi2)
        self.pi3 = PolicyInformation(self.xpi3)
        self.pi4 = PolicyInformation(self.xpi4)
        self.ext1 = CertificatePolicies([self.xpi1])
        self.ext2 = CertificatePolicies([self.xpi2])
        self.ext3 = CertificatePolicies([self.xpi3])
        self.ext4 = CertificatePolicies([self.xpi4])
        self.ext5 = CertificatePolicies([self.xpi1, self.xpi2, self.xpi4])
        self.ext6 = CertificatePolicies({'critical': True})
        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4, self.ext5, self.ext6]

    def test_as_text(self):
        self.assertEqual(
            self.ext1.as_text(),
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * text1'
        )
        self.assertEqual(
            self.ext2.as_text(),
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * UserNotice:\n'
            '    * Explicit text: text2'
        )
        self.assertEqual(
            self.ext3.as_text(),
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * UserNotice:\n'
            '    * Reference:\n'
            '      * Organiziation: text3\n'
            '      * Notice Numbers: [1]'
        )
        self.assertEqual(
            self.ext4.as_text(),
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * text4\n'
            '  * UserNotice:\n'
            '    * Explicit text: text5\n'
            '    * Reference:\n'
            '      * Organiziation: text6\n'
            '      * Notice Numbers: [1, 2, 3]'
        )
        self.assertEqual(
            self.ext5.as_text(),
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * text1\n'
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * UserNotice:\n'
            '    * Explicit text: text2\n'
            '* Policy Identifier: 2.5.29.32.0\n'
            '  Policy Qualifiers:\n'
            '  * text4\n'
            '  * UserNotice:\n'
            '    * Explicit text: text5\n'
            '    * Reference:\n'
            '      * Organiziation: text6\n'
            '      * Notice Numbers: [1, 2, 3]'
        )
        self.assertEqual(self.ext6.as_text(), '')

    def test_count(self):
        self.assertEqual(self.ext1.count(self.xpi1), 1)
        self.assertEqual(self.ext1.count(self.spi1), 1)
        self.assertEqual(self.ext1.count(self.pi1), 1)
        self.assertEqual(self.ext1.count(self.xpi2), 0)
        self.assertEqual(self.ext1.count(self.spi2), 0)
        self.assertEqual(self.ext1.count(self.pi2), 0)

    def test_del(self):
        del self.ext1[0]
        self.assertEqual(len(self.ext1), 0)

    def test_extend(self):
        self.ext1.extend([self.xpi2, self.pi4])
        self.assertEqual(self.ext1, self.ext5)

    def test_from_list(self):
        self.assertEqual(CertificatePolicies([self.xpi1]), self.ext1)

    def test_getitem(self):
        self.assertEqual(self.ext1[0], self.pi1)
        self.assertEqual(self.ext2[0], self.pi2)
        self.assertEqual(self.ext3[0], self.pi3)
        self.assertEqual(self.ext5[0], self.pi1)
        self.assertEqual(self.ext5[1], self.pi2)
        self.assertEqual(self.ext5[2], self.pi4)

    def test_getitem_slices(self):
        self.assertEqual(self.ext5[0:], [self.pi1, self.pi2, self.pi4])
        self.assertEqual(self.ext5[1:], [self.pi2, self.pi4])
        self.assertEqual(self.ext5[2:], [self.pi4])

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))
        self.assertEqual(hash(self.ext4), hash(self.ext4))
        self.assertEqual(hash(self.ext5), hash(self.ext5))
        self.assertEqual(hash(self.ext6), hash(self.ext6))

        self.assertEqual(hash(self.ext1), hash(CertificatePolicies([self.xpi1])))
        self.assertEqual(hash(self.ext2), hash(CertificatePolicies([self.xpi2])))
        self.assertEqual(hash(self.ext3), hash(CertificatePolicies([self.xpi3])))
        self.assertEqual(hash(self.ext4), hash(CertificatePolicies([self.xpi4])))
        self.assertEqual(hash(self.ext5), hash(CertificatePolicies([self.xpi1, self.xpi2, self.xpi4])))

        self.assertEqual(hash(self.ext1), hash(CertificatePolicies([self.spi1])))
        self.assertEqual(hash(self.ext2), hash(CertificatePolicies([self.spi2])))
        self.assertEqual(hash(self.ext3), hash(CertificatePolicies([self.spi3])))
        self.assertEqual(hash(self.ext4), hash(CertificatePolicies([self.spi4])))
        self.assertEqual(hash(self.ext5), hash(CertificatePolicies([self.spi1, self.spi2, self.spi4])))

        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext1), hash(self.ext4))
        self.assertNotEqual(hash(self.ext1), hash(self.ext5))
        self.assertNotEqual(hash(self.ext1), hash(self.ext6))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext4))
        self.assertNotEqual(hash(self.ext2), hash(self.ext5))
        self.assertNotEqual(hash(self.ext2), hash(self.ext6))
        self.assertNotEqual(hash(self.ext3), hash(self.ext4))
        self.assertNotEqual(hash(self.ext3), hash(self.ext5))
        self.assertNotEqual(hash(self.ext3), hash(self.ext6))

        self.assertNotEqual(hash(self.ext3), hash(self.ext6))
        self.assertNotEqual(hash(self.ext4), hash(CertificatePolicies({'critical': False})))

    def test_in(self):
        self.assertIn(self.xpi1, self.ext1)
        self.assertIn(self.spi1, self.ext1)
        self.assertIn(self.pi1, self.ext1)

        self.assertIn(self.xpi2, self.ext2)
        self.assertIn(self.spi2, self.ext2)
        self.assertIn(self.pi2, self.ext2)

        self.assertIn(self.xpi1, self.ext5)
        self.assertIn(self.xpi2, self.ext5)
        self.assertIn(self.xpi4, self.ext5)

    def test_insert(self):
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.spi1]})
        self.ext1.insert(0, self.xpi2)
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.spi2, self.spi1]})
        self.ext1.insert(1, self.spi3)
        self.assertEqual(self.ext1.serialize(),
                         {'critical': False, 'value': [self.spi2, self.spi3, self.spi1]})
        self.ext1.insert(0, self.pi4)
        self.assertEqual(self.ext1.serialize(),
                         {'critical': False, 'value': [self.spi4, self.spi2, self.spi3, self.spi1]})

    def test_len(self):
        self.assertEqual(len(self.ext1), 1)
        self.assertEqual(len(self.ext2), 1)
        self.assertEqual(len(self.ext3), 1)
        self.assertEqual(len(self.ext4), 1)
        self.assertEqual(len(self.ext5), 3)
        self.assertEqual(len(self.ext6), 0)

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext1, self.ext4)
        self.assertNotEqual(self.ext1, self.ext5)
        self.assertNotEqual(self.ext1, self.ext6)

        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext2, self.ext4)
        self.assertNotEqual(self.ext2, self.ext5)
        self.assertNotEqual(self.ext2, self.ext6)

        self.assertNotEqual(self.ext3, self.ext4)
        self.assertNotEqual(self.ext3, self.ext5)
        self.assertNotEqual(self.ext3, self.ext6)

        self.assertNotEqual(self.ext6, CertificatePolicies({'critical': False}))

    def test_not_in(self):
        self.assertNotIn(self.xpi2, self.ext1)
        self.assertNotIn(self.spi2, self.ext1)
        self.assertNotIn(self.pi2, self.ext1)

        self.assertNotIn(self.xpi2, self.ext6)
        self.assertNotIn(self.spi2, self.ext6)
        self.assertNotIn(self.pi2, self.ext6)

    def test_pop(self):
        self.assertEqual(self.ext1.pop(), self.pi1)
        self.assertEqual(len(self.ext1), 0)
        self.assertEqual(self.ext5.pop(1), self.pi2)
        self.assertEqual(len(self.ext5), 2)

    def test_remove(self):
        self.ext1.remove(self.xpi1)
        self.assertEqual(len(self.ext1), 0)
        self.ext2.remove(self.spi2)
        self.assertEqual(len(self.ext2), 0)
        self.ext3.remove(self.pi3)
        self.assertEqual(len(self.ext3), 0)

    def test_repr(self):
        self.assertEqual(
            repr(self.ext1),
            '<CertificatePolicies: [PolicyInformation(oid=2.5.29.32.0, 1 qualifier)], critical=False>')
        self.assertEqual(
            repr(self.ext2),
            '<CertificatePolicies: [PolicyInformation(oid=2.5.29.32.0, 1 qualifier)], critical=False>')
        self.assertEqual(
            repr(self.ext3),
            '<CertificatePolicies: [PolicyInformation(oid=2.5.29.32.0, 1 qualifier)], critical=False>')
        self.assertEqual(
            repr(self.ext4),
            '<CertificatePolicies: [PolicyInformation(oid=2.5.29.32.0, 2 qualifiers)], critical=False>')
        self.assertEqual(
            repr(self.ext5),
            '<CertificatePolicies: [PolicyInformation(oid=2.5.29.32.0, 1 qualifier), '
            'PolicyInformation(oid=2.5.29.32.0, 1 qualifier), PolicyInformation(oid=2.5.29.32.0, 2 '
            'qualifiers)], critical=False>'
        )
        self.assertEqual(
            repr(self.ext6),
            '<CertificatePolicies: [], critical=True>'
        )

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': [self.spi1]})
        self.assertEqual(self.ext2.serialize(), {'critical': False, 'value': [self.spi2]})
        self.assertEqual(self.ext3.serialize(), {'critical': False, 'value': [self.spi3]})
        self.assertEqual(self.ext4.serialize(), {'critical': False, 'value': [self.spi4]})
        self.assertEqual(self.ext5.serialize(),
                         {'critical': False, 'value': [self.spi1, self.spi2, self.spi4]})
        self.assertEqual(self.ext6.serialize(), {'critical': True, 'value': []})

        self.assertEqual(self.ext1, CertificatePolicies(self.ext1.serialize()))
        self.assertEqual(self.ext2, CertificatePolicies(self.ext2.serialize()))
        self.assertEqual(self.ext3, CertificatePolicies(self.ext3.serialize()))
        self.assertEqual(self.ext4, CertificatePolicies(self.ext4.serialize()))
        self.assertEqual(self.ext5, CertificatePolicies(self.ext5.serialize()))
        self.assertEqual(self.ext6, CertificatePolicies(self.ext6.serialize()))

    def test_setitem(self):
        self.ext1[0] = self.xpi2
        self.assertEqual(self.ext1, self.ext2)
        self.ext1[0] = self.spi3
        self.assertEqual(self.ext1, self.ext3)
        self.ext1[0] = self.pi4
        self.assertEqual(self.ext1, self.ext4)

    def test_setitem_slices(self):
        self.ext1[0:] = [self.xpi2]
        self.assertEqual(self.ext1, self.ext2)

    def test_str(self):
        self.assertEqual(str(self.ext1), 'CertificatePolicies(1 Policy, critical=False)')
        self.assertEqual(str(self.ext2), 'CertificatePolicies(1 Policy, critical=False)')
        self.assertEqual(str(self.ext3), 'CertificatePolicies(1 Policy, critical=False)')
        self.assertEqual(str(self.ext4), 'CertificatePolicies(1 Policy, critical=False)')
        self.assertEqual(str(self.ext5), 'CertificatePolicies(3 Policies, critical=False)')
        self.assertEqual(str(self.ext6), 'CertificatePolicies(0 Policies, critical=True)')


class IssuerAlternativeNameTestCase(ListExtensionTestMixin, TestCase):
    ext_class = IssuerAlternativeName
    uri1 = 'https://example.com'
    uri2 = 'https://example.net'
    dns1 = 'example.com'
    dns2 = 'example.net'

    x1 = x509.extensions.Extension(
        oid=ExtensionOID.ISSUER_ALTERNATIVE_NAME, critical=False,
        value=x509.IssuerAlternativeName([])
    )
    x2 = x509.extensions.Extension(
        oid=ExtensionOID.ISSUER_ALTERNATIVE_NAME, critical=False,
        value=x509.IssuerAlternativeName([uri(uri1)])
    )
    x3 = x509.extensions.Extension(
        oid=ExtensionOID.ISSUER_ALTERNATIVE_NAME, critical=False,
        value=x509.IssuerAlternativeName([uri(uri1), dns(dns1)])
    )
    x4 = x509.extensions.Extension(
        oid=ExtensionOID.ISSUER_ALTERNATIVE_NAME, critical=True,
        value=x509.IssuerAlternativeName([])
    )
    x5 = x509.extensions.Extension(
        oid=ExtensionOID.ISSUER_ALTERNATIVE_NAME, critical=True,
        value=x509.IssuerAlternativeName([uri(uri2), dns(dns2)])
    )
    xs = [x1, x2, x3, x4, x5]

    def setUp(self):
        super(IssuerAlternativeNameTestCase, self).setUp()

        self.ext1 = IssuerAlternativeName({'critical': False})
        self.ext2 = IssuerAlternativeName({'critical': False, 'value': [self.uri1]})
        self.ext3 = IssuerAlternativeName({'critical': False, 'value': [self.uri1, self.dns1]})
        self.ext4 = IssuerAlternativeName({'critical': True})
        self.ext5 = IssuerAlternativeName({'critical': True, 'value': [self.uri2, self.dns2]})

        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4, self.ext5]

    def test_as_text(self):
        self.assertEqual(self.ext1.as_text(), "")
        self.assertEqual(self.ext2.as_text(), "* URI:https://example.com")
        self.assertEqual(self.ext3.as_text(), "* URI:https://example.com\n* DNS:example.com")
        self.assertEqual(self.ext4.as_text(), "")
        self.assertEqual(self.ext5.as_text(), "* URI:https://example.net\n* DNS:example.net")

    def test_count(self):
        self.assertEqual(self.ext1.count(self.uri1), 0)
        self.assertEqual(self.ext1.count(uri(self.uri1)), 0)
        self.assertEqual(self.ext2.count(self.uri1), 1)
        self.assertEqual(self.ext2.count(uri(self.uri1)), 1)

    def test_del(self):
        del self.ext3[1]
        self.assertEqual(self.ext3, self.ext2)
        del self.ext3[0]
        self.assertEqual(self.ext3, self.ext1)

    def test_extend(self):
        self.ext1.extend([self.uri1, dns(self.dns1)])
        self.assertEqual(self.ext1, self.ext3)

    def test_from_list(self):
        self.assertEqual(IssuerAlternativeName([]), self.ext1)
        self.assertEqual(IssuerAlternativeName([self.uri1]), self.ext2)
        self.assertEqual(IssuerAlternativeName([self.uri1, self.dns1]), self.ext3)
        self.assertEqual(IssuerAlternativeName([uri(self.uri1)]), self.ext2)
        self.assertEqual(IssuerAlternativeName([uri(self.uri1), dns(self.dns1)]), self.ext3)

    def test_getitem(self):
        self.assertEqual(self.ext3[0], 'URI:%s' % self.uri1)
        self.assertEqual(self.ext3[1], 'DNS:%s' % self.dns1)
        self.assertEqual(self.ext5[0], 'URI:%s' % self.uri2)
        self.assertEqual(self.ext5[1], 'DNS:%s' % self.dns2)

    def test_getitem_slices(self):
        self.assertEqual(self.ext3[0:], ['URI:%s' % self.uri1, 'DNS:%s' % self.dns1])
        self.assertEqual(self.ext3[1:], ['DNS:%s' % self.dns1])
        self.assertEqual(self.ext5[0:], ['URI:%s' % self.uri2, 'DNS:%s' % self.dns2])
        self.assertEqual(self.ext5[1:], ['DNS:%s' % self.dns2])

    def test_hash(self):
        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext1), hash(self.ext4))
        self.assertNotEqual(hash(self.ext1), hash(self.ext5))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext4))
        self.assertNotEqual(hash(self.ext2), hash(self.ext5))
        self.assertNotEqual(hash(self.ext3), hash(self.ext4))
        self.assertNotEqual(hash(self.ext3), hash(self.ext5))
        self.assertNotEqual(hash(self.ext4), hash(self.ext5))

    def test_in(self):
        self.assertIn(self.uri1, self.ext2)
        self.assertIn(self.uri1, self.ext3)
        self.assertIn(uri(self.uri1), self.ext3)
        self.assertIn(self.uri2, self.ext5)
        self.assertIn(self.dns2, self.ext5)
        self.assertIn(uri(self.uri2), self.ext5)
        self.assertIn(dns(self.dns2), self.ext5)

    def test_insert(self):
        self.ext1.insert(0, self.uri1)
        self.assertEqual(self.ext1, self.ext2)
        self.ext1.insert(1, dns(self.dns1))
        self.assertEqual(self.ext1, self.ext3)

        self.ext1.insert(5, dns(self.dns2))
        self.assertEqual(self.ext1, IssuerAlternativeName({
            'critical': False,
            'value': [self.uri1, self.dns1, self.dns2],
        }))

    def test_len(self):
        self.assertEqual(len(self.ext1), 0)
        self.assertEqual(len(self.ext2), 1)
        self.assertEqual(len(self.ext3), 2)
        self.assertEqual(len(self.ext4), 0)
        self.assertEqual(len(self.ext5), 2)

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext1, self.ext4)
        self.assertNotEqual(self.ext1, self.ext5)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext2, self.ext4)
        self.assertNotEqual(self.ext2, self.ext5)
        self.assertNotEqual(self.ext3, self.ext4)
        self.assertNotEqual(self.ext3, self.ext5)
        self.assertNotEqual(self.ext4, self.ext5)

    def test_not_in(self):
        self.assertNotIn(self.dns2, self.ext2)
        self.assertNotIn(self.dns2, self.ext3)
        self.assertNotIn(dns(self.dns1), self.ext1)

    def test_pop(self):
        self.assertEqual(self.ext3.pop(1), 'DNS:%s' % self.dns1)
        self.assertEqual(self.ext3, self.ext2)

        with self.assertRaisesRegex(IndexError, '^pop index out of range$'):
            self.ext3.pop(1)

    def test_remove(self):
        self.ext3.remove(self.dns1)
        self.assertEqual(self.ext3, self.ext2)

        self.ext3.remove(uri(self.uri1))
        self.assertEqual(self.ext3, self.ext1)

        with self.assertRaisesRegex(ValueError, r'^list\.remove\(x\): x not in list$'):
            self.ext3.remove(uri(self.uri1))

    def test_repr(self):
        self.assertEqual(repr(self.ext1), "<IssuerAlternativeName: [], critical=False>")
        self.assertEqual(repr(self.ext2),
                         "<IssuerAlternativeName: ['URI:https://example.com'], critical=False>")
        self.assertEqual(
            repr(self.ext3),
            "<IssuerAlternativeName: ['URI:https://example.com', 'DNS:example.com'], critical=False>")
        self.assertEqual(repr(self.ext4), "<IssuerAlternativeName: [], critical=True>")
        self.assertEqual(
            repr(self.ext5),
            "<IssuerAlternativeName: ['URI:https://example.net', 'DNS:example.net'], critical=True>")

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), {'critical': False, 'value': []})
        self.assertEqual(self.ext2.serialize(), {'critical': False, 'value': ['URI:https://example.com']})
        self.assertEqual(self.ext3.serialize(),
                         {'critical': False, 'value': ['URI:https://example.com', 'DNS:example.com']})
        self.assertEqual(self.ext4.serialize(), {'critical': True, 'value': []})
        self.assertEqual(self.ext5.serialize(),
                         {'critical': True, 'value': ['URI:https://example.net', 'DNS:example.net']})

    def test_setitem(self):
        self.ext3[0] = self.uri2
        self.ext3[1] = dns(self.dns2)
        self.ext3.critical = True
        self.assertEqual(self.ext3, self.ext5)

        with self.assertRaisesRegex(IndexError, '^list assignment index out of range$'):
            self.ext1[0] = self.uri1

    def test_setitem_slices(self):
        self.ext2[1:] = [self.dns1]
        self.assertEqual(self.ext2, self.ext3)
        self.ext4[0:] = [uri(self.uri2), dns(self.dns2)]
        self.assertEqual(self.ext4, self.ext5)

    def test_str(self):
        self.assertEqual(str(self.ext1), "")
        self.assertEqual(str(self.ext2), "URI:https://example.com")
        self.assertEqual(str(self.ext3), "URI:https://example.com,DNS:example.com")
        self.assertEqual(str(self.ext4), "/critical")
        self.assertEqual(str(self.ext5), "URI:https://example.net,DNS:example.net/critical")


class KeyUsageTestCase(TestCase):
    def assertBasic(self, ext):
        self.assertTrue(ext.critical)
        self.assertIn('cRLSign', ext)
        self.assertIn('keyCertSign', ext)
        self.assertNotIn('keyEncipherment', ext)

        typ = ext.extension_type
        self.assertIsInstance(typ, x509.KeyUsage)
        self.assertTrue(typ.crl_sign)
        self.assertTrue(typ.key_cert_sign)
        self.assertFalse(typ.key_encipherment)

        crypto = ext.as_extension()
        self.assertEqual(crypto.oid, ExtensionOID.KEY_USAGE)

    def test_basic(self):
        self.assertBasic(KeyUsage('critical,cRLSign,keyCertSign'))
        self.assertBasic(KeyUsage({'critical': True, 'value': ['cRLSign', 'keyCertSign']}))
        self.assertBasic(KeyUsage(x509.extensions.Extension(
            oid=ExtensionOID.KEY_USAGE,
            critical=True,
            value=x509.KeyUsage(
                content_commitment=False,
                crl_sign=True,
                data_encipherment=True,
                decipher_only=False,
                digital_signature=False,
                encipher_only=False,
                key_agreement=True,
                key_cert_sign=True,
                key_encipherment=False,
            )
        )))

        ext = KeyUsage('critical,cRLSign,keyCertSign')
        ext2 = KeyUsage(ext.as_extension())
        self.assertEqual(ext, ext2)

    def test_hash(self):
        ext1 = KeyUsage('critical,cRLSign,keyCertSign')
        ext2 = KeyUsage('cRLSign,keyCertSign')
        ext3 = KeyUsage('cRLSign,keyCertSign,keyEncipherment')

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertEqual(hash(ext3), hash(ext3))

        self.assertNotEqual(hash(ext1), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext3))
        self.assertNotEqual(hash(ext2), hash(ext3))

    def test_eq(self):
        self.assertEqual(KeyUsage('cRLSign'), KeyUsage('cRLSign'))
        self.assertEqual(KeyUsage('cRLSign,keyCertSign'), KeyUsage('cRLSign,keyCertSign'))
        self.assertEqual(KeyUsage('cRLSign,keyCertSign'), KeyUsage('keyCertSign,cRLSign'))

        self.assertEqual(KeyUsage('critical,cRLSign'), KeyUsage('critical,cRLSign'))
        self.assertEqual(KeyUsage('critical,cRLSign,keyCertSign'), KeyUsage('critical,cRLSign,keyCertSign'))
        self.assertEqual(KeyUsage('critical,cRLSign,keyCertSign'), KeyUsage('critical,keyCertSign,cRLSign'))

    def test_ne(self):
        self.assertNotEqual(KeyUsage('cRLSign'), KeyUsage('keyCertSign'))
        self.assertNotEqual(KeyUsage('cRLSign'), KeyUsage('critical,cRLSign'))
        self.assertNotEqual(KeyUsage('cRLSign'), 10)

    def test_sanity_checks(self):
        # there are some sanity checks
        self.assertEqual(KeyUsage('decipherOnly').value, ['decipherOnly', 'keyAgreement'])

    def test_empty_str(self):
        # we want to accept an empty str as constructor
        ku = KeyUsage('')
        self.assertEqual(len(ku), 0)
        self.assertFalse(bool(ku))

    def test_dunder(self):
        # test __contains__ and __len__
        ku = KeyUsage('cRLSign')
        self.assertIn('cRLSign', ku)
        self.assertNotIn('keyCertSign', ku)
        self.assertEqual(len(ku), 1)
        self.assertTrue(bool(ku))

    def test_error(self):
        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): foo$'):
            KeyUsage('foo')
        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): foobar$'):
            KeyUsage('foobar')

        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): foo$'):
            KeyUsage('critical,foo')

        with self.assertRaisesRegex(ValueError, r'^None: Invalid critical value passed$'):
            KeyUsage({'critical': None, 'value': ['cRLSign']})

        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type object$'):
            KeyUsage(object())

    def test_completeness(self):
        # make sure whe haven't forgotton any keys anywhere
        self.assertEqual(set(KeyUsage.CRYPTOGRAPHY_MAPPING.keys()),
                         set([e[0] for e in KeyUsage.CHOICES]))


class ExtendedKeyUsageTestCase(TestCase):
    def assertBasic(self, ext, critical=True):
        self.assertEqual(ext.critical, critical)
        self.assertIn('clientAuth', ext)
        self.assertIn('serverAuth', ext)
        self.assertNotIn('smartcardLogon', ext)

        typ = ext.extension_type
        self.assertIsInstance(typ, x509.ExtendedKeyUsage)
        self.assertEqual(typ.oid, ExtensionOID.EXTENDED_KEY_USAGE)

        crypto = ext.as_extension()
        self.assertEqual(crypto.critical, critical)
        self.assertEqual(crypto.oid, ExtensionOID.EXTENDED_KEY_USAGE)

        self.assertIn(ExtendedKeyUsageOID.SERVER_AUTH, crypto.value)
        self.assertIn(ExtendedKeyUsageOID.CLIENT_AUTH, crypto.value)
        self.assertNotIn(ExtendedKeyUsageOID.OCSP_SIGNING, crypto.value)

    def test_basic(self):
        self.assertBasic(ExtendedKeyUsage('critical,serverAuth,clientAuth'))
        self.assertBasic(ExtendedKeyUsage(x509.extensions.Extension(
            oid=ExtensionOID.EXTENDED_KEY_USAGE,
            critical=True,
            value=x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH])))
        )

    def test_hash(self):
        ext1 = ExtendedKeyUsage('critical,serverAuth')
        ext2 = ExtendedKeyUsage('serverAuth')
        ext3 = ExtendedKeyUsage('serverAuth,clientAuth')

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertEqual(hash(ext3), hash(ext3))

        self.assertNotEqual(hash(ext1), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext3))
        self.assertNotEqual(hash(ext2), hash(ext3))

    def test_eq(self):
        self.assertEqual(ExtendedKeyUsage('serverAuth'), ExtendedKeyUsage('serverAuth'))
        self.assertEqual(ExtendedKeyUsage('serverAuth,clientAuth'), ExtendedKeyUsage('serverAuth,clientAuth'))
        self.assertEqual(ExtendedKeyUsage('serverAuth,clientAuth'), ExtendedKeyUsage('clientAuth,serverAuth'))

        self.assertEqual(ExtendedKeyUsage('critical,serverAuth'), ExtendedKeyUsage('critical,serverAuth'))
        self.assertEqual(ExtendedKeyUsage('critical,serverAuth,clientAuth'),
                         ExtendedKeyUsage('critical,serverAuth,clientAuth'))
        self.assertEqual(ExtendedKeyUsage('critical,serverAuth,clientAuth'),
                         ExtendedKeyUsage('critical,clientAuth,serverAuth'))

    def test_ne(self):
        self.assertNotEqual(ExtendedKeyUsage('serverAuth'), ExtendedKeyUsage('clientAuth'))
        self.assertNotEqual(ExtendedKeyUsage('serverAuth'), ExtendedKeyUsage('critical,serverAuth'))
        self.assertNotEqual(ExtendedKeyUsage('serverAuth'), 10)

    def test_not_critical(self):
        self.assertBasic(ExtendedKeyUsage('serverAuth,clientAuth'), critical=False)
        ext_value = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH])
        self.assertBasic(ExtendedKeyUsage(
            x509.extensions.Extension(
                oid=ExtensionOID.EXTENDED_KEY_USAGE,
                critical=False,
                value=ext_value
            ),
        ), critical=False)

    def test_completeness(self):
        # make sure whe haven't forgotton any keys anywhere
        self.assertEqual(set(ExtendedKeyUsage.CRYPTOGRAPHY_MAPPING.keys()),
                         set([e[0] for e in ExtendedKeyUsage.CHOICES]))


class NameConstraintsTestCase(TestCase):
    ext_empty = x509.extensions.Extension(
        oid=ExtensionOID.NAME_CONSTRAINTS, critical=True,
        value=x509.NameConstraints(permitted_subtrees=[], excluded_subtrees=[])
    )
    ext_permitted = x509.extensions.Extension(
        oid=ExtensionOID.NAME_CONSTRAINTS, critical=True,
        value=x509.NameConstraints(permitted_subtrees=[dns('example.com')], excluded_subtrees=[])
    )
    ext_excluded = x509.extensions.Extension(
        oid=ExtensionOID.NAME_CONSTRAINTS, critical=True,
        value=x509.NameConstraints(permitted_subtrees=[], excluded_subtrees=[dns('example.com')])
    )
    ext_both = x509.extensions.Extension(
        oid=ExtensionOID.NAME_CONSTRAINTS, critical=True,
        value=x509.NameConstraints(permitted_subtrees=[dns('example.com')],
                                   excluded_subtrees=[dns('example.net')])
    )
    ext_not_critical = x509.extensions.Extension(
        oid=ExtensionOID.NAME_CONSTRAINTS, critical=False,
        value=x509.NameConstraints(permitted_subtrees=[dns('example.com')],
                                   excluded_subtrees=[dns('example.net')])
    )

    def assertEmpty(self, ext):
        self.assertEqual(ext.permitted, [])
        self.assertEqual(ext.excluded, [])
        self.assertEqual(ext, NameConstraints([[], []]))
        self.assertFalse(bool(ext))
        self.assertTrue(ext.critical)
        self.assertEqual(ext.as_extension(), self.ext_empty)

    def assertPermitted(self, ext):
        self.assertEqual(ext.permitted, [dns('example.com')])
        self.assertEqual(ext.excluded, [])
        self.assertEqual(ext, NameConstraints([['example.com'], []]))
        self.assertTrue(bool(ext))
        self.assertTrue(ext.critical)
        self.assertEqual(ext.as_extension(), self.ext_permitted)

    def assertExcluded(self, ext):
        self.assertEqual(ext.permitted, [])
        self.assertEqual(ext.excluded, [dns('example.com')])
        self.assertEqual(ext, NameConstraints([[], ['example.com']]))
        self.assertTrue(bool(ext))
        self.assertTrue(ext.critical)
        self.assertEqual(ext.as_extension(), self.ext_excluded)

    def assertBoth(self, ext):
        self.assertEqual(ext.permitted, [dns('example.com')])
        self.assertEqual(ext.excluded, [dns('example.net')])
        self.assertEqual(ext, NameConstraints([['example.com'], ['example.net']]))
        self.assertTrue(bool(ext))
        self.assertEqual(ext.as_extension(), self.ext_both)
        self.assertTrue(ext.critical)

    def test_from_list(self):
        self.assertEmpty(NameConstraints([[], []]))
        self.assertPermitted(NameConstraints([['example.com'], []]))
        self.assertExcluded(NameConstraints([[], ['example.com']]))
        self.assertBoth(NameConstraints([['example.com'], ['example.net']]))

        # same thing again but with GeneralName instances
        self.assertPermitted(NameConstraints([[dns('example.com')], []]))
        self.assertExcluded(NameConstraints([[], [dns('example.com')]]))
        self.assertBoth(NameConstraints([[dns('example.com')], [dns('example.net')]]))

    def test_from_dict(self):
        self.assertEmpty(NameConstraints({}))
        self.assertEmpty(NameConstraints({'value': {}}))
        self.assertEmpty(NameConstraints({'value': {'permitted': [], 'excluded': []}}))

        self.assertPermitted(NameConstraints({'value': {'permitted': ['example.com']}}))
        self.assertPermitted(NameConstraints({'value': {'permitted': ['example.com'], 'excluded': []}}))
        self.assertPermitted(NameConstraints({'value': {'permitted': [dns('example.com')]}}))
        self.assertPermitted(NameConstraints({'value': {'permitted': [dns('example.com')], 'excluded': []}}))

        self.assertExcluded(NameConstraints({'value': {'excluded': ['example.com']}}))
        self.assertExcluded(NameConstraints({'value': {'excluded': ['example.com'], 'permitted': []}}))
        self.assertExcluded(NameConstraints({'value': {'excluded': [dns('example.com')]}}))
        self.assertExcluded(NameConstraints({'value': {'excluded': [dns('example.com')], 'permitted': []}}))

        self.assertBoth(NameConstraints({'value': {'permitted': ['example.com'],
                                                   'excluded': ['example.net']}}))
        self.assertBoth(NameConstraints({'value': {'permitted': [dns('example.com')],
                                                   'excluded': [dns('example.net')]}}))

    def test_from_extension(self):
        self.assertEmpty(NameConstraints(self.ext_empty))
        self.assertPermitted(NameConstraints(self.ext_permitted))
        self.assertExcluded(NameConstraints(self.ext_excluded))
        self.assertBoth(NameConstraints(self.ext_both))

    def test_hash(self):
        ext1 = NameConstraints([['example.com'], []])
        ext2 = NameConstraints([['example.com'], ['example.net']])
        ext3 = NameConstraints([[], ['example.net']])

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertEqual(hash(ext3), hash(ext3))

        self.assertNotEqual(hash(ext1), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext3))
        self.assertNotEqual(hash(ext2), hash(ext3))

    def test_as_str(self):  # test various string conversion methods
        ext = NameConstraints(self.ext_empty)
        self.assertEqual(str(ext), "NameConstraints(permitted=[], excluded=[], critical=True)")
        self.assertEqual(repr(ext), "<NameConstraints: permitted=[], excluded=[], critical=True>")
        self.assertEqual(ext.as_text(), "")

        ext = NameConstraints(self.ext_permitted)
        self.assertEqual(str(ext),
                         "NameConstraints(permitted=['DNS:example.com'], excluded=[], critical=True)")
        self.assertEqual(repr(ext),
                         "<NameConstraints: permitted=['DNS:example.com'], excluded=[], critical=True>")
        self.assertEqual(ext.as_text(), "Permitted:\n  * DNS:example.com\n")

        ext = NameConstraints(self.ext_excluded)
        self.assertEqual(str(ext),
                         "NameConstraints(permitted=[], excluded=['DNS:example.com'], critical=True)")
        self.assertEqual(repr(ext),
                         "<NameConstraints: permitted=[], excluded=['DNS:example.com'], critical=True>")
        self.assertEqual(ext.as_text(), "Excluded:\n  * DNS:example.com\n")

        ext = NameConstraints(self.ext_both)
        self.assertEqual(
            str(ext),
            "NameConstraints(permitted=['DNS:example.com'], excluded=['DNS:example.net'], critical=True)")
        self.assertEqual(
            repr(ext),
            "<NameConstraints: permitted=['DNS:example.com'], excluded=['DNS:example.net'], critical=True>")
        self.assertEqual(ext.as_text(), """Permitted:
  * DNS:example.com
Excluded:
  * DNS:example.net
""")

    def test_error(self):
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type NoneType$'):
            NameConstraints(None)
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type bool$'):
            NameConstraints(False)

    def test_serialize(self):
        empty = NameConstraints(self.ext_empty)
        permitted = NameConstraints(self.ext_permitted)
        excluded = NameConstraints(self.ext_excluded)
        both = NameConstraints(self.ext_both)
        not_critical = NameConstraints(self.ext_not_critical)

        self.assertEqual(NameConstraints(empty.serialize()), empty)
        self.assertEqual(NameConstraints(permitted.serialize()), permitted)
        self.assertEqual(NameConstraints(excluded.serialize()), excluded)
        self.assertEqual(NameConstraints(both.serialize()), both)
        self.assertEqual(NameConstraints(not_critical.serialize()), not_critical)


class OCSPNoCheckTestCase(ExtensionTestMixin, TestCase):
    ext_class = OCSPNoCheck

    x1 = x509.extensions.Extension(oid=ExtensionOID.OCSP_NO_CHECK, critical=True,
                                   value=x509.OCSPNoCheck())
    x2 = x509.extensions.Extension(oid=ExtensionOID.OCSP_NO_CHECK, critical=False,
                                   value=x509.OCSPNoCheck())
    xs = [x1, x2]

    def setUp(self):
        super(OCSPNoCheckTestCase, self).setUp()
        self.ext1 = OCSPNoCheck({'critical': True})
        self.ext2 = OCSPNoCheck({'critical': False})
        self.exts = [self.ext1, self.ext2]

    # OCSPNoCheck does not compare as equal until cryptography 2.7:
    #   https://github.com/pyca/cryptography/issues/4818
    @unittest.skipUnless(x509.OCSPNoCheck() == x509.OCSPNoCheck(),
                         'Extensions compare as equal.')  # pragma: cryptography<2.7
    def test_as_extension(self):
        super(OCSPNoCheckTestCase, self).test_as_extension()

    def test_as_text(self):
        ext1 = OCSPNoCheck()
        ext2 = OCSPNoCheck({'critical': True})
        self.assertEqual(ext1.as_text(), "OCSPNoCheck")
        self.assertEqual(ext2.as_text(), "OCSPNoCheck")

    def test_ne(self):
        ext1 = x509.extensions.Extension(oid=ExtensionOID.OCSP_NO_CHECK, critical=True, value=None)
        ext2 = x509.extensions.Extension(oid=ExtensionOID.OCSP_NO_CHECK, critical=False, value=None)

        self.assertNotEqual(OCSPNoCheck(ext1), OCSPNoCheck(ext2))
        self.assertNotEqual(OCSPNoCheck({'critical': True}), OCSPNoCheck({'critical': False}))

    def test_hash(self):
        ext1 = OCSPNoCheck()
        ext2 = OCSPNoCheck({'critical': True})

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext2))

    # OCSPNoCheck does not compare as equal until cryptography 2.7:
    #   https://github.com/pyca/cryptography/issues/4818
    @unittest.skipUnless(x509.OCSPNoCheck() == x509.OCSPNoCheck(),
                         'Extensions compare as equal.')  # pragma: cryptography<2.7
    def test_for_builder(self):
        super(OCSPNoCheckTestCase, self).test_for_builder()

    def test_from_extension(self):
        ext = OCSPNoCheck(x509.extensions.Extension(
            oid=ExtensionOID.OCSP_NO_CHECK, critical=True, value=None))
        self.assertTrue(ext.critical)

        ext = OCSPNoCheck(x509.extensions.Extension(
            oid=ExtensionOID.OCSP_NO_CHECK, critical=False, value=None))
        self.assertFalse(ext.critical)

    def test_from_dict(self):
        self.assertFalse(OCSPNoCheck({}).critical)
        self.assertTrue(OCSPNoCheck({'critical': True}).critical)
        self.assertTrue(OCSPNoCheck({'critical': True, 'foo': 'bar'}).critical)
        self.assertFalse(OCSPNoCheck({'critical': False}).critical)
        self.assertFalse(OCSPNoCheck({'critical': False, 'foo': 'bar'}).critical)

    def test_from_str(self):
        with self.assertRaises(NotImplementedError):
            OCSPNoCheck('foobar')

    def test_str(self):
        ext1 = OCSPNoCheck({'critical': True})
        ext2 = OCSPNoCheck({'critical': False})

        self.assertEqual(str(ext1), 'OCSPNoCheck/critical')
        self.assertEqual(str(ext2), 'OCSPNoCheck')

    def test_repr(self):
        ext1 = OCSPNoCheck({'critical': True})
        ext2 = OCSPNoCheck({'critical': False})

        self.assertEqual(repr(ext1), '<OCSPNoCheck: critical=True>')
        self.assertEqual(repr(ext2), '<OCSPNoCheck: critical=False>')

    def test_serialize(self):
        ext1 = OCSPNoCheck({'critical': True})
        ext2 = OCSPNoCheck({'critical': False})

        self.assertEqual(ext1.serialize(), ext1.serialize())
        self.assertNotEqual(ext1.serialize(), ext2.serialize())
        self.assertEqual(ext1, OCSPNoCheck(ext1.serialize()))
        self.assertEqual(ext2, OCSPNoCheck(ext2.serialize()))


class PrecertPoisonTestCase(ExtensionTestMixin, TestCase):
    # NOTE: this extension is always critical and has no value, that's why there are fewer test instances here
    ext_class = PrecertPoison

    x1 = x509.extensions.Extension(oid=ExtensionOID.PRECERT_POISON, critical=True, value=x509.PrecertPoison())
    xs = [x1]

    def setUp(self):
        super(PrecertPoisonTestCase, self).setUp()
        self.ext1 = PrecertPoison({})
        self.exts = [self.ext1]

    # PrecertPoison does not compare as equal until cryptography 2.7:
    #   https://github.com/pyca/cryptography/issues/4818
    @unittest.skipUnless(hasattr(x509, 'PrecertPoison') and x509.PrecertPoison() == x509.PrecertPoison(),
                         'Extensions compare as equal.')  # pragma: only cryptography<2.7
    def test_as_extension(self):
        super(PrecertPoisonTestCase, self).test_as_extension()

    def test_as_text(self):
        self.assertEqual(PrecertPoison().as_text(), "PrecertPoison")

    # PrecertPoison does not compare as equal until cryptography 2.7:
    #   https://github.com/pyca/cryptography/issues/4818
    @unittest.skipUnless(hasattr(x509, 'PrecertPoison') and x509.PrecertPoison() == x509.PrecertPoison(),
                         'Extensions compare as equal.')  # pragma: only cryptography<2.7
    def test_for_builder(self):
        super(PrecertPoisonTestCase, self).test_for_builder()

    def test_hash(self):
        ext1 = PrecertPoison()
        ext2 = PrecertPoison({'critical': True})

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertEqual(hash(ext1), hash(ext2))

    def test_ne(self):
        # PrecertPoison is always critical and has no value, thus all instances compare as equal (and there
        # is nothing we could test)
        pass

    def test_from_extension(self):
        ext = PrecertPoison(x509.extensions.Extension(
            oid=ExtensionOID.PRECERT_POISON, critical=True, value=None))
        self.assertTrue(ext.critical)

    def test_from_dict(self):
        self.assertTrue(PrecertPoison({}).critical)
        self.assertTrue(PrecertPoison({'critical': True}).critical)
        self.assertTrue(PrecertPoison({'critical': True, 'foo': 'bar'}).critical)

    def test_from_str(self):
        with self.assertRaises(NotImplementedError):
            PrecertPoison('foobar')

    def test_str(self):
        self.assertEqual(str(PrecertPoison({'critical': True})), 'PrecertPoison/critical')

    def test_repr(self):
        self.assertEqual(repr(PrecertPoison({'critical': True})), '<PrecertPoison: critical=True>')

    def test_serialize(self):
        ext1 = PrecertPoison()
        ext2 = PrecertPoison({'critical': True})

        self.assertEqual(ext1.serialize(), ext1.serialize())
        self.assertEqual(ext1.serialize(), ext2.serialize())
        self.assertEqual(ext1, PrecertPoison(ext1.serialize()))
        self.assertEqual(ext2, PrecertPoison(ext2.serialize()))

    def test_non_critical(self):
        ext = x509.extensions.Extension(oid=ExtensionOID.PRECERT_POISON, critical=False, value=None)

        with self.assertRaisesRegex(ValueError, '^PrecertPoison must always be marked as critical$'):
            PrecertPoison(ext)
        with self.assertRaisesRegex(ValueError, '^PrecertPoison must always be marked as critical$'):
            PrecertPoison({'critical': False})


@unittest.skipUnless(ca_settings.OPENSSL_SUPPORTS_SCT,
                     'This version of OpenSSL does not support SCTs')
class PrecertificateSignedCertificateTimestampsTestCase(
        DjangoCAWithCertTestCase):  # pragma: only cryptography>=2.4

    def setUp(self):
        super(PrecertificateSignedCertificateTimestampsTestCase, self).setUp()
        self.name1 = 'letsencrypt_x3-cert'
        self.name2 = 'comodo_ev-cert'
        cert1 = self.certs[self.name1]
        cert2 = self.certs[self.name2]

        self.x1 = cert1.x509.extensions.get_extension_for_oid(
            ExtensionOID.PRECERT_SIGNED_CERTIFICATE_TIMESTAMPS)
        self.x2 = cert2.x509.extensions.get_extension_for_oid(
            ExtensionOID.PRECERT_SIGNED_CERTIFICATE_TIMESTAMPS)
        self.ext1 = PrecertificateSignedCertificateTimestamps(self.x1)
        self.ext2 = PrecertificateSignedCertificateTimestamps(self.x2)
        self.exts = [self.ext1, self.ext2]
        self.xs = [self.x1, self.x2]
        self.data1 = certs[self.name1]['precertificate_signed_certificate_timestamps']
        self.data2 = certs[self.name2]['precertificate_signed_certificate_timestamps']

    def test_count(self):
        self.assertEqual(self.ext1.count(self.data1['value'][0]), 1)
        self.assertEqual(self.ext1.count(self.data2['value'][0]), 0)
        self.assertEqual(self.ext1.count(self.x1.value[0]), 1)
        self.assertEqual(self.ext1.count(self.x2.value[0]), 0)

        self.assertEqual(self.ext2.count(self.data1['value'][0]), 0)
        self.assertEqual(self.ext2.count(self.data2['value'][0]), 1)
        self.assertEqual(self.ext2.count(self.x1.value[0]), 0)
        self.assertEqual(self.ext2.count(self.x2.value[0]), 1)

    def test_del(self):
        with self.assertRaises(NotImplementedError):
            del self.ext1[0]
        with self.assertRaises(NotImplementedError):
            del self.ext2[0]

    def test_extend(self):
        with self.assertRaises(NotImplementedError):
            self.ext1.extend([])
        with self.assertRaises(NotImplementedError):
            self.ext2.extend([])

    def test_extension_type(self):
        self.assertEqual(self.ext1.extension_type, self.x1.value)
        self.assertEqual(self.ext2.extension_type, self.x2.value)

    def test_from_list(self):
        with self.assertRaises(NotImplementedError):
            PrecertificateSignedCertificateTimestamps([])

    def test_getitem(self):
        self.assertEqual(self.ext1[0], self.data1['value'][0])
        self.assertEqual(self.ext1[1], self.data1['value'][1])
        with self.assertRaises(IndexError):
            self.ext1[2]

        self.assertEqual(self.ext2[0], self.data2['value'][0])
        self.assertEqual(self.ext2[1], self.data2['value'][1])
        self.assertEqual(self.ext2[2], self.data2['value'][2])
        with self.assertRaises(IndexError):
            self.ext2[3]

    def test_getitem_slices(self):
        self.assertEqual(self.ext1[:1], self.data1['value'][:1])
        self.assertEqual(self.ext2[:2], self.data2['value'][:2])
        self.assertEqual(self.ext2[:], self.data2['value'][:])

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext2))

    def test_in(self):
        for val in self.data1['value']:
            self.assertIn(val, self.ext1)
        for val in self.x1.value:
            self.assertIn(val, self.ext1)
        for val in self.data2['value']:
            self.assertIn(val, self.ext2)
        for val in self.x2.value:
            self.assertIn(val, self.ext2)

    def test_insert(self):
        with self.assertRaises(NotImplementedError):
            self.ext1.insert(0, self.data1['value'][0])
        with self.assertRaises(NotImplementedError):
            self.ext2.insert(0, self.data2['value'][0])

    def test_len(self):
        self.assertEqual(len(self.ext1), 2)
        self.assertEqual(len(self.ext2), 3)

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)

    def test_not_in(self):
        self.assertNotIn(self.data1['value'][0], self.ext2)
        self.assertNotIn(self.data2['value'][0], self.ext1)

        self.assertNotIn(self.x1.value[0], self.ext2)
        self.assertNotIn(self.x2.value[0], self.ext1)

    def test_pop(self):
        with self.assertRaises(NotImplementedError):
            self.ext1.pop(self.data1['value'][0])
        with self.assertRaises(NotImplementedError):
            self.ext2.pop(self.data2['value'][0])

    def test_remove(self):
        with self.assertRaises(NotImplementedError):
            self.ext1.remove(self.data1['value'][0])
        with self.assertRaises(NotImplementedError):
            self.ext2.remove(self.data2['value'][0])

    def test_repr(self):
        if six.PY2:  # pragma: only py2
            exp1 = [{str(k): str(v) for k, v in e.items()} for e in self.data1['value']]
            exp2 = [{str(k): str(v) for k, v in e.items()} for e in self.data2['value']]
        else:
            exp1 = self.data1['value']
            exp2 = self.data2['value']

        self.assertEqual(
            repr(self.ext1),
            '<PrecertificateSignedCertificateTimestamps: %s, critical=False>' % repr(exp1))
        self.assertEqual(
            repr(self.ext2),
            '<PrecertificateSignedCertificateTimestamps: %s, critical=False>' % repr(exp2))

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), self.data1)
        self.assertEqual(self.ext2.serialize(), self.data2)

    def test_setitem(self):
        with self.assertRaises(NotImplementedError):
            self.ext1[0] = self.data2['value'][0]
        with self.assertRaises(NotImplementedError):
            self.ext2[0] = self.data1['value'][0]

    def test_setitem_slices(self):
        with self.assertRaises(NotImplementedError):
            self.ext1[:] = self.data2
        with self.assertRaises(NotImplementedError):
            self.ext2[:] = self.data1

    def test_str(self):
        self.assertEqual(str(self.ext1), '<2 entry(s)>')
        self.assertEqual(str(self.ext2), '<3 entry(s)>')

        with self.patch_object(self.ext2, 'critical', True):
            self.assertEqual(str(self.ext2), '<3 entry(s)>/critical')


class UnknownExtensionTestCase(TestCase):
    def test_basic(self):
        unk = SubjectAlternativeName(['https://example.com']).as_extension()
        ext = UnrecognizedExtension(unk)
        self.assertEqual(ext.name, 'Unsupported extension (OID %s)' % unk.oid.dotted_string)
        self.assertEqual(ext.as_text(), 'Could not parse extension')

        name = 'my name'
        error = 'my error'
        ext = UnrecognizedExtension(unk, name=name, error=error)
        self.assertEqual(ext.name, name)
        self.assertEqual(ext.as_text(), 'Could not parse extension (%s)' % error)


class SubjectAlternativeNameTestCase(TestCase):
    def test_operators(self):
        ext = SubjectAlternativeName(['https://example.com'])
        self.assertIn('https://example.com', ext)
        self.assertIn(uri('https://example.com'), ext)
        self.assertNotIn('https://example.net', ext)
        self.assertNotIn(uri('https://example.net'), ext)

        self.assertEqual(len(ext), 1)
        self.assertEqual(bool(ext), True)

    def test_from_extension(self):
        x509_ext = x509.extensions.Extension(
            oid=ExtensionOID.SUBJECT_ALTERNATIVE_NAME, critical=True,
            value=x509.SubjectAlternativeName([dns('example.com')]))
        ext = SubjectAlternativeName(x509_ext)
        self.assertEqual(ext.as_extension(), x509_ext)

    def test_from_dict(self):
        ext = SubjectAlternativeName({})
        self.assertEqual(ext.value, [])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 0)
        self.assertEqual(bool(ext), False)

        ext = SubjectAlternativeName({'value': None})
        self.assertEqual(ext.value, [])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 0)
        self.assertEqual(bool(ext), False)

        ext = SubjectAlternativeName({'value': []})
        self.assertEqual(ext.value, [])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 0)
        self.assertEqual(bool(ext), False)

        ext = SubjectAlternativeName({'value': 'example.com'})
        self.assertEqual(ext.value, [dns('example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 1)
        self.assertEqual(bool(ext), True)

        ext = SubjectAlternativeName({'value': dns('example.com')})
        self.assertEqual(ext.value, [dns('example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 1)
        self.assertEqual(bool(ext), True)

        ext = SubjectAlternativeName({'value': ['example.com']})
        self.assertEqual(ext.value, [dns('example.com')])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 1)
        self.assertEqual(bool(ext), True)

        ext = SubjectAlternativeName({'value': ['example.com', dns('example.net')]})
        self.assertEqual(ext.value, [dns('example.com'), dns('example.net')])
        self.assertFalse(ext.critical)
        self.assertEqual(len(ext), 2)
        self.assertEqual(bool(ext), True)

    def test_list_funcs(self):
        ext = SubjectAlternativeName(['https://example.com'])
        ext.append('https://example.net')
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net')])
        self.assertEqual(ext.count('https://example.com'), 1)
        self.assertEqual(ext.count(uri('https://example.com')), 1)
        self.assertEqual(ext.count('https://example.net'), 1)
        self.assertEqual(ext.count(uri('https://example.net')), 1)
        self.assertEqual(ext.count('https://example.org'), 0)
        self.assertEqual(ext.count(uri('https://example.org')), 0)

        ext.clear()
        self.assertEqual(ext.value, [])
        self.assertEqual(ext.count('https://example.com'), 0)
        self.assertEqual(ext.count(uri('https://example.com')), 0)

        ext.extend(['https://example.com', 'https://example.net'])
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net')])
        ext.extend(['https://example.org'])
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net'),
                                     uri('https://example.org')])

        ext.clear()
        ext.extend([uri('https://example.com'), uri('https://example.net')])
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net')])
        ext.extend([uri('https://example.org')])
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net'),
                                     uri('https://example.org')])

        self.assertEqual(ext.pop(), 'URI:https://example.org')
        self.assertEqual(ext.value, [uri('https://example.com'), uri('https://example.net')])

        self.assertIsNone(ext.remove('https://example.com'))
        self.assertEqual(ext.value, [uri('https://example.net')])

        self.assertIsNone(ext.remove(uri('https://example.net')))
        self.assertEqual(ext.value, [])

        ext.insert(0, 'https://example.com')
        self.assertEqual(ext.value, [uri('https://example.com')])

    def test_slices(self):
        val = ['DNS:foo', 'DNS:bar', 'DNS:bla']
        ext = SubjectAlternativeName(val)
        self.assertEqual(ext[0], val[0])
        self.assertEqual(ext[1], val[1])
        self.assertEqual(ext[0:], val[0:])
        self.assertEqual(ext[1:], val[1:])
        self.assertEqual(ext[:1], val[:1])
        self.assertEqual(ext[1:2], val[1:2])

        ext[0] = 'test'
        val = [dns('test'), dns('bar'), dns('bla')]
        self.assertEqual(ext.value, val)
        ext[1:2] = ['x', 'y']
        val[1:2] = [dns('x'), dns('y')]
        self.assertEqual(ext.value, val)
        ext[1:] = ['a', 'b']
        val[1:] = [dns('a'), dns('b')]
        self.assertEqual(ext.value, val)

        del ext[0]
        del val[0]
        self.assertEqual(ext.value, val)

    def test_serialize(self):
        val = ['foo', 'bar', 'bla']
        ext = SubjectAlternativeName({'value': val, 'critical': False})
        self.assertEqual(ext, SubjectAlternativeName(ext.serialize()))
        ext = SubjectAlternativeName({'value': val, 'critical': True})
        self.assertEqual(ext, SubjectAlternativeName(ext.serialize()))

    def test_as_str(self):  # test various string conversion methods
        san = SubjectAlternativeName([])
        self.assertEqual(str(san), "")
        self.assertEqual(repr(san), "<SubjectAlternativeName: [], critical=False>")
        self.assertEqual(san.as_text(), "")
        san.critical = True
        self.assertEqual(str(san), "/critical")
        self.assertEqual(repr(san), "<SubjectAlternativeName: [], critical=True>")
        self.assertEqual(san.as_text(), "")

        san = SubjectAlternativeName(['example.com'])
        self.assertEqual(str(san), "DNS:example.com")
        self.assertEqual(repr(san), "<SubjectAlternativeName: ['DNS:example.com'], critical=False>")
        self.assertEqual(san.as_text(), "* DNS:example.com")
        san.critical = True
        self.assertEqual(str(san), "DNS:example.com/critical")
        self.assertEqual(repr(san), "<SubjectAlternativeName: ['DNS:example.com'], critical=True>")
        self.assertEqual(san.as_text(), "* DNS:example.com")

        san = SubjectAlternativeName([dns('example.com')])
        self.assertEqual(str(san), "DNS:example.com")
        self.assertEqual(repr(san), "<SubjectAlternativeName: ['DNS:example.com'], critical=False>")
        self.assertEqual(san.as_text(), "* DNS:example.com")
        san.critical = True
        self.assertEqual(str(san), "DNS:example.com/critical")
        self.assertEqual(repr(san), "<SubjectAlternativeName: ['DNS:example.com'], critical=True>")
        self.assertEqual(san.as_text(), "* DNS:example.com")

        san = SubjectAlternativeName([dns('example.com'), dns('example.org')])
        self.assertEqual(str(san), "DNS:example.com,DNS:example.org")
        self.assertEqual(repr(san),
                         "<SubjectAlternativeName: ['DNS:example.com', 'DNS:example.org'], critical=False>")
        self.assertEqual(san.as_text(), "* DNS:example.com\n* DNS:example.org")
        san.critical = True
        self.assertEqual(str(san), "DNS:example.com,DNS:example.org/critical")
        self.assertEqual(repr(san),
                         "<SubjectAlternativeName: ['DNS:example.com', 'DNS:example.org'], critical=True>")
        self.assertEqual(san.as_text(), "* DNS:example.com\n* DNS:example.org")

    def test_hash(self):
        ext1 = SubjectAlternativeName('example.com')
        ext2 = SubjectAlternativeName('critical,example.com')
        ext3 = SubjectAlternativeName('critical,example.com,example.net')

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertEqual(hash(ext3), hash(ext3))

        self.assertNotEqual(hash(ext1), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext3))
        self.assertNotEqual(hash(ext2), hash(ext3))

    def test_error(self):
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type NoneType$'):
            SubjectAlternativeName(None)
        with self.assertRaisesRegex(ValueError, r'^Value is of unsupported type bool$'):
            SubjectAlternativeName(False)


class SubjectKeyIdentifierTestCase(ExtensionTestMixin, TestCase):
    ext_class = SubjectKeyIdentifier

    hex1 = '33:33:33:33:33:33'
    hex2 = '44:44:44:44:44:44'
    hex3 = '55:55:55:55:55:55'
    b1 = b'333333'
    b2 = b'DDDDDD'
    b3 = b'UUUUUU'  # really unknown right now
    x1 = x509.Extension(
        oid=x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER, critical=False,
        value=x509.SubjectKeyIdentifier(b1)
    )
    x2 = x509.Extension(
        oid=x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER, critical=False,
        value=x509.SubjectKeyIdentifier(b2)
    )
    x3 = x509.Extension(
        oid=x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER, critical=True,
        value=x509.SubjectKeyIdentifier(b3)
    )
    xs = [x1, x2, x3]

    def setUp(self):
        super(SubjectKeyIdentifierTestCase, self).setUp()
        self.ext1 = SubjectKeyIdentifier(self.hex1)
        self.ext2 = SubjectKeyIdentifier(self.hex2)
        self.ext3 = SubjectKeyIdentifier({'value': self.hex3, 'critical': True})
        self.exts = [self.ext1, self.ext2, self.ext3]

    def test_basic(self):
        ext = SubjectKeyIdentifier(self.x1)
        self.assertEqual(ext.as_text(), '33:33:33:33:33:33')
        self.assertEqual(ext.as_extension(), self.x1)

    def test_as_text(self):
        self.assertEqual(SubjectKeyIdentifier(self.hex1).as_text(), self.hex1)
        self.assertEqual(SubjectKeyIdentifier(self.hex2).as_text(), self.hex2)
        self.assertEqual(SubjectKeyIdentifier(self.x1).as_text(), self.hex1)

    def test_hash(self):
        ext1 = SubjectKeyIdentifier(self.hex1)
        ext2 = SubjectKeyIdentifier(self.hex2)
        ext3 = SubjectKeyIdentifier(self.x1)

        self.assertEqual(hash(ext1), hash(ext1))
        self.assertEqual(hash(ext1), hash(ext3))
        self.assertEqual(hash(ext2), hash(ext2))
        self.assertNotEqual(hash(ext1), hash(ext2))

    def test_ne(self):
        ext1 = SubjectKeyIdentifier(self.hex1)
        ext2 = SubjectKeyIdentifier(self.hex2)
        ext3 = SubjectKeyIdentifier(self.x1)

        self.assertNotEqual(ext1, ext2)
        self.assertNotEqual(ext2, ext3)

    def test_repr(self):
        ext1 = SubjectKeyIdentifier(self.hex1)
        ext2 = SubjectKeyIdentifier(self.hex2)
        ext3 = SubjectKeyIdentifier(self.x1)

        if six.PY2:  # pragma: only py2
            self.assertEqual(repr(ext1), '<SubjectKeyIdentifier: 333333, critical=False>')
            self.assertEqual(repr(ext2), '<SubjectKeyIdentifier: DDDDDD, critical=False>')
            self.assertEqual(repr(ext3), '<SubjectKeyIdentifier: 333333, critical=False>')
        else:
            self.assertEqual(repr(ext1), '<SubjectKeyIdentifier: b\'333333\', critical=False>')
            self.assertEqual(repr(ext2), '<SubjectKeyIdentifier: b\'DDDDDD\', critical=False>')
            self.assertEqual(repr(ext3), '<SubjectKeyIdentifier: b\'333333\', critical=False>')

    def test_serialize(self):
        ext1 = SubjectKeyIdentifier(self.hex1)
        ext2 = SubjectKeyIdentifier(self.hex2)
        ext3 = SubjectKeyIdentifier(self.x1)

        self.assertEqual(ext1.serialize(), {'critical': False, 'value': self.hex1})
        self.assertEqual(ext2.serialize(), {'critical': False, 'value': self.hex2})
        self.assertEqual(ext3.serialize(), {'critical': False, 'value': self.hex1})
        self.assertEqual(ext1.serialize(), SubjectKeyIdentifier(self.hex1).serialize())
        self.assertNotEqual(ext1.serialize(), ext2.serialize())

    def test_str(self):
        ext = SubjectKeyIdentifier(self.hex1)
        self.assertEqual(str(ext), self.hex1)


class TLSFeatureTestCase(TestCase):
    x1 = x509.extensions.Extension(
        oid=ExtensionOID.TLS_FEATURE, critical=True,
        value=x509.TLSFeature(features=[TLSFeatureType.status_request])
    )
    x2 = x509.extensions.Extension(
        oid=ExtensionOID.TLS_FEATURE, critical=False,
        value=x509.TLSFeature(features=[TLSFeatureType.status_request])
    )
    x3 = x509.extensions.Extension(
        oid=ExtensionOID.TLS_FEATURE, critical=False,
        value=x509.TLSFeature(features=[TLSFeatureType.status_request, TLSFeatureType.status_request_v2])
    )
    x4 = x509.extensions.Extension(
        oid=ExtensionOID.TLS_FEATURE, critical=False,
        value=x509.TLSFeature(features=[TLSFeatureType.status_request_v2, TLSFeatureType.status_request])
    )
    xs = [x1, x2, x3, x4]

    def setUp(self):
        super(TLSFeatureTestCase, self).setUp()
        self.ext1 = TLSFeature('critical,OCSPMustStaple')
        self.ext2 = TLSFeature('OCSPMustStaple')
        self.ext3 = TLSFeature('OCSPMustStaple,MultipleCertStatusRequest')
        self.ext4 = TLSFeature('MultipleCertStatusRequest,OCSPMustStaple')  # reversed order
        self.exts = [self.ext1, self.ext2, self.ext3, self.ext4]

    def assertBasic(self, ext, critical=True):
        self.assertEqual(ext.critical, critical)
        self.assertEqual(ext.value, ['OCSPMustStaple'])

        typ = ext.extension_type
        self.assertIsInstance(typ, x509.TLSFeature)
        self.assertEqual(typ.oid, ExtensionOID.TLS_FEATURE)

        crypto = ext.as_extension()
        self.assertEqual(crypto.critical, critical)
        self.assertEqual(crypto.oid, ExtensionOID.TLS_FEATURE)

        self.assertIn(TLSFeatureType.status_request, crypto.value)
        self.assertNotIn(TLSFeatureType.status_request_v2, crypto.value)

    def test_completeness(self):
        # make sure whe haven't forgotton any keys anywhere
        self.assertEqual(set(TLSFeature.CRYPTOGRAPHY_MAPPING.keys()),
                         set([e[0] for e in TLSFeature.CHOICES]))
        self.assertCountEqual(TLSFeature.CRYPTOGRAPHY_MAPPING.values(),
                              x509.TLSFeatureType.__members__.values())

    def test_count(self):
        self.assertEqual(self.ext1.count('OCSPMustStaple'), 1)
        self.assertEqual(self.ext2.count('OCSPMustStaple'), 1)
        self.assertEqual(self.ext3.count('OCSPMustStaple'), 1)
        self.assertEqual(self.ext4.count('OCSPMustStaple'), 1)

        self.assertEqual(self.ext1.count(TLSFeatureType.status_request), 1)
        self.assertEqual(self.ext2.count(TLSFeatureType.status_request), 1)
        self.assertEqual(self.ext3.count(TLSFeatureType.status_request), 1)
        self.assertEqual(self.ext4.count(TLSFeatureType.status_request), 1)

        self.assertEqual(self.ext1.count('MultipleCertStatusRequest'), 0)
        self.assertEqual(self.ext2.count('MultipleCertStatusRequest'), 0)
        self.assertEqual(self.ext3.count('MultipleCertStatusRequest'), 1)
        self.assertEqual(self.ext4.count('MultipleCertStatusRequest'), 1)

        self.assertEqual(self.ext1.count(TLSFeatureType.status_request_v2), 0)
        self.assertEqual(self.ext2.count(TLSFeatureType.status_request_v2), 0)
        self.assertEqual(self.ext3.count(TLSFeatureType.status_request_v2), 1)
        self.assertEqual(self.ext4.count(TLSFeatureType.status_request_v2), 1)

        with self.assertRaisesRegex(ValueError, r'^Unknown value: foo$'):
            self.assertEqual(self.ext1.count('foo'), 0)

    def test_eq_order(self):
        # ext3 and ext4 are the same, only with different order
        self.assertEqual(self.ext3, self.ext4),

    def test_from_list(self):
        self.assertEqual(TLSFeature(['OCSPMustStaple']), self.ext2)
        self.assertEqual(TLSFeature(['OCSPMustStaple', 'MultipleCertStatusRequest']), self.ext3)
        self.assertEqual(TLSFeature(['OCSPMustStaple', 'MultipleCertStatusRequest']), self.ext4)
        self.assertEqual(TLSFeature(['MultipleCertStatusRequest', 'OCSPMustStaple']), self.ext4)

    def test_hash(self):
        self.assertEqual(hash(self.ext1), hash(self.ext1))
        self.assertEqual(hash(self.ext2), hash(self.ext2))
        self.assertEqual(hash(self.ext3), hash(self.ext3))

        self.assertNotEqual(hash(self.ext1), hash(self.ext2))
        self.assertNotEqual(hash(self.ext1), hash(self.ext3))
        self.assertNotEqual(hash(self.ext2), hash(self.ext3))

    def test_hash_order(self):
        self.assertEqual(hash(self.ext3), hash(self.ext4))

    def test_in(self):
        self.assertIn('OCSPMustStaple', self.ext1)
        self.assertIn('OCSPMustStaple', self.ext2)
        self.assertIn('OCSPMustStaple', self.ext3)
        self.assertIn('OCSPMustStaple', self.ext4)
        self.assertIn('MultipleCertStatusRequest', self.ext3)
        self.assertIn('MultipleCertStatusRequest', self.ext4)

        self.assertIn(TLSFeatureType.status_request, self.ext1)
        self.assertIn(TLSFeatureType.status_request, self.ext2)
        self.assertIn(TLSFeatureType.status_request_v2, self.ext3)

    def test_len(self):
        self.assertEqual(len(self.ext1), 1)
        self.assertEqual(len(self.ext2), 1)
        self.assertEqual(len(self.ext3), 2)
        self.assertEqual(len(self.ext4), 2)

    def test_ne(self):
        self.assertNotEqual(self.ext1, self.ext2)
        self.assertNotEqual(self.ext1, self.ext3)
        self.assertNotEqual(self.ext2, self.ext3)
        self.assertNotEqual(self.ext1, 10)

    def test_not_in(self):
        self.assertNotIn('MultipleCertStatusRequest', self.ext1)
        self.assertNotIn('MultipleCertStatusRequest', self.ext2)
        self.assertNotIn(TLSFeatureType.status_request_v2, self.ext1)
        self.assertNotIn(TLSFeatureType.status_request_v2, self.ext2)

    def test_repr(self):
        self.assertEqual(repr(self.ext1), "<TLSFeature: ['OCSPMustStaple'], critical=True>")
        self.assertEqual(repr(self.ext2), "<TLSFeature: ['OCSPMustStaple'], critical=False>")

        # Make sure that different order results in the same output
        self.assertEqual(repr(self.ext3),
                         "<TLSFeature: ['MultipleCertStatusRequest', 'OCSPMustStaple'], critical=False>")
        self.assertEqual(repr(self.ext4),
                         "<TLSFeature: ['MultipleCertStatusRequest', 'OCSPMustStaple'], critical=False>")

    def test_serialize(self):
        self.assertEqual(self.ext1.serialize(), {
            'critical': True,
            'value': ['OCSPMustStaple'],
        })
        self.assertEqual(self.ext2.serialize(), {
            'critical': False,
            'value': ['OCSPMustStaple'],
        })
        self.assertEqual(self.ext3.serialize(), {
            'critical': False,
            'value': ['OCSPMustStaple', 'MultipleCertStatusRequest'],
        })
        self.assertEqual(TLSFeature(self.ext1.serialize()), self.ext1)
        self.assertEqual(TLSFeature(self.ext2.serialize()), self.ext2)
        self.assertEqual(TLSFeature(self.ext3.serialize()), self.ext3)
        self.assertNotEqual(TLSFeature(self.ext1.serialize()), self.ext2)

    def test_str(self):
        exp_order = 'MultipleCertStatusRequest,OCSPMustStaple'
        self.assertEqual(str(self.ext1), 'OCSPMustStaple/critical')
        self.assertEqual(str(self.ext2), 'OCSPMustStaple')

        # Make sure that different order results in the same output
        self.assertEqual(str(self.ext3), exp_order)
        self.assertEqual(str(self.ext4), exp_order)

    def test_unknown_values(self):
        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): foo$'):
            TLSFeature('foo')
        with self.assertRaisesRegex(ValueError, r'^Unknown value\(s\): foo$'):
            TLSFeature('critical,foo')
