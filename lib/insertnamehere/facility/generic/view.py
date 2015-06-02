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

from collections import OrderedDict

from ...error import NoSuchRecord, UserError
from ...web.util import ErrorPage, HTTPNotFound, url_for
from .view_admin import GenericAdmin
from .view_proposal import GenericProposal


class Generic(GenericAdmin, GenericProposal):
    """
    Base class for Facility objects.
    """

    def __init__(self, id_):
        """
        Construct facility object.

        Takes the facility "id" as recorded in the database.  Instances of
        this class should be constructed by looking up the facility's "code"
        (from the get_code class method) in the database, then calling
        this constructor with the associated identifier.
        """

        self.id_ = id_

    @classmethod
    def get_code(cls):
        """
        Get the facility "code".

        This is a short string to uniquely identify the facility.  It will
        correspond to an entry in the "facility" table.
        """

        return 'generic'

    def get_name(self):
        """
        Get the name of the facility.
        """

        return 'Generic Facility'

    def view_facility_home(self, db):
        # Determine which semesters have open calls for proposals.
        # TODO: restrict to open calls.
        open_semesters = OrderedDict()
        for call in db.search_call(facility_id=self.id_).values():
            if call.semester_id not in open_semesters:
                open_semesters[call.semester_id] = call.semester_name

        return {
            'title': self.get_name(),
            'open_semesters': open_semesters,
        }

    def view_semester_calls(self, db, semester_id):
        try:
            semester = db.get_semester(self.id_, semester_id)
        except NoSuchRecord:
            raise HTTPNotFound('Semester not found')

        # TODO: restrict to open calls.
        calls = db.search_call(facility_id=self.id_, semester_id=semester_id)
        if not calls:
            raise ErrorPage('No calls are currently open for this semester.')

        return {
            'title': 'Call for Semester {0}'.format(semester.name),
            'semester': semester,
            'calls': calls.values(),
        }
