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

from collections import OrderedDict, namedtuple
from itertools import groupby

from ..type import ProposalWithCode


def prepare_home(application_name, facilities):
    return {
        'title': application_name,
        'facilities': facilities.values(),
    }


def prepare_dashboard(db, person_id, facilities):

    proposals = db.search_proposal(person_id=person_id)

    facility_proposals = OrderedDict()

    for id_, ps in groupby(proposals.values(), lambda x: x.facility_id):
        facility = facilities[id_]
        facility_proposals[facility.name] = [
            ProposalWithCode(*p, code=facility.view.make_proposal_code(db, p),
                             facility_code=facility.code)
            for p in ps]

    return {
        'title': 'Personal Dashboard',
        'proposals': facility_proposals,
    }