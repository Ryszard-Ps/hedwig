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

from sqlalchemy.sql import select
from sqlalchemy.sql.functions import count

from ...db.meta import call, proposal
from ...error import ConsistencyError, FormattedError, UserError
from .meta import jcmt_available, jcmt_allocation, jcmt_options, \
    jcmt_request, jcmt_review
from .type import \
    JCMTAvailable, JCMTAvailableCollection, \
    JCMTOptions, JCMTRequest, JCMTRequestCollection, \
    JCMTReview, JCMTReviewerExpertise


class JCMTPart(object):
    def get_jcmt_options(self, proposal_id):
        """
        Retrieve the JCMT proposal options for a given proposal.
        """

        with self._transaction() as conn:
            row = conn.execute(jcmt_options.select().where(
                jcmt_options.c.proposal_id == proposal_id)).first()

            if row is None:
                return None

            else:
                return JCMTOptions(**row)

    def get_jcmt_review(self, reviewer_id):
        """
        Retrieve the JCMT-specific parts of a review.
        """

        with self._transaction() as conn:
            row = conn.execute(jcmt_review.select().where(
                jcmt_review.c.reviewer_id == reviewer_id)).first()

            if row is None:
                return None

            else:
                return JCMTReview(**row)

    def search_jcmt_allocation(self, proposal_id):
        """
        Retrieve the observing allocations for the given proposal.
        """

        ans = JCMTRequestCollection()

        stmt = jcmt_allocation.select().where(
            jcmt_allocation.c.proposal_id == proposal_id)

        with self._transaction() as conn:
            for row in conn.execute(stmt.order_by(jcmt_allocation.c.id.asc())):
                ans[row['id']] = JCMTRequest(**row)

        return ans

    def search_jcmt_available(self, call_id):
        """
        Retrieve information about the observing time available (normally
        for a given call for proposals).
        """

        stmt = jcmt_available.select()

        if call_id is not None:
            stmt = stmt.where(jcmt_available.c.call_id == call_id)

        ans = JCMTAvailableCollection()

        with self._transaction() as conn:
            for row in conn.execute(stmt.order_by(jcmt_available.c.id.asc())):
                ans[row['id']] = JCMTAvailable(**row)

        return ans

    def search_jcmt_request(self, proposal_id):
        """
        Retrieve the observing requests for the given proposal.
        """

        ans = JCMTRequestCollection()

        stmt = jcmt_request.select().where(
            jcmt_request.c.proposal_id == proposal_id)

        with self._transaction() as conn:
            for row in conn.execute(stmt.order_by(jcmt_request.c.id.asc())):
                ans[row['id']] = JCMTRequest(**row)

        return ans

    def set_jcmt_options(self, proposal_id, target_of_opp, daytime,
                         time_specific, polarimetry):
        """
        Set the JCMT proposal options for a given proposal.
        """

        values = {
            jcmt_options.c.target_of_opp: target_of_opp,
            jcmt_options.c.daytime: daytime,
            jcmt_options.c.time_specific: time_specific,
            jcmt_options.c.polarimetry: polarimetry,
        }

        with self._transaction() as conn:
            if 0 < conn.execute(select(
                    [count(jcmt_options.c.proposal_id)]).where(
                        jcmt_options.c.proposal_id == proposal_id)).scalar():
                # Update existing options.
                result = conn.execute(jcmt_options.update().where(
                    jcmt_options.c.proposal_id == proposal_id
                ).values(values))

                if result.rowcount != 1:
                    raise ConsistencyError(
                        'no rows matched updating JCMT options')

            else:
                # Add new options record.
                values.update({
                    jcmt_options.c.proposal_id: proposal_id,
                })

                conn.execute(jcmt_options.insert().values(values))

    def set_jcmt_review(self, role_class, reviewer_id, expertise, is_update):
        if expertise is not None:
            if not JCMTReviewerExpertise.is_valid(expertise):
                raise UserError('Reviewer expertise level not recognised.')

        values = {
            jcmt_review.c.expertise: expertise,
        }

        with self._transaction() as conn:
            # Determine type of review and check values are valid for it.
            reviewer = self.search_reviewer(
                role_class, reviewer_id=reviewer_id, _conn=conn).get_single()

            role_info = role_class.get_info(reviewer.role)
            attr_req = {
                jcmt_review.c.expertise: role_info.jcmt_expertise,
            }

            for (attr, attr_allowed) in attr_req.items():
                if attr_allowed:
                    if values[attr] is None:
                        raise FormattedError(
                            '{} should be specified', attr.name)
                else:
                    if values[attr] is not None:
                        raise FormattedError(
                            '{} should not be specified', attr.name)

            # Check if the review already exists.
            already_exists = self._exists_jcmt_review(
                conn, reviewer_id=reviewer_id)
            if is_update and not already_exists:
                raise ConsistencyError(
                    'JCMT review does not exist for reviewer {}', reviewer_id)
            elif already_exists and not is_update:
                raise ConsistencyError(
                    'JCMT review already exists for reviewer {}', reviewer_id)

            # Perform the insert/update.
            if is_update:
                result = conn.execute(jcmt_review.update().where(
                    jcmt_review.c.reviewer_id == reviewer_id
                ).values(values))

                if result.rowcount != 1:
                    raise ConsistencyError(
                        'no rows matched updating JCMT review {}', reviewer_id)

            else:
                values.update({
                    jcmt_review.c.reviewer_id: reviewer_id,
                })

                result = conn.execute(jcmt_review.insert().values(values))

    def sync_jcmt_call_available(self, call_id, records,
                                 _test_skip_check=False):
        """
        Update the records of the amount of time available for a call.
        """

        records.validate()

        with self._transaction() as conn:
            if not _test_skip_check and \
                    not self._exists_id(conn, call, call_id):
                raise ConsistencyError(
                    'call does not exist with id={}', call_id)

            return self._sync_records(
                conn, jcmt_available, jcmt_available.c.call_id, call_id,
                records, unique_columns=(jcmt_available.c.weather,))

    def sync_jcmt_proposal_allocation(self, proposal_id, records,
                                      _test_skip_check=False):
        """
        Update the observing allocations for the given proposal to match
        the specified records.
        """

        records.validate()

        with self._transaction() as conn:
            if not _test_skip_check and \
                    not self._exists_id(conn, proposal, proposal_id):
                raise ConsistencyError(
                    'proposal does not exist with id={}', proposal_id)

            return self._sync_records(
                conn, jcmt_allocation, jcmt_allocation.c.proposal_id,
                proposal_id, records, unique_columns=(
                    jcmt_allocation.c.instrument, jcmt_allocation.c.weather))

    def sync_jcmt_proposal_request(self, proposal_id, records,
                                   _test_skip_check=False):
        """
        Update the observing requests for the given proposal to match
        the specified records.
        """

        records.validate()

        with self._transaction() as conn:
            if not _test_skip_check and \
                    not self._exists_id(conn, proposal, proposal_id):
                raise ConsistencyError(
                    'proposal does not exist with id={}', proposal_id)

            return self._sync_records(
                conn, jcmt_request, jcmt_request.c.proposal_id, proposal_id,
                records, unique_columns=(
                    jcmt_request.c.instrument, jcmt_request.c.weather))

    def _exists_jcmt_review(self, conn, reviewer_id):
        """
        Test whether a JCMT review record exists.
        """

        return 0 < conn.execute(select([
            count(jcmt_review.c.reviewer_id)
        ]).where(
            jcmt_review.c.reviewer_id == reviewer_id
        )).scalar()
