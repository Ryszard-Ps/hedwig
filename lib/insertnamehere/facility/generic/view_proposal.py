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

from ...astro.coord import CoordSystem
from ...email.format import render_email_template
from ...error import NoSuchRecord, UserError
from ...type import Affiliation, Call, \
    ProposalState, ProposalText, ProposalTextRole, \
    Queue, ResultCollection, Semester, Target, TargetCollection
from ...util import get_countries
from ...view import auth
from ...web.util import ErrorPage, HTTPError, HTTPForbidden, \
    HTTPNotFound, HTTPRedirect, \
    flash, session, url_for
from ...view.util import organise_collection, with_proposal


class GenericProposal(object):
    def view_proposal_new(self, db, call_id, form, is_post):
        try:
            call = db.search_call(
                facility_id=self.id_, call_id=call_id, is_open=True
            ).get_single()
        except NoSuchRecord:
            raise HTTPNotFound('Call not found')
        except MultipleRecords:
            raise HTTPError('Multiple calls found')

        affiliations = db.search_affiliation(
            queue_id=call.queue_id, hidden=False)
        if not affiliations:
            raise HTTPError('No affiliations appear to be available.')

        message = None

        proposal_title = ''
        affiliation_id = None

        if is_post:
            proposal_title = form['proposal_title']

            affiliation_id = int(form['affiliation_id'])
            if affiliation_id not in affiliations:
                raise ErrorPage('Invalid affiliation selected.')

            try:
                proposal_id = db.add_proposal(
                    call_id=call_id, person_id=session['person']['id'],
                    affiliation_id=affiliation_id,
                    title=proposal_title)
                flash('Your new proposal has been created.')
                raise HTTPRedirect(url_for('.proposal_view',
                                           proposal_id=proposal_id))

            except UserError as e:
                message = e.message

        return {
            'title': 'New Proposal',
            'call': call,
            'message': message,
            'proposal_title': proposal_title,
            'affiliations': affiliations.values(),
            'affiliation_id': affiliation_id
        }

    @with_proposal(permission='view')
    def view_proposal_view(self, db, proposal, can):
        countries = get_countries()

        ctx = {
            'title': proposal.title,
            'can_edit': can.edit,
            'is_submitted': ProposalState.is_submitted(proposal.state),
            'proposal': proposal._replace(members=[
                x._replace(institution_country=countries.get(
                    x.institution_country, 'Unknown country'))
                for x in proposal.members.values()]),
            'proposal_code': self.make_proposal_code(db, proposal),
        }

        ctx.update(self._view_proposal_extra(db, proposal))

        return ctx

    def _view_proposal_extra(self, db, proposal):
        """
        Method to gather additional information for the proposal view page.

        Sub-classes can override this method to add additional information
        to the proposal.
        """

        abstract = None
        try:
            abstract = db.get_proposal_text(proposal.id,
                                            ProposalTextRole.ABSTRACT)
        except NoSuchRecord:
            pass

        targets = [
            x._replace(system=CoordSystem.get_name(x.system)) for x in
            db.search_target(
                proposal_id=proposal.id).to_formatted_collection().values()]

        return {
            'abstract': abstract,
            'targets': targets,
        }

    @with_proposal(permission='edit')
    def view_proposal_submit(self, db, proposal, can, form, is_post):
        if ProposalState.is_submitted(proposal.state):
            raise ErrorPage('The proposal has already been submitted.')

        # TODO: validate proposal before allowing submission.

        if is_post:
            if 'submit_confirm' in form:
                db.update_proposal(proposal.id, state=ProposalState.SUBMITTED)

                proposal_code = self.make_proposal_code(db, proposal)

                db.add_message(
                    'Proposal {0} submitted'.format(proposal_code),
                    render_email_template(
                        'proposal_submitted.txt', {
                            'proposal': proposal,
                            'proposal_code': proposal_code,
                            'target_url': url_for(
                                '.proposal_view',
                                proposal_id=proposal.id, _external=True),
                        },
                        facility=self),
                    [x.person_id for x in proposal.members.values()])

                flash('The proposal has been submitted.')

            else:
                flash('The submission process has been cancelled.')

            raise HTTPRedirect(url_for('.proposal_view',
                                       proposal_id=proposal.id))

        return {
            'title': 'Submit Proposal',
            'proposal': proposal,
        }

    @with_proposal(permission='edit')
    def view_proposal_withdraw(self, db, proposal, can, form, is_post):
        if not ProposalState.is_submitted(proposal.state):
            raise ErrorPage('The proposal has not been submitted.')

        if is_post:
            if 'submit_confirm' in form:
                db.update_proposal(proposal.id, state=ProposalState.WITHDRAWN)

                proposal_code = self.make_proposal_code(db, proposal)

                db.add_message(
                    'Proposal {0} withdrawn'.format(proposal_code),
                    render_email_template(
                        'proposal_withdrawn.txt', {
                            'proposal': proposal,
                            'proposal_code': proposal_code,
                        },
                        facility=self),
                    [x.person_id for x in proposal.members.values()])

                flash('The proposal has been withdrawn.')

            else:
                flash('The withdrawl process has been cancelled.')

            raise HTTPRedirect(url_for('.proposal_view',
                                       proposal_id=proposal.id))

        return {
            'title': 'Withdraw Proposal',
            'proposal': proposal,
        }

    @with_proposal(permission='edit')
    def view_title_edit(self, db, proposal, can, form, is_post):
        message = None

        if is_post:
            try:
                proposal = proposal._replace(title=form['proposal_title'])
                db.update_proposal(proposal.id, title=proposal.title)
                flash('The proposal title has been changed.')
                raise HTTPRedirect(url_for('.proposal_view',
                                           proposal_id=proposal.id))

            except UserError as e:
                message = e.message

        return {
            'title': 'Edit Title',
            'message': message,
            'proposal': proposal,
        }

    @with_proposal(permission='edit')
    def view_abstract_edit(self, db, proposal, can, form, is_post):
        message = None

        try:
            abstract = db.get_proposal_text(proposal.id,
                                            ProposalTextRole.ABSTRACT)
            is_update = True
        except NoSuchRecord:
            abstract = ProposalText('', 'plain')
            is_update = False

        if is_post:
            abstract = abstract._replace(text=form['text'],
                                         format=form['format'])

            try:
                db.set_proposal_text(proposal.id, ProposalTextRole.ABSTRACT,
                                     abstract.text, abstract.format, is_update)
                flash('The abstract has been saved.')
                raise HTTPRedirect(url_for('.proposal_view',
                                           proposal_id=proposal.id))

            except UserError as e:
                message = e.message

        return {
            'title': 'Edit Abstract',
            'message': message,
            'proposal_id': proposal.id,
            'text': abstract,
            'target': url_for('.abstract_edit', proposal_id=proposal.id),
        }

    @with_proposal(permission='edit')
    def view_member_edit(self, db, proposal, can, form, is_post):
        message = None
        records = proposal.members

        affiliations = db.search_affiliation(
            queue_id=proposal.queue_id, hidden=False)
        if not affiliations:
            raise HTTPError('No affiliations appear to be available.')

        if is_post:
            if 'pi' in form:
                pi = int(form['pi'])
            else:
                pi = None

            try:
                # Create a new list from the items so that it is safe
                # to update and/or delete from records (for Python-3).
                for (id_, record) in list(records.items()):

                    # The affiliation_id should always be present, so use it
                    # to detect members who have been deleted from the form.
                    affiliation_str = form.get('affiliation_{0}'.format(id_))
                    if affiliation_str is None:
                        del records[id_]
                        continue

                    records[id_] = record._replace(
                        pi=(id_ == pi),
                        editor=('editor_{0}'.format(id_) in form),
                        observer=('observer_{0}'.format(id_) in form),
                        affiliation_id=int(affiliation_str))

                db.sync_proposal_member(
                    proposal.id, records,
                    editor_person_id=session['person']['id'])

                flash('The proposal member list has been updated.')
                raise HTTPRedirect(url_for('.proposal_view',
                                           proposal_id=proposal.id))

            except UserError as e:
                message = e.message

        return {
            'title': 'Edit Members',
            'message': message,
            'proposal_id': proposal.id,
            'members': records.values(),
            'affiliations': affiliations.values(),
        }

    @with_proposal(permission='edit')
    def view_member_add(self, db, proposal, can, form, is_post):
        message_link = message_invite = None
        member = dict(editor=None, observer=None, person_id=None,
                      name='', email='')

        affiliations = db.search_affiliation(
            queue_id=proposal.queue_id, hidden=False)
        if not affiliations:
            raise HTTPError('No affiliations appear to be available.')

        if is_post:
            member['editor'] = 'editor' in form
            member['observer'] = 'observer' in form
            if 'person_id' in form:
                member['person_id'] = int(form['person_id'])
            member['name'] = form.get('name', '')
            member['email'] = form.get('email', '')
            member['affiliation_id'] = int(form['affiliation_id'])

            if 'submit-link' in form:
                try:
                    if member['person_id'] is None:
                        raise UserError(
                            'No-one was selected from the directory.')

                    try:
                        person = db.get_person(person_id=member['person_id'])
                    except NoSuchRecord:
                        raise ErrorPage('This person\'s record was not found')

                    if not person.public:
                        raise ErrorPage('This person\'s record is private.')

                    db.add_member(proposal.id, member['person_id'],
                                  member['affiliation_id'],
                                  editor=member['editor'],
                                  observer=member['observer'])

                    db.add_message(
                        'Proposal {0} invitation'.format(
                            self.make_proposal_code(db, proposal)),
                        render_email_template(
                            'proposal_invitation.txt', {
                                'proposal': proposal,
                                'recipient_name': person.name,
                                'inviter_name': session['person']['name'],
                                'target_url': url_for(
                                    '.proposal_view',
                                    proposal_id=proposal.id, _external=True),
                            },
                            facility=self),
                        [member['person_id']])

                    flash('{0} has been added to the proposal.', person.name)
                    raise HTTPRedirect(url_for('.proposal_view',
                                       proposal_id=proposal.id))

                except UserError as e:
                    message_link = e.message

            elif 'submit-invite' in form:
                try:
                    if not member['name']:
                        raise UserError('Please enter the person\'s name.')
                    if not member['email']:
                        raise UserError('Please enter an email address.')

                    person_id = db.add_person(member['name'])
                    db.add_email(person_id, member['email'], primary=True)
                    db.add_member(proposal.id, person_id,
                                  member['affiliation_id'],
                                  editor=member['editor'],
                                  observer=member['observer'])
                    (token, expiry) = db.add_invitation(person_id)

                    db.add_message(
                        'Proposal {0} invitation'.format(
                            self.make_proposal_code(db, proposal)),
                        render_email_template(
                            'proposal_invitation.txt', {
                                'token': token,
                                'expiry': expiry,
                                'proposal': proposal,
                                'recipient_name': member['name'],
                                'inviter_name': session['person']['name'],
                                'target_url': url_for(
                                    'people.invitation_token_enter',
                                    token=token, _external=True),
                                'target_plain': url_for(
                                    'people.invitation_token_enter',
                                    _external=True),
                            },
                            facility=self),
                        [person_id])

                    flash('{0} has been added to the proposal.',
                          member['name'])

                    # Return to the proposal page after editing the new
                    # member's institution.
                    session['next_page'] = url_for('.proposal_view',
                                                   proposal_id=proposal.id)

                    raise HTTPRedirect(url_for(
                        'people.person_edit_institution', person_id=person_id))

                except UserError as e:
                    message_invite = e.message

            else:
                raise ErrorPage('Unknown action.')

        # Prepare list of people to display as the registered member
        # directory, filtering out current proposal members.
        countries = get_countries()
        current_persons = [m.person_id for m in proposal.members.values()]
        persons = [
            p._replace(institution_country=countries.get(
                p.institution_country))
            for p in db.search_person(registered=True, public=True,
                                      with_institution=True).values()
            if p.id not in current_persons
        ]

        return {
            'title': 'Add Member',
            'message_link': message_link,
            'message_invite': message_invite,
            'proposal_id': proposal.id,
            'persons': persons,
            'affiliations': affiliations.values(),
            'member': member,
        }

    @with_proposal(permission='edit')
    def view_target_edit(self, db, proposal, can, form, is_post):
        message = None

        records = db.search_target(
            proposal_id=proposal.id).to_formatted_collection()

        if is_post:
            # Temporary dictionaries for new records.
            updated_records = {}
            added_records = {}

            for param in form:
                if not param.startswith('name_'):
                    continue
                id_ = param[5:]

                if id_.startswith('new_'):
                    target_id = int(id_[4:])
                    destination = added_records
                else:
                    target_id = int(id_)
                    destination = updated_records

                destination[target_id] = Target(
                    target_id, proposal.id, form[param],
                    int(form['system_' + id_]),
                    form['x_' + id_],
                    form['y_' + id_])

            records = organise_collection(TargetCollection, updated_records,
                                          added_records)

            try:
                db.sync_proposal_target(
                    proposal.id,
                    TargetCollection.from_formatted_collection(records))

                flash('The target object list has been saved.')

                raise HTTPRedirect(url_for('.proposal_view',
                                           proposal_id=proposal.id))

            except UserError as e:
                message = e.message

        return {
            'title': 'Edit Targets',
            'proposal_id': proposal.id,
            'message': message,
            'systems': CoordSystem.get_options(),
            'targets': records.values(),
        }

    @with_proposal(permission='edit')
    def view_request_edit(self, db, proposal, can, form, is_post):
        raise ErrorPage('Observing request not implemented for this facility.')
