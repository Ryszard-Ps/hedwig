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


class Error(Exception):
    """Base class for exceptions in this application."""

    pass


class DatabaseError(Error):
    """Base class for exceptions raised by the database."""

    def __init__(self, orig):
        """
        Construct exception using the message from an original exception,
        which itself is stored as the "orig" attribute.
        """

        Error.__init__(self, orig.message)
        self.orig = orig


class DatabaseIntegrityError(DatabaseError):
    """Error for database integrity failures."""
    pass


class FormattedError(Error):
    """Base class for exceptions with formatted messages."""
    def __init__(self, fmt_string, *fmt_args):
        """
        Construct exception with a message generated using string
        formatting based on the given string and taking the remaining
        arguments as the formatting parameters.
        """

        Error.__init__(self, fmt_string.format(*fmt_args))


class ConsistencyError(FormattedError):
    """Error for when the applications detects database inconsistency."""
    pass


class UserError(FormattedError):
    """
    Exception class for errors which are presumed to result from user
    input and with a message suitable for display to the user.
    """

    pass
