# Copyright (C) 2015 East Asian Observatory
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful,but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

from __future__ import absolute_import, division, print_function, \
    unicode_literals

from binascii import hexlify, unhexlify
from codecs import utf_8_encode
from hashlib import pbkdf2_hmac
import os

_rounds = 1000000


def create_password_hash(password_raw):
    """
    Create hash and salt for the given raw password.

    The password is encoded as UTF-8 and a salt read from "os.random".
    Returns ASCII hex representation of the hash and salt.
    """

    password_salt = os.urandom(32)
    password_hash = pbkdf2_hmac(
        'sha256', utf_8_encode(password_raw)[0], password_salt, _rounds)

    return (hexlify(password_hash), hexlify(password_salt))


def check_password_hash(password_raw, password_hash, password_salt):
    """
    Checks the given raw password against the hash and salt.

    Assumes that the hash and salt are given in ASCII hex representation
    and checks whether the password re-generates the hash when hashed
    using the salt.
    """

    return password_hash == hexlify(pbkdf2_hmac(
        'sha256', utf_8_encode(password_raw)[0], unhexlify(password_salt),
        _rounds))
