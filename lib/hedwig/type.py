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

from collections import OrderedDict, namedtuple
from math import sqrt
import re

from .astro.coord import CoordSystem, coord_from_dec_deg, coord_to_dec_deg, \
    format_coord, parse_coord
from .db.meta import affiliation, calculation, call, category, \
    email, facility, group_member, institution, institution_log, \
    member, message, moc, person, \
    prev_proposal, prev_proposal_pub, \
    proposal, proposal_category, queue, review, reviewer, \
    semester, target, user_log
from .error import FormattedError, NoSuchRecord, MultipleRecords, UserError

Affiliation = namedtuple(
    'Affiliation',
    [x.name for x in affiliation.columns] + ['weight'])

CalculatorInfo = namedtuple(
    'CalculatorInfo',
    ['id', 'code', 'name', 'calculator', 'modes'])

CalculatorMode = namedtuple(
    'CalculatorMode',
    ['code', 'name'])

CalculatorResult = namedtuple(
    'CalculatorResult',
    ['output', 'extra'])

CalculatorValue = namedtuple(
    'CalculatorValue',
    ['code', 'name', 'abbr', 'format', 'unit'])

Calculation = namedtuple(
    'Calculation',
    [x.name for x in calculation.columns])

Call = namedtuple(
    'Call',
    map(lambda x: x.name, call.columns) +
    ['facility_id', 'semester_name', 'queue_name',
     'queue_description', 'queue_description_format'])

Category = namedtuple(
    'Category',
    [x.name for x in category.columns])

Email = namedtuple(
    'Email',
    map(lambda x: x.name, email.columns))

Facility = namedtuple(
    'Facility',
    [x.name for x in facility.columns])

FacilityInfo = namedtuple(
    'FacilityInfo',
    ['id', 'code', 'name', 'view'])

GroupMember = namedtuple(
    'GroupMember',
    [x.name for x in group_member.columns] +
    ['person_name', 'person_public', 'person_registered',
     'institution_id', 'institution_name', 'institution_department',
     'institution_organization', 'institution_country'])

Institution = namedtuple(
    'Institution',
    map(lambda x: x.name, institution.columns))

InstitutionInfo = namedtuple(
    'InstitutionInfo',
    ['id', 'name', 'department', 'organization', 'country'])

InstitutionLog = namedtuple(
    'InstitutionLog',
    [x.name for x in institution_log.columns
     if not x.name.startswith('prev_')] +
    ['prev', 'person_name', 'institution_name'])

Link = namedtuple(
    'Link',
    ['text', 'url'])

Member = namedtuple(
    'Member',
    [x.name for x in member.columns if x.name not in ('institution_id',)] +
    ['person_name', 'person_public', 'person_registered',
     'affiliation_name',
     'resolved_institution_id',
     'institution_name', 'institution_department',
     'institution_organization', 'institution_country'])

MemberInfo = namedtuple(
    'MemberInfo',
    ['pi', 'editor', 'observer'])

MemberInstitution = namedtuple(
    'MemberInstitution',
    ['id', 'institution_id'])

MemberPIInfo = namedtuple(
    'MemberPIInfo',
    ['person_id', 'person_name', 'person_public', 'affiliation_name'])

Message = namedtuple(
    'Message',
    [x.name for x in message.columns] + ['recipients', 'state'])

MessageRecipient = namedtuple(
    'MessageRecipient',
    ['person_id', 'name', 'address', 'public'])

MOCInfo = namedtuple(
    'MOCInfo',
    [x.name for x in moc.columns])

Person = namedtuple(
    'Person',
    map(lambda x: x.name, person.columns) +
    ['email', 'institution', 'proposals', 'reviews'])

PersonInfo = namedtuple(
    'PersonInfo',
    [x.name for x in person.columns] +
    ['institution_name', 'institution_department',
     'institution_organization', 'institution_country'])

PrevProposal = namedtuple(
    'PrevProposal',
    [x.name for x in prev_proposal.columns] +
    ['publications'])

PrevProposalPub = namedtuple(
    'PrevProposalPub',
    [x.name for x in prev_proposal_pub.columns] + ['proposal_id'])

Proposal = namedtuple(
    'Proposal',
    map(lambda x: x.name, proposal.columns) + [
        'semester_id', 'semester_name', 'semester_code',
        'queue_id', 'queue_name', 'queue_code',
        'facility_id',
        'abst_word_lim',
        'tech_word_lim', 'tech_fig_lim', 'tech_page_lim',
        'sci_word_lim', 'sci_fig_lim', 'sci_page_lim',
        'capt_word_lim', 'expl_word_lim',
        'date_close',
        'decision_accept', 'decision_exempt', 'decision_ready',
        'members', 'reviewers', 'categories',
    ])

ProposalWithCode = namedtuple('ProposalWithCode',
                              Proposal._fields + ('code', 'facility_code'))

ProposalCategory = namedtuple(
    'ProposalCategory',
    [x.name for x in proposal_category.columns] + ['category_name'])

ProposalFigure = namedtuple(
    'ProposalFigure',
    ['data', 'type', 'filename'])

ProposalFigureInfo = namedtuple(
    'ProposalFigInfo',
    ['id', 'proposal_id', 'role', 'type', 'state', 'caption',
     'md5sum', 'filename', 'uploaded', 'uploader', 'uploader_name',
     'has_preview'])

ProposalFigureThumbPreview = namedtuple(
    'ProposalFigureThumbPreview', ['thumbnail', 'preview'])

ProposalPDFInfo = namedtuple(
    'ProposalPDFInfo',
    ['id', 'proposal_id', 'role', 'md5sum', 'state', 'pages',
     'filename', 'uploaded', 'uploader', 'uploader_name'])

ProposalText = namedtuple(
    'ProposalText',
    ['text', 'format'])

ProposalTextInfo = namedtuple(
    'ProposalTextInfo',
    ['id', 'proposal_id', 'role', 'format', 'words',
     'edited', 'editor', 'editor_name'])

Reviewer = namedtuple(
    'Reviewer',
    [x.name for x in reviewer.columns] +
    ['person_name', 'person_public', 'person_registered',
     'institution_id', 'institution_name', 'institution_department',
     'institution_organization', 'institution_country',
     'review_present'] +
    ['review_{}'.format(x.name) for x in review.columns
     if x != review.c.reviewer_id])

ReviewerInfo = namedtuple(
    'ReviewerInfo',
    ['id', 'role', 'review_present'])

Semester = namedtuple(
    'Semester',
    map(lambda x: x.name, semester.columns))

SemesterInfo = namedtuple(
    'SemesterInfo',
    ['id', 'facility_id', 'name', 'code', 'date_start', 'date_end'])

Target = namedtuple(
    'Target',
    [x.name for x in target.columns])

TargetObject = namedtuple('TargetObject', ('name', 'system', 'coord'))

TargetToolInfo = namedtuple(
    'TargetToolInfo',
    ['id', 'code', 'name', 'tool'])

UserInfo = namedtuple(
    'UserInfo',
    ['id', 'name'])

UserLog = namedtuple(
    'UserLog',
    [x.name for x in user_log.columns])

Queue = namedtuple(
    'Queue',
    map(lambda x: x.name, queue.columns))

QueueInfo = namedtuple(
    'Queue',
    ['id', 'facility_id', 'name', 'code'])

ValidationMessage = namedtuple(
    'ValidationMessage',
    ['is_error', 'description', 'link_text', 'link_url'])


class FormatType(object):
    PLAIN = 1
    RST = 2

    FormatTypeInfo = namedtuple('FormatTypeInfo', ('name', 'allow_user'))

    _info = OrderedDict((
        (PLAIN, FormatTypeInfo('Plain', True)),
        (RST,   FormatTypeInfo('RST',   False)),
    ))

    @classmethod
    def is_valid(cls, format_, is_system=False):
        """
        Determines whether the given format is allowed.

        By default only allows formats for which "allow_user" is enabled.
        However with the "is_system" flag, allows any format.
        """

        format_info = cls._info.get(format_, None)

        if format_info is None:
            return False

        return is_system or format_info.allow_user

    @classmethod
    def get_options(cls, is_system=False):
        """
        Get an OrderedDict of type names by type numbers.
        """

        return OrderedDict([(k, v.name) for (k, v) in cls._info.items()
                            if is_system or v.allow_user])


class Assessment(object):
    FEASIBLE = 1
    PROBLEM = 2
    INFEASIBLE = 3

    AssessmentInfo = namedtuple('AssessmentInfo', ('name',))

    _info = OrderedDict((
        (FEASIBLE,   AssessmentInfo('Feasible')),
        (PROBLEM,    AssessmentInfo('Problematic')),
        (INFEASIBLE, AssessmentInfo('Infeasible')),
    ))

    @classmethod
    def is_valid(cls, assessment):
        return assessment in cls._info

    @classmethod
    def get_name(cls, assessment):
        return cls._info[assessment].name

    @classmethod
    def get_options(cls):
        return OrderedDict(((k, v.name) for (k, v) in cls._info.items()))


class AttachmentState(object):
    NEW = 1
    PROCESSING = 2
    READY = 3
    ERROR = 4

    AttachmentStateInfo = namedtuple('AttachmentStateInfo',
                                     ('name', 'ready', 'error'))

    _info = OrderedDict((
        (NEW,         AttachmentStateInfo('New',        False, False)),
        (PROCESSING,  AttachmentStateInfo('Processing', False, False)),
        (READY,       AttachmentStateInfo('Ready',      True,  False)),
        (ERROR,       AttachmentStateInfo('Error',      False, True)),
    ))

    @classmethod
    def is_valid(cls, state):
        return state in cls._info

    @classmethod
    def get_name(cls, state):
        return cls._info[state].name

    @classmethod
    def is_ready(cls, state):
        return cls._info[state].ready

    @classmethod
    def is_error(cls, state):
        return cls._info[state].error

    @classmethod
    def unready_states(cls):
        return [k for (k, v) in cls._info.items() if not v.ready]


FileTypeInfo = namedtuple('FileTypeInfo',
                          ('name', 'mime', 'preview', 'allow_user'))


class FigureType(object):
    PNG = 1
    JPEG = 2
    PDF = 3
    PS = 4
    SVG = 5

    _info = OrderedDict((
        (PNG,  FileTypeInfo('PNG',  'image/png',              False, True)),
        (JPEG, FileTypeInfo('JPEG', 'image/jpeg',             False, True)),
        (PDF,  FileTypeInfo('PDF',  'application/pdf',        True,  True)),
        (PS,   FileTypeInfo('EPS',  'application/postscript', True,  False)),
        (SVG,  FileTypeInfo('SVG',  'image/svg+xml',          True,  False)),
    ))

    @classmethod
    def is_valid(cls, type_, is_system=False):
        """
        Determine if the given figure type is valid.

        By default only allows types where "allow_user" is enabled.
        """

        type_info = cls._info.get(type_, None)

        if type_info is None:
            return False

        return is_system or type_info.allow_user

    @classmethod
    def get_name(cls, type_):
        return cls._info[type_].name

    @classmethod
    def get_mime_type(cls, type_):
        return cls._info[type_].mime

    @classmethod
    def needs_preview(cls, type_):
        return cls._info[type_].preview

    @classmethod
    def from_mime_type(cls, mime_type):
        for (type_, info) in cls._info.items():
            if info.mime == mime_type:
                return type_

        raise UserError('File has type "{}" which is not recognised.',
                        mime_type)

    @classmethod
    def can_view_inline(cls, type_):
        """
        Determine whether the type of figure is suitable for sending to the
        browser to view inline.

        Currently implemented as any image/* MIME type or PDF, which
        means it returns True for all types at the time of writing.
        """

        return (type_ == cls.PDF or
                cls.get_mime_type(type_).startswith('image/'))

    @classmethod
    def allowed_type_names(cls):
        return [x.name for x in cls._info.values() if x.allow_user]

    @classmethod
    def allowed_mime_types(cls):
        return [x.mime for x in cls._info.values() if x.allow_user]


class GroupType(object):
    CTTEE = 1
    TECH = 2
    COORD = 3

    GroupInfo = namedtuple(
        'GroupInfo',
        ('name', 'view_all_prop', 'private_moc',
         'review_coord', 'review_view'))

    _info = OrderedDict((
        #                         Authorization: Prop   MOC    Rv Ed  Rv Vw
        (CTTEE, GroupInfo('Committee',           True,  False, False, True)),
        (TECH,  GroupInfo('Technical assessors', False, True,  False, False)),
        (COORD, GroupInfo('Review coordinators', True,  False, True,  True)),
    ))

    @classmethod
    def is_valid(cls, type_):
        return type_ in cls._info

    @classmethod
    def get_info(cls, type_):
        return cls._info[type_]

    @classmethod
    def get_options(cls):
        """
        Get an OrderedDict of type names by type numbers.
        """

        return OrderedDict(((k, v.name) for (k, v) in cls._info.items()))

    @classmethod
    def view_all_groups(cls):
        return [k for (k, v) in cls._info.items() if v.view_all_prop]

    @classmethod
    def private_moc_groups(cls):
        return [k for (k, v) in cls._info.items() if v.private_moc]

    @classmethod
    def review_coord_groups(cls):
        return [k for (k, v) in cls._info.items() if v.review_coord]

    @classmethod
    def review_view_groups(cls):
        return [k for (k, v) in cls._info.items() if v.review_view]


class MessageState(object):
    UNSENT = 1
    SENDING = 2
    SENT = 3

    StateInfo = namedtuple(
        'StateInfo', ('name',))

    _info = OrderedDict((
        (UNSENT,  StateInfo('Unsent')),
        (SENDING, StateInfo('Sending')),
        (SENT,    StateInfo('Sent')),
    ))

    @classmethod
    def get_options(cls):
        return OrderedDict(((k, v.name) for (k, v) in cls._info.items()))


class ProposalState(object):
    PREPARATION = 1
    SUBMITTED = 2
    WITHDRAWN = 3
    REVIEW = 4
    ABANDONED = 5
    ACCEPTED = 6
    REJECTED = 7

    StateInfo = namedtuple(
        'StateInfo', ('short_name', 'name', 'edit', 'submitted', 'reviewed'))

    #                 Abbr     Name              Edit   Sub/d  Rev/d
    _info = OrderedDict((
        (PREPARATION,
            StateInfo('Prep',  'In preparation', True,  False, False)),
        (SUBMITTED,
            StateInfo('Sub',   'Submitted',      True,  True,  False)),
        (WITHDRAWN,
            StateInfo('Wdwn',  'Withdrawn',      True,  False, False)),
        (REVIEW,
            StateInfo('Rev',   'Under review',   False, True,  False)),
        (ABANDONED,
            StateInfo('Abnd',  'Abandoned',      False, False, False)),
        (ACCEPTED,
            StateInfo('Acc',   'Accepted',       False, True,  True)),
        (REJECTED,
            StateInfo('Rej',   'Rejected',       False, True,  True)),
    ))

    @classmethod
    def is_submitted(cls, state):
        return cls._info[state].submitted

    @classmethod
    def is_reviewed(cls, state):
        return cls._info[state].reviewed

    @classmethod
    def is_valid(cls, state):
        return state in cls._info

    @classmethod
    def get_name(cls, state):
        return cls._info[state].name

    @classmethod
    def get_short_name(cls, state):
        return cls._info[state].short_name

    @classmethod
    def can_edit(cls, state):
        return cls._info[state].edit

    @classmethod
    def editable_states(cls):
        return [k for (k, v) in cls._info.items() if v.edit]

    @classmethod
    def submitted_states(cls):
        return [k for (k, v) in cls._info.items() if v.submitted]

    @classmethod
    def reviewed_states(cls):
        return [k for (k, v) in cls._info.items() if v.reviewed]

    @classmethod
    def by_name(cls, name):
        """
        Attempt to find a state value by name.

        Returns None if no match is found.
        """

        lowername = name.lower()
        for (state, info) in cls._info.items():
            if lowername == info.name.lower():
                return state

        return None


class PublicationType(object):
    PLAIN = 1
    DOI = 2
    ADS = 3
    ARXIV = 4

    PubTypeInfo = namedtuple('PubTypeInfo', ('name', 'placeholder', 'regex'))

    _info = OrderedDict((
        (PLAIN, PubTypeInfo('Text description',
                            '',
                            None)),
        (DOI,   PubTypeInfo('DOI',
                            '00.0000/XXXXXX',
                            [re.compile('^\d+\.\d+\/.*$')])),
        (ADS,   PubTypeInfo('ADS bibcode',
                            '0000..............X',
                            [re.compile('^\d\d\d\d..............[A-Za-z]$')])),
        (ARXIV, PubTypeInfo('arXiv article ID',
                            '0000.00000',
                            [re.compile('^\d+\.\d+$'),
                             re.compile('^.+\/\d+$')])),
    ))

    @classmethod
    def is_valid(cls, type_):
        return type_ in cls._info

    @classmethod
    def get_options(cls):
        return cls._info.copy()

    @classmethod
    def get_info(cls, type_):
        return cls._info[type_]


class ReviewerRole(object):
    TECH = 1
    EXTERNAL = 2
    CTTEE_PRIMARY = 3
    CTTEE_SECONDARY = 4
    CTTEE_OTHER = 5
    FEEDBACK = 6

    # Type which describes how the reviewer roles are defined, where:
    # * name_review indicates whether the name can be suffixed with "review".
    RoleInfo = namedtuple(
        'RoleInfo',
        ('name', 'unique', 'text', 'assessment', 'rating', 'weight',
         'cttee', 'name_review', 'feedback', 'note', 'display_class'))

    # Options:  Unique Text   Ass/nt Rating Weight Cttee  "Rev"  Feedbk Note
    _info = OrderedDict((
        (TECH,
            RoleInfo(
                'Technical',
                True,  True,  True,  False, False, False, True,  False, True,
                'tech')),
        (EXTERNAL,
            RoleInfo(
                'External',
                False, True,  False, True,  False, False, True,  False, False,
                'ext')),
        (CTTEE_PRIMARY,
            RoleInfo(
                'TAC Primary',
                True,  True,  False, True,  True,  True,  True,  True,  True,
                'cttee')),
        (CTTEE_SECONDARY,
            RoleInfo(
                'TAC Secondary',
                False, True,  False, True,  True,  True,  True,  True,  True,
                'cttee')),
        (CTTEE_OTHER,
            RoleInfo(
                'Rating',
                False, False, False, True,  True,  True,  False, False, False,
                'cttee')),
        (FEEDBACK,
            RoleInfo(
                'Feedback',
                True,  True,  False, False, False, False, False, False, False,
                'feedback')),
    ))

    @classmethod
    def is_valid(cls, role):
        return role in cls._info

    @classmethod
    def get_info(cls, role):
        return cls._info[role]

    @classmethod
    def get_cttee_roles(cls):
        return [k for (k, v) in cls._info.items() if v.cttee]

    @classmethod
    def get_feedback_roles(cls):
        """Get list of roles who can write the feedback review."""

        return [k for (k, v) in cls._info.items() if v.feedback]

    @classmethod
    def get_options(cls):
        """
        Get an OrderedDict of role names by role numbers.
        """

        return OrderedDict(((k, v.name) for (k, v) in cls._info.items()))


class TextRole(object):
    ABSTRACT = 1
    TECHNICAL_CASE = 2
    SCIENCE_CASE = 3
    TOOL_NOTE = 4

    RoleInfo = namedtuple('RoleInfo', ('name', 'shortname', 'url_path'))

    #                Name                        Short   Path
    _info = {
        ABSTRACT:
            RoleInfo('Abstract',                 'abst', None),
        TECHNICAL_CASE:
            RoleInfo('Technical Justification',  'tech', 'technical'),
        SCIENCE_CASE:
            RoleInfo('Scientific Justification', 'sci',  'scientific'),
        TOOL_NOTE:
            RoleInfo('Note on Tool Results',     'tool', None),
    }

    @classmethod
    def is_valid(cls, role):
        return role in cls._info

    @classmethod
    def get_name(cls, role):
        return cls._info[role].name

    @classmethod
    def short_name(cls, role):
        return cls._info[role].shortname

    @classmethod
    def url_path(cls, role):
        return cls._info[role].url_path

    @classmethod
    def get_url_paths(cls):
        return [v.url_path for v in cls._info.values()
                if v.url_path is not None]

    @classmethod
    def by_url_path(cls, url_path, default=()):
        """
        Attempt to find a role by URL path.

        Returns the given default, when specified, if no match is found.
        Otherwise an exception is raised.
        """

        for (role, info) in cls._info.items():
            if url_path == info.url_path:
                return role

        if default == ():
            raise FormattedError('Text role URL path "{}" not recognised',
                                 url_path)
        else:
            return default


class UserLogEvent(object):
    CREATE = 1
    LINK_PROFILE = 2
    CHANGE_NAME = 3
    CHANGE_PASS = 4
    GET_TOKEN = 5
    USE_TOKEN = 6
    USE_INVITE = 7

    EventInfo = namedtuple('EventInfo', ('description',))

    _info = {
        CREATE:       EventInfo('Account created'),
        LINK_PROFILE: EventInfo('Profile linked'),
        CHANGE_NAME:  EventInfo('Changed user name'),
        CHANGE_PASS:  EventInfo('Changed password'),
        GET_TOKEN:    EventInfo('Issued password reset code'),
        USE_TOKEN:    EventInfo('Used password reset code'),
        USE_INVITE:   EventInfo('Profile linked via invitation'),
    }

    @classmethod
    def is_valid(cls, event):
        return event in cls._info

    @classmethod
    def get_info(cls, event):
        return cls._info[event]


class ResultCollection(OrderedDict):
    def get_single(self, default=()):
        n = len(self)
        if n == 0:
            if default == ():
                raise NoSuchRecord('can not get single record: no results')
            else:
                return default
        elif n > 1:
            raise MultipleRecords('can not get single record: many results')
        else:
            # WARNING: Python-2 only.
            return self.values()[0]


class OrderedResultCollection(ResultCollection):
    """
    Subclass of ResultCollection for results from tables with a sort_order
    column.
    """

    def ensure_sort_order(self):
        """
        Ensure all records have a non-None sort_order entry.

        Iterates through the entries in this collection finding the maximum
        sort_order used and all the entries without a sort order.  Then those
        entries are assigned sort_order values above the previous maximum
        in the order in which they appear in the collection.
        """

        i = 0
        unordered = []

        for (key, value) in self.items():
            if value.sort_order is None:
                unordered.append(key)
            elif value.sort_order > i:
                i = value.sort_order

        for key in unordered:
            i += 1
            self[key] = self[key]._replace(sort_order=i)


ResultTable = namedtuple('ResultTable', ('table', 'columns', 'rows'))


class EmailCollection(ResultCollection):
    def get_primary(self):
        for email in self.values():
            if email.primary:
                return email

        raise KeyError('no primary address')

    def validate(self):
        """
        Attempts to validate a collection of email records.

        Checks:

        * There is exactly one primary address.
        * No email addresses are duplicated.

        Raises UserError for any problems found.
        """

        n_primary = 0
        seen_address = set()

        for email in self.values():
            if email.primary:
                n_primary += 1

            if email.address in seen_address:
                raise UserError('The address "{}" appears more than once.',
                                email.address)
            seen_address.add(email.address)

        if n_primary == 0:
            raise UserError('There is no primary address.')
        elif n_primary != 1:
            raise UserError('There is more than one primary address.')


class GroupMemberCollection(ResultCollection):
    def values_by_group_type(self, group_type):
        """
        Get a list of the reviewers with the given role.
        """

        return [x for x in self.values() if x.group_type == group_type]


class MemberCollection(OrderedResultCollection):
    def get_pi(self):
        for member in self.values():
            if member.pi:
                return member

        raise KeyError('no pi member')

    def get_person(self, person_id):
        for member in self.values():
            if member.person_id == person_id:
                return member

        raise KeyError('person not in member collection')

    def get_students(self):
        ans = []

        for member in self.values():
            if member.student:
                ans.append(member)

        return ans

    def validate(self, editor_person_id):
        """
        Attempts to validate the members of a proposal.

        Checks:

        * There is exactly one PI.
        * There is at least one editor.
        * The given person ID is an editor.  (To prevent people removing
          their own editor permission.)

        Raises UserError for any problems found.

        "editor_person_id" can be set to "None" to disable the person checks.
        """

        n_pi = 0
        n_editor = 0
        person_is_editor = None

        for member in self.values():
            if member.pi:
                n_pi += 1

            if member.editor:
                n_editor += 1

            if ((editor_person_id is not None) and
                    (member.person_id == editor_person_id)):
                person_is_editor = member.editor

        if n_pi == 0:
            raise UserError('There is no PI specified.')
        elif n_pi != 1:
            raise UserError('There is more than one PI specified.')

        if n_editor == 0:
            raise UserError('There are no specified editors.')

        if editor_person_id is not None:
            if person_is_editor is None:
                raise UserError(
                    'You can not remove yourself from the proposal.')
            elif not person_is_editor:
                raise UserError(
                    'You can not remove yourself as an editor.')


class PrevProposalCollection(ResultCollection):
    def validate(self):
        """
        Attempt to validate the previous proposal collection.

        Checks:

        * Each entry has a proposal code.
        * No entry has more than 6 publications.
        * No code or identifier is repeated.

        Raises UserError for any problems found.
        """

        seen_codes = set()
        seen_ids = {}

        for pp in self.values():
            if not pp.proposal_code:
                raise UserError(
                    'A proposal code must be specified for each entry.')

            if pp.proposal_code in seen_codes:
                raise UserError(
                    'Proposal code {} is listed more than once.',
                    pp.proposal_code)

            if pp.proposal_id is not None:
                if pp.proposal_id in seen_ids:
                    raise UserError(
                        'Proposal codes {} and {} appear to refer to '
                        'the same proposal.',
                        seen_ids[pp.proposal_id], pp.proposal_code)

            if len(pp.publications) > 6:
                raise UserError(
                    'More than 6 publications are specified for proposal {}.',
                    pp.proposal_code)

            for publication in pp.publications:
                if not publication.description:
                    raise UserError(
                        'Description missing for a publication for '
                        'proposal {}', pp.proposal_code)

                if not PublicationType.is_valid(publication.type):
                    raise UserError(
                        'Unknown publication type for publication "{}" '
                        '(for proposal {}).',
                        publication.description, pp.proposal_code)

                type_info = PublicationType.get_info(publication.type)
                if type_info.regex is not None:
                    for regex in type_info.regex:
                        if regex.search(publication.description):
                            break
                    else:
                        raise UserError(
                            '{} "{}" (for proposal {}) does not appear '
                            'to be valid.  An entry of the form "{}" was '
                            'expected.  If you are having trouble entering '
                            'this reference, please change the type to '
                            '"{}" to avoid this system trying to process it.',
                            type_info.name, publication.description,
                            pp.proposal_code, type_info.placeholder,
                            PublicationType.get_info(
                                PublicationType.PLAIN).name)

            # Record the code and identifier to check for duplicates.
            seen_codes.add(pp.proposal_code)

            if pp.proposal_id is not None:
                seen_ids[pp.proposal_id] = pp.proposal_code


class ProposalTextCollection(ResultCollection):
    def get_role(self, role, default=()):
        for pdf in self.values():
            if pdf.role == role:
                return pdf

        if default == ():
            raise KeyError('no text/PDF for this role')
        else:
            return default


class ProposalFigureCollection(ResultCollection):
    def values_by_role(self, role):
        """
        Return a list of values for the given role.
        """

        return [x for x in self.values() if x.role == role]


class ReviewerCollection(ResultCollection):
    def get_overall_rating(self, include_unweighted, with_std_dev):
        """
        Create weighted average of the ratings of completed reviews.

        If "unweighted" review roles are included, then these are
        weighted at 100%.

        If the standard deviation is requested, then this method
        returns a pair as (overall_rating, standard_deviation).
        """

        total_rating = 0.0
        total_weight = 0.0
        rating_and_weight = []

        for review in self.values():
            role_info = ReviewerRole.get_info(review.role)

            # Skip unweighted reviews if we don't want to include them.
            if not (include_unweighted or role_info.weight):
                continue

            # Skip incomplete reviews.
            if not review.review_present:
                continue
            if (not role_info.rating) or (review.review_rating is None):
                continue
            if role_info.weight and (review.review_weight is None):
                continue

            # Add to running totals.
            if role_info.weight:
                weight = (review.review_weight / 100.0)
            else:
                weight = 1.0

            total_rating += review.review_rating * weight
            total_weight += weight

            # Record the validated ratings with their weights in case
            # we want also to calculate the standard deviation.
            rating_and_weight.append((review.review_rating, weight))

        if not total_weight:
            return (None, None) if with_std_dev else None

        overall_rating = total_rating / total_weight

        if not with_std_dev:
            return overall_rating

        # If we require the standard deviation, iterate over the values
        # again to calculate the deviation from the weighted mean.
        total_dev = 0.0

        for (rating, weight) in rating_and_weight:
            total_dev += weight * ((rating - overall_rating) ** 2)

        std_dev = sqrt(total_dev / total_weight)

        return (overall_rating, std_dev)

    def get_person(self, person_id, roles=None):
        for member in self.values():
            if ((member.person_id == person_id) and
                    ((roles is None) or (member.role in roles))):
                return member

        raise KeyError('person not in reviewer collection')

    def person_id_by_role(self, role):
        """
        Get a list of the person identifiers for members of this
        reveiwer collection with the given role.
        """

        return [x.person_id for x in self.values() if x.role == role]

    def values_by_role(self, role):
        """
        Get a list of the reviewers with the given role.
        """

        return [x for x in self.values() if x.role == role]

    def values_in_role_order(self, cttee_role=None):
        """
        Iterate over the values of the collection in the order of
        the reviewer roles.

        Optionally return only committee roles (cttee_role=True) or
        non-committee roles (cttee_role=False).

        Note: operates by looping over known roles.  Any reviewers with
        invalid (or no longer recognised) roles will not be yielded.
        """

        roles = ReviewerRole.get_options().keys()

        cttee_roles = None
        if cttee_role is not None:
            cttee_roles = ReviewerRole.get_cttee_roles()

        for role in roles:
            if cttee_role is not None:
                if ((cttee_role and (role not in cttee_roles)) or
                        ((not cttee_role) and (role in cttee_roles))):
                    continue

            for member in self.values():
                if member.role == role:
                    yield member


class TargetCollection(OrderedResultCollection):
    def to_formatted_collection(self):
        ans = OrderedDict()

        for (k, v) in self.items():
            if v.x is None or v.y is None:
                x = y = ''
            else:
                (x, y) = format_coord(v.system,
                                      coord_from_dec_deg(v.system, v.x, v.y))

            if v.time is None:
                time = ''
            else:
                time = '{}'.format(v.time)

            if v.priority is None:
                priority = ''
            else:
                priority = '{}'.format(v.priority)

            ans[k] = v._replace(x=x, y=y, time=time, priority=priority)

        return ans

    @classmethod
    def from_formatted_collection(cls, records):
        ans = cls()

        for (k, v) in records.items():
            system = v.system

            if not v.name:
                raise UserError('Each target object should have a name.')

            if v.x and v.y:
                (x, y) = coord_to_dec_deg(parse_coord(system,
                                                      v.x, v.y, v.name))

            elif v.x or v.y:
                raise UserError('Target "{}" has only one coordinate.',
                                v.name)

            else:
                system = x = y = None

            try:
                if v.time:
                    time = float(v.time)
                else:
                    time = None
            except ValueError:
                raise UserError('Could not parse time for "{}".', v.name)

            try:
                if v.priority:
                    priority = int(v.priority)
                else:
                    priority = None
            except ValueError:
                raise UserError('Could not parse priority for "{}".', v.name)

            ans[k] = v._replace(system=system, x=x, y=y,
                                time=time, priority=priority)

        return ans

    def to_object_list(self):
        """
        Returns a list of target objects representing members of the
        collection for which coordinates have been defined.
        """

        ans = []

        for v in self.values():
            if not (v.x is None or v.y is None):
                ans.append(TargetObject(
                    v.name, v.system, coord_from_dec_deg(v.system, v.x, v.y)))

        return ans

    def total_time(self):
        """
        Returns the sum of the "time" value for each target in the collection
        for which this value isn't undefined.

        A total of 0.0 will be returned if no targets had defined times.  (Or
        if the times add up to zero.)
        """

        total = 0.0

        for v in self.values():
            if v.time is not None:
                total += v.time

        return total


def null_tuple(type_):
    """
    Make a named tuple instance of the given type with all entries
    set to None.
    """

    return type_(*((None,) * len(type_._fields)))


def with_can_edit(obj, can_edit):
    """
    Add a "can_edit" field to a tuple and set it to the given value.
    """

    return namedtuple(type(obj).__name__ + 'WithCE',
                      obj._fields + ('can_edit',))(*obj, can_edit=can_edit)
