# Copyright (C) 2015-2016 East Asian Observatory
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

from collections import namedtuple
from math import pi
import re

from healpy import ang2pix

from ...astro.coord import CoordSystem, format_coord
from ...error import NoSuchRecord
from ...view import auth
from ...view.tool import BaseTargetTool
from ...web.util import ErrorPage, HTTPNotFound
from ...type.enum import AttachmentState, FileTypeInfo
from ...type.util import null_tuple

TargetClash = namedtuple('TargetClash', ('target', 'mocs', 'target_search',
                                         'display_coord'))


class ClashTool(BaseTargetTool):
    @classmethod
    def get_code(cls):
        """
        Get the target tool "code".
        """

        return 'clash'

    def get_name(self):
        """
        Get the target tool's name.
        """

        return 'Clash Tool'

    def get_default_facility_code(self):
        """
        Get the code of the facility for which this target tool is
        designed.
        """

        return 'generic'

    def get_custom_routes(self):
        return [
            ('generic/moc_view.html',
             '/tool/clash/moc/<int:moc_id>',
             'tool_clash_moc_info',
             self.view_moc_info,
             {}),
            (None,
             '/tool/clash/moc/<int:moc_id>/fits',
             'tool_clash_moc_fits',
             self.view_moc_fits,
             {}),
            ('generic/moc_view_list.html',
             '/tool/clash/moc/',
             'tool_clash_moc_list',
             self.view_moc_list,
             {}),
        ]

    def _view_single(self, db, target_object, args):
        clashes = None
        non_clashes = None

        public = self._determine_public_constraint(db)
        moc_ready = self._check_mocs_exist_and_ready(db, public)

        if target_object is not None:
            (clashes, non_clashes) = self._do_moc_search(
                db, [target_object], public=public)

        return {
            'run_button': 'Search',
            'clashes': clashes,
            'non_clashes': non_clashes,
            'moc_ready': moc_ready,
            'target_moc_info': '.tool_clash_moc_info',
        }

    def _view_upload(self, db, target_objects, args):
        clashes = None
        non_clashes = None

        public = self._determine_public_constraint(db)
        moc_ready = self._check_mocs_exist_and_ready(db, public)

        if target_objects is not None:
            (clashes, non_clashes) = self._do_moc_search(
                db, target_objects, public=public)

        return {
            'run_button': 'Search',
            'clashes': clashes,
            'non_clashes': non_clashes,
            'moc_ready': moc_ready,
            'target_moc_info': '.tool_clash_moc_info',
        }

    def _view_proposal(self, db, proposal, target_objects, args):
        public = self._determine_public_constraint(db)
        moc_ready = self._check_mocs_exist_and_ready(db, public)

        (clashes, non_clashes) = self._do_moc_search(
            db, target_objects, public=public)

        return {
            'clashes': clashes,
            'non_clashes': non_clashes,
            'moc_ready': moc_ready,
            'target_moc_info': '.tool_clash_moc_info',
        }

    def _determine_public_constraint(self, db):
        """
        Determine the database search constraint we should use on the public
        field.

        The constraint should be that the public flag is true, unless the user
        has access to private mocs.
        """

        public = True

        if auth.for_private_moc(db, self.facility.id_):
            public = None

        return public

    def _check_mocs_exist_and_ready(self, db, public):
        """
        Raise an ErrorPage if there are no MOCs available and return True
        if all available MOCs are ready.
        """

        mocs = db.search_moc(facility_id=self.facility.id_, public=public)
        if not mocs:
            raise ErrorPage('No coverage maps have been set up yet.')

        return all(AttachmentState.is_ready(x.state) for x in mocs.values())

    def _do_moc_search(self, db, targets, public):
        order = self.facility.get_moc_order()
        clashes = []
        non_clashes = []

        for target in targets:
            # If the coordinates weren't entered in ICRS, use the
            # Astropy transformation to convert them.
            if target.system == CoordSystem.ICRS:
                coord = target.coord
            else:
                coord = target.coord.icrs

            ra_rad = coord.spherical.lon.rad
            dec_rad = coord.spherical.lat.rad
            cell = ang2pix(2 ** order, pi / 2 - dec_rad, ra_rad, nest=True)

            target_clashes = db.search_moc_cell(
                facility_id=self.facility.id_, public=public,
                order=order, cell=int(cell))

            archive_url = self.facility.make_archive_search_url(
                coord.spherical.lon.deg, coord.spherical.lat.deg)
            archive_url_text = ' '.join(format_coord(CoordSystem.ICRS, coord))

            if target_clashes:
                clashes.append(TargetClash(
                    target, target_clashes, archive_url, archive_url_text))

            else:
                non_clashes.append(TargetClash(
                    target, None, archive_url, archive_url_text))

        return (clashes, non_clashes)

    def view_moc_list(self, db, args, form):
        public = self._determine_public_constraint(db)

        mocs = db.search_moc(facility_id=self.facility.id_, public=public)

        return {
            'title': 'Coverage List',
            'mocs': mocs.values(),
        }

    def view_moc_info(self, db, args, form, moc_id):
        public = self._determine_public_constraint(db)

        try:
            moc = db.search_moc(
                facility_id=self.facility.id_, public=public,
                moc_id=moc_id, with_description=True).get_single()
        except NoSuchRecord:
            raise HTTPNotFound('Coverage map not found.')

        return {
            'title': 'Coverage: {}'.format(moc.name),
            'moc': moc,
        }

    def view_moc_fits(self, db, args, form, moc_id):
        public = self._determine_public_constraint(db)

        try:
            moc = db.search_moc(
                facility_id=self.facility.id_, public=public,
                moc_id=moc_id, with_description=False).get_single()
        except NoSuchRecord:
            raise HTTPNotFound('Coverage map not found.')

        try:
            moc_fits = db.get_moc_fits(moc_id)
        except NoSuchRecord:
            raise HTTPNotFound('The FITS file for this coverage map '
                               'appears to be missing.')

        return (
            moc_fits,
            null_tuple(FileTypeInfo)._replace(mime='application/fits'),
            '{}.fits'.format(re.sub('[^-_a-z0-9]', '_', moc.name.lower())))
