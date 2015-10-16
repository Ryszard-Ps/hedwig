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

from ..config import get_facilities
from ..email.format import render_email_template
from ..error import FormattedError, NoSuchRecord, UserError
from ..type import FormatType, MemberInstitution, ProposalState, ReviewerRole
from ..util import get_logger

logger = get_logger(__name__)


class FeedbackError(FormattedError):
    pass


def close_call_proposals(db, call_id):
    """
    Function to update the status of proposals at the closure of a
    call.

    * Sets the status to REVIEW (or ABANDONED if not submitted).
    * Writes the member institutions into the member table.
    """

    try:
        call = db.search_call(call_id=call_id, is_open=False).get_single()
    except NoSuchRecord:
        raise UserError('Call with id={} not found or still open.', call_id)

    for proposal in db.search_proposal(call_id=call_id,
                                       with_members=True).values():
        # Change the proposal state.
        new_state = None

        if proposal.state == ProposalState.SUBMITTED:
            new_state = ProposalState.REVIEW

        elif proposal.state in (ProposalState.PREPARATION,
                                ProposalState.WITHDRAWN):
            new_state = ProposalState.ABANDONED

        if new_state is not None:
            logger.info('Setting state of proposal {} to {}',
                        proposal.id, ProposalState.get_name(new_state))
            db.update_proposal(proposal.id, state=new_state)
        else:
            logger.warning('Proposal {} is in unexpected state "{}"',
                           proposal.id, ProposalState.get_name(proposal.state))

        # Freeze the current institution ID values in the member table.
        records = {}
        for member in proposal.members.values():
            records[member.id] = MemberInstitution(
                member.id, member.resolved_institution_id)

        logger.debug('Synchronizing institution_id values into member table')
        db.sync_proposal_member_institution(proposal.id, records)


def send_call_proposal_feedback(db, call_id, proposals):
    """
    Sends feedback for the given proposals.

    Applies the following action to each of the given proposals:

        * Sets the status to ACCEPTED or REJECTED based on the decision.
        * Write a feedback email message into the database including the
          feedback report.

    The proposals argument must be a list of Proposal objects including
    the feedback reviews and all members.
    """

    logger.debug('Preparing to send feedback for call {}', call_id)

    # Determine the facility class.
    logger.debug('Determining facility class for this call')
    try:
        facility_info = db.get_call_facility(call_id)
    except NoSuchRecord:
        logger.error('Call {} facility identifier unknown', call.id)
        return 0

    for facility_class in get_facilities():
        if facility_class.get_code() == facility_info.code:
            facility = facility_class(facility_info.id)
            break
    else:
        logger.error('Call {} facility {} not present',
                     call_id, facility_info.code)
        return 0

    # Iterate over proposals and send feedback.
    n_processed = 0

    for proposal in proposals:
        logger.debug('Preparing to send feedback for proposal {}', proposal.id)

        try:
            # Check that the proposal is still in the REVIEW state.
            if proposal.state != ProposalState.REVIEW:
                raise FeedbackError('Proposal {} is not under review',
                                    proposal.id)

            # Double-check facility assignment.
            if facility.id_ != proposal.facility_id:
                raise FeedbackError(
                    'Proposal {} has different facility from the call',
                    proposal.id)

            # Filter reviews in case the proposal record contains more than
            # just the feedback report.  Also check the reviews are plain text
            # so that we can include them in the email message.
            feedback = []
            for review in proposal.reviewers.values():
                if review.role != ReviewerRole.FEEDBACK:
                    continue

                if review.review_format != FormatType.PLAIN:
                    raise FeedbackError('Feedback review {} is not plain text',
                                        review.id)

                feedback.append(review.review_text)

            # Prepare email (but don't write now -- set the state first so
            # that, if something goes wrong, we don't get into a loop of
            # sending the email again every time we poll for feedback
            # which is ready to send).
            proposal_code = facility.make_proposal_code(db, proposal)
            email_subject = 'Proposal {} {}'.format(
                proposal_code,
                ('accepted' if proposal.decision_accept else 'rejected'))
            email_ctx = {
                'proposal': proposal,
                'proposal_code': proposal_code,
                'feedback': feedback,
            }
            email_ctx.update(facility.get_feedback_extra(db, proposal))
            email_body = render_email_template(
                'proposal_feedback.txt', email_ctx, facility=facility)

            # Change the proposal state.
            new_state = (ProposalState.ACCEPTED if proposal.decision_accept
                         else ProposalState.REJECTED)

            logger.info('Setting state of proposal {} to {}',
                        proposal.id, ProposalState.get_name(new_state))

            db.update_proposal(proposal.id, state=new_state)

            # Write feedback email message into the database.  Do this after
            # setting the state (see comment above for why).
            logger.debug('Writing feedback message for proposal {}',
                         proposal.id)

            db.add_message(email_subject, email_body,
                           [x.person_id for x in proposal.members.values()])

        except FeedbackError:
            logger.exception('Failed to send feedback for proposal {}',
                             proposal.id)

    return n_processed
