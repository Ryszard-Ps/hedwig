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

from insertnamehere.error import ConsistencyError, DatabaseIntegrityError, \
    UserError
from insertnamehere.type import Member, MemberCollection, Proposal, \
    ResultCollection
from .dummy_db import DBTestCase


class DBProposalTest(DBTestCase):
    def test_facility(self):
        # Test the ensure_facility method.
        facility_id = self.db.ensure_facility('my_tel')
        self.assertIsInstance(facility_id, int)

        facility_id_copy = self.db.ensure_facility('my_tel')
        facility_id_diff = self.db.ensure_facility('my_other_tel')

        self.assertEqual(facility_id_copy, facility_id)
        self.assertNotEqual(facility_id_diff, facility_id)

    def test_semester(self):
        # Test add_semeseter method.
        facility_id = self.db.ensure_facility('my_tel')
        self.assertIsInstance(facility_id, int)

        with self.assertRaisesRegexp(ConsistencyError, 'facility does not'):
            self.db.add_semester(999, '99A')

        semester_id = self.db.add_semester(facility_id, '99A')
        self.assertIsInstance(semester_id, int)

        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_semester(facility_id, '99A')

        semester_id_2 = self.db.add_semester(facility_id, '99B')
        self.assertIsInstance(semester_id_2, int)
        self.assertNotEqual(semester_id_2, semester_id)

        semesters = self.db.search_semester(facility_id=facility_id)
        self.assertIsInstance(semesters, ResultCollection)
        self.assertEqual(len(semesters), 2)

        # Try updating a record.
        self.assertEqual(self.db.get_semester(semester_id).name, '99A')
        self.db.update_semester(semester_id, name='99 (a)')
        self.assertEqual(self.db.get_semester(semester_id).name, '99 (a)')
        with self.assertRaisesRegexp(ConsistencyError, 'semester does not ex'):
            self.db.update_semester(999, name='bad semester')

    def test_queue(self):
        # Test add_queue method.
        facility_id = self.db.ensure_facility('my_tel')
        self.assertIsInstance(facility_id, int)

        with self.assertRaisesRegexp(ConsistencyError, 'facility does not'):
            self.db.add_queue(999, 'INT')

        queue_id = self.db.add_queue(facility_id, 'INT')
        self.assertIsInstance(queue_id, int)

        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_queue(facility_id, 'INT')

        queue_id_2 = self.db.add_queue(facility_id, 'XYZ')
        self.assertIsInstance(queue_id_2, int)
        self.assertNotEqual(queue_id_2, queue_id)

        # Try searching: add a queue for another facility first.
        facility_id_2 = self.db.ensure_facility('my_other_tel')
        queue_id_3 = self.db.add_queue(facility_id_2, '???')
        self.assertIsInstance(queue_id_3, int)
        queues = self.db.search_queue(facility_id=facility_id)
        self.assertIsInstance(queues, ResultCollection)
        self.assertEqual(list(queues.keys()), [queue_id, queue_id_2])
        queues = self.db.search_queue(facility_id=facility_id_2)
        self.assertEqual(list(queues.keys()), [queue_id_3])

        # Try updating a record.
        queue = self.db.get_queue(queue_id_3)
        self.assertEqual(queue.name, '???')
        self.db.update_queue(queue_id_3, name='!!!')
        queue = self.db.get_queue(queue_id_3)
        self.assertEqual(queue.name, '!!!')

    def test_call(self):
        # Check that we can create a call for proposals.
        facility_id = self.db.ensure_facility('my_tel')
        self.assertIsInstance(facility_id, int)
        semester_id = self.db.add_semester(facility_id, 'My Semester')
        self.assertIsInstance(semester_id, int)
        queue_id = self.db.add_queue(facility_id, 'My Queue')
        self.assertIsInstance(queue_id, int)

        call_id = self.db.add_call(semester_id, queue_id)
        self.assertIsInstance(call_id, int)

        # Check tests for bad values.
        with self.assertRaisesRegexp(ConsistencyError, 'semester does not'):
            self.db.add_call(999, queue_id)
        with self.assertRaisesRegexp(ConsistencyError, 'queue does not'):
            self.db.add_call(semester_id, 999)

        # Check uniqueness constraint.
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_call(semester_id, queue_id)

        # Check facility consistency check.
        facility_id_2 = self.db.ensure_facility('my_other_tel')
        semester_id_2 = self.db.add_semester(facility_id_2, 'My Semester')
        with self.assertRaisesRegexp(ConsistencyError,
                                     'inconsistent facility references'):
            self.db.add_call(semester_id_2, queue_id)

    def test_add_proposal(self):
        call_id_1 = self._create_test_call('semester1', 'queue1')
        self.assertIsInstance(call_id_1, int)
        call_id_2 = self._create_test_call('semester2', 'queue2')
        self.assertIsInstance(call_id_2, int)

        person_id = self.db.add_person('Person 1')
        self.assertIsInstance(person_id, int)

        # Create proposals and check the numbers are as expected.
        for call_id in (call_id_1, call_id_2):
            for i in range(1, 11):
                title = 'Proposal {0}'.format(i)
                proposal_id = self.db.add_proposal(call_id, person_id, title)
                self.assertIsInstance(proposal_id, int)

                proposal = self.db.get_proposal(proposal_id, with_members=True)
                self.assertIsInstance(proposal, Proposal)

                self.assertEqual(proposal.number, i)

                # Check remaining proposal records.
                self.assertEqual(proposal.id, proposal_id)
                self.assertEqual(proposal.title, title)
                self.assertEqual(proposal.call_id, call_id)
                self.assertIsInstance(proposal.members, MemberCollection)
                self.assertEqual(len(proposal.members), 1)
                member = proposal.members.get_single()
                self.assertIsInstance(member, Member)
                self.assertEqual(member.person_id, person_id)
                self.assertEqual(member.proposal_id, proposal_id)
                self.assertTrue(member.pi)
                self.assertTrue(member.editor)
                self.assertFalse(member.observer)

        # The proposal must have a title.
        with self.assertRaisesRegexp(UserError, 'blank'):
            self.db.add_proposal(call_id_1, person_id, '')

        # Check for error raised when the call or person doesn't exist.
        with self.assertRaisesRegexp(ConsistencyError, '^call does not'):
            self.db.add_proposal(999, person_id, 'Title')
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_proposal(999, person_id, 'Title',
                                 _test_skip_check=True)

        with self.assertRaisesRegexp(ConsistencyError, '^person does not'):
            self.db.add_proposal(call_id, 999, 'Title')
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_proposal(call_id, 999, 'Title', _test_skip_check=True)

    def test_add_member(self):
        # Create test records and check we have integer identifiers for all.
        call_id = self._create_test_call('semester1', 'queue1')
        person_id_1 = self.db.add_person('Person 1')
        person_id_2 = self.db.add_person('Person 2')
        person_id_3 = self.db.add_person('Person 3')
        proposal_id = self.db.add_proposal(call_id, person_id_1, 'Proposal 1')

        for id_ in (call_id, person_id_1, person_id_2, person_id_3,
                    proposal_id):
            self.assertIsInstance(id_, int)

        # Check the member list as we add members one at a time.
        result = self.db.search_member(proposal_id=proposal_id)
        self.assertEqual(_member_person_set(result), [person_id_1])

        self.db.add_member(proposal_id, person_id_2, False, False, True)
        result = self.db.search_member(proposal_id=proposal_id)
        self.assertEqual(_member_person_set(result),
                         [person_id_1, person_id_2])

        self.db.add_member(proposal_id, person_id_3, False, True, True)
        result = self.db.search_member(proposal_id=proposal_id)
        self.assertEqual(_member_person_set(result),
                         [person_id_1, person_id_2, person_id_3])

        self.assertEqual(result.get_pi().person_id, person_id_1)

        # Ensure we can't add a member twice.
        with self.assertRaises(DatabaseIntegrityError):
            self.db.add_member(proposal_id, person_id_2, False, False, False)

        # Try searching instead by person_id.
        result = self.db.search_member(person_id=person_id_2)
        member = result.get_single()
        self.assertEqual(member.proposal_id, proposal_id)
        self.assertEqual(member.person_id, person_id_2)

    def _create_test_call(self, semester_name, queue_name):
        facility_id = self.db.ensure_facility('my_tel')
        self.assertIsInstance(facility_id, int)
        semester_id = self.db.add_semester(facility_id, semester_name)
        self.assertIsInstance(semester_id, int)
        queue_id = self.db.add_queue(facility_id, queue_name)
        self.assertIsInstance(queue_id, int)

        call_id = self.db.add_call(semester_id, queue_id)
        self.assertIsInstance(call_id, int)

        return call_id


def _member_person_set(member_collection):
    return map(lambda x: x.person_id, member_collection.values())