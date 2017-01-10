from __future__ import absolute_import, division, print_function, \
    unicode_literals

from collections import OrderedDict
import time

from rsr_calculator import RSR

from ...type.enum import ProposalState
from ...web.util import HTTPError, HTTPForbidden, HTTPNotFound, HTTPRedirect, \
    flash, session, url_for
from ...error import CalculatorError, UserError, NoSuchRecord
from ...type.misc import SectionedList
from ...type.simple import CalculatorMode, CalculatorResult, CalculatorValue, \
    ProposalWithCode
from ...view.calculator import BaseCalculator
from ...view import auth


class RSRCalculator(BaseCalculator):
    EXPECTED = 1
    TIME = 2

    modes = OrderedDict((
        (EXPECTED, CalculatorMode('rms-exp', 'RMS expected in given time')),
        (TIME, CalculatorMode('rms-time', 'Time required for target RMS')),
    ))

    version = 1

    @classmethod
    def get_code(cls):
        """
        Get the calculator "code".

        This is a short string used to uniquely identify the calculator
        within the facility which uses it.
        """
        return 'rsr'

    def __init__(self, facility, id_):
        super(RSRCalculator, self).__init__(facility, id_)
        self._calculator = RSR(self.EXPECTED)
        self._unit_selected = 'mK'

    def get_default_facility_code(self):
        """
        Get the code for the facility which has the template for this
        calculator.  This method need only be overridden if the calculator
        is intended to be used by multiple facilities.
        """
        return 'rsr'

    def get_name(self):
        return 'RSR'

    def get_calc_version(self):
        return self._calculator.get_version()

    def get_inputs(self, mode, version=None):
        if version is None:
            version = self.version
        inputs = SectionedList()
        if mode == self.EXPECTED:
            inputs.extend([
                CalculatorValue(
                    'Fl', 'Frequency between: 73 & 111', None, '{}', 'GHz.'
                ),
                CalculatorValue(
                    't', 'Time of integration', None, '{}', 'min.'
                ),
                CalculatorValue(
                    'units', 'Unit of measurment', None, '{}', ''
                )
            ])
        elif mode == self.TIME:
            inputs.extend([
                CalculatorValue(
                    'Fl', 'Frequency between: 73 & 111', None, '{}', 'GHz.'
                ),
                CalculatorValue(
                    's', 'Sensitivity', None, '{}', 'Temperature units'
                ),
                CalculatorValue(
                    'units', 'Unit of measurment', None, '{}', ''
                )
            ])
        return inputs

    def get_default_input(self, mode):
        if mode == self.EXPECTED:
            return {
                'Fl': 0.0,
                't': 0.0,
                'units': ['mK', 'mJy']
            }
        elif mode == self.TIME:
            return {
                'Fl': 0.0,
                's': 0.0,
                'units': ['temperature', 'flux']
            }
        else:
            raise CalculatorError('Something goes wrong')

    def parse_input(self, mode, input_, defaults=None):
        """
        Parse inputs as obtained from the HTML form (typically unicode)
        and return values suitable for calculation (perhaps float).

        If defaults are specified, these are used in place of missing
        values to avoid a UserError being raised.  This is useful
        in the case of changing mode when the form has been
        filled in incompletely.
        """
        parsed = {}
        validated = False

        for field in self.get_inputs(mode):
            try:
                if field.code != 'units':
                    parsed[field.code] = float(input_[field.code])
                else:
                    parsed[field.code] = input_[field.code]

            except ValueError:
                if (not input_[field.code]) and (defaults is not None):
                    parsed[field.code] = defaults[field.code]

                else:
                    raise UserError('Invalid value for {}.', field.name)
            validated = self._calculator.validate_frequency(parsed['Fl'])
            if validated is False:
                raise UserError(
                    'Invalid value for the Frequency {}', parsed['Fl']
                )
        return parsed

    def __call__(self, mode, input_):
        """
        Method in charge to perform the calculus.
        """
        t_before = time.time()
        output = {}

        self._unit_selected = input_['units']

        if mode == self.EXPECTED:
            self._calculator.set_mode(mode)
            output = self._calculator.calculator(
                input_['Fl'], input_['t'], input_['units']
            )
        else:
            raise CalculatorError('Unknown mode...')

        return CalculatorResult(output, {})

    def get_outputs(self, mode, version=None):
        """
        Get the list of calculator outputs for a given version of the
        calculator.
        """

        if version is None:
            version = self.version

        if version == 1:
            if mode == self.EXPECTED:
                if self._unit_selected == 'mK':
                    return [
                        CalculatorValue('mK', 'Result', None, '{}', 'mK'),
                        CalculatorValue(
                            'temperature', 'Result', None, '{}', 'temperature'
                        )
                    ]
                else:
                    return [
                        CalculatorValue('mJy', 'Result', None, '{}', 'mJy'),
                        CalculatorValue(
                            'flux', 'Result', None, '{}', 'flux'
                        )
                    ]
            elif mode == self.TIME:
                return []
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')

    def convert_input_mode(self, mode, new_mode, input_):
        """
        Convert the inputs for one mode to form a suitable set of inputs
        for another mode.  Only called if the mode is changed.
        """
        new_input = {}
        if mode == self.EXPECTED:
            new_input['Fl'] = input_['Fl']
            new_input['s'] = input_['t']
        elif mode == self.TIME:
            new_input['Fl'] = input_['Fl']
            new_input['t'] = input_['s']
        else:
            raise CalculatorError('Unknown mode.')
        return new_input

    def format_input(self, inputs, values):
        """
        Format the calculator inputs for display in the input form.

        This is because the input form needs to take string inputs so that
        we can give it back malformatted user input strings for correction.
        """

        return values

    def view(self, db, mode, args, form):
        """
        Web view handler for a generic calculator.
        """

        message = None

        inputs = self.get_inputs(mode)
        output = CalculatorResult(None, None)
        proposal_id = None
        for_proposal_id = None
        calculation_id = None
        calculation_proposal = None
        calculation_title = ''
        overwrite = False

        # If the user is logged in, determine whether there are any proposals
        # to which they can add calculator results.
        proposals = None
        if 'user_id' in session and 'person' in session:
            proposals = [
                ProposalWithCode(
                    *x, code=self.facility.make_proposal_code(db, x))
                for x in db.search_proposal(
                    facility_id=self.facility.id_,
                    person_id=session['person']['id'], person_is_editor=True,
                    state=ProposalState.editable_states()).values()]

        if form is not None:
            try:
                if 'proposal_id' in form:
                    proposal_id = int(form['proposal_id'])

                if 'for_proposal_id' in form:
                    for_proposal_id = int(form['for_proposal_id'])

                if 'calculation_title' in form:
                    calculation_title = form['calculation_title']

                if 'calculation_id' in form:
                    calculation_id = int(form['calculation_id'])

                if 'calculation_proposal' in form:
                    calculation_proposal = int(form['calculation_proposal'])

                if 'overwrite' in form:
                    overwrite = True

                # Work primarily with the un-parsed "input_values" so that,
                # in the event of a parsing error, we can still put the user
                # data back in the form for correction.
                input_values = self.get_form_input(inputs, form)

                if 'submit_mode' in form:
                    parsed_input = self.parse_input(
                        mode, input_values,
                        defaults=self.get_default_input(mode))

                    new_mode = int(form['mode'])

                    if not self.is_valid_mode(mode):
                        raise HTTPError('Invalid mode.')

                    if new_mode != mode:
                        # If the mode actually changed, convert the input
                        # and then create new formatted input values.
                        new_input = self.convert_input_mode(mode, new_mode,
                                                            parsed_input)

                        inputs = self.get_inputs(new_mode)
                        input_values = self.format_input(inputs, new_input)

                        mode = new_mode

                elif 'submit_calc' in form:
                    parsed_input = self.parse_input(mode, input_values)

                    output = self(mode, parsed_input)

                elif ('submit_save' in form) or ('submit_save_redir' in form):
                    parsed_input = self.parse_input(mode, input_values)

                    proposal_id = int(form['proposal_id'])

                    # Check access via the normal auth module.
                    proposal = db.get_proposal(self.facility.id_, proposal_id,
                                               with_members=True)

                    if not auth.for_proposal(
                            self.facility.get_reviewer_roles(),
                            db, proposal).edit:
                        raise HTTPForbidden(
                            'Edit permission denied for this proposal.')

                    output = self(mode, parsed_input)

                    if overwrite:
                        # Check that the calculation is really for the right
                        # proposal.
                        try:
                            calculation = db.get_calculation(calculation_id)
                        except NoSuchRecord:
                            raise UserError(
                                'Can not overwrite calculation: '
                                'calculation not found.')
                        if calculation.proposal_id != proposal_id:
                            raise UserError(
                                'Can not overwrite calculation: '
                                'it appears to be for a different proposal.')

                        db.update_calculation(
                            calculation_id,
                            mode=mode, version=self.version,
                            input_=parsed_input, output=output.output,
                            calc_version=self.get_calc_version(),
                            title=calculation_title)

                    else:
                        db.add_calculation(
                            proposal_id, self.id_, mode, self.version,
                            parsed_input, output.output,
                            self.get_calc_version(), calculation_title)

                    if 'submit_save_redir' in form:
                        flash('The calculation has been saved.')
                        raise HTTPRedirect(url_for('.proposal_view',
                                                   proposal_id=proposal_id,
                                                   _anchor='calculations'))

                    else:
                        for_proposal_id = proposal_id

                        flash(
                            'The calculation has been saved to proposal '
                            '{}: "{}".',
                            self.facility.make_proposal_code(db, proposal),
                            proposal.title)

                else:
                    raise HTTPError('Unknown action.')

            except UserError as e:
                message = e.message

        else:
            if 'proposal_id' in args:
                try:
                    proposal_id = int(args['proposal_id'])
                except ValueError:
                    raise HTTPError('Non-integer proposal_id query argument')
                for_proposal_id = proposal_id

            if 'calculation_id' in args:
                try:
                    calculation = db.get_calculation(
                        int(args['calculation_id']))
                except NoSuchRecord:
                    raise HTTPNotFound('Calculation not found.')

                # Check authorization to see this calculation.
                proposal = db.get_proposal(
                    self.facility.id_, calculation.proposal_id,
                    with_members=True, with_reviewers=True)

                can = auth.for_proposal(self.facility.get_reviewer_roles(),
                                        db, proposal)
                if not can.view:
                    raise HTTPForbidden('Access denied for that proposal.')

                proposal_id = proposal.id

                if calculation.version == self.version:
                    default_input = calculation.input
                else:
                    default_input = self.convert_input_version(
                        mode, calculation.version, calculation.input)

                calculation_id = calculation.id
                calculation_proposal = proposal_id
                calculation_title = calculation.title
                overwrite = can.edit

                try:
                    output = self(mode, default_input)
                except UserError as e:
                    message = e.message

            else:
                # When we didn't receive a form submission, get the default
                # values -- need to convert these to strings to match the
                # form input strings as explained above.
                default_input = self.get_default_input(mode)

            input_values = self.format_input(inputs, default_input)

        # If we have a specific proposal ID, see if we know its code.
        proposal_code = None
        if (proposal_id is not None) and (proposals is not None):
            for proposal in proposals:
                if proposal.id == proposal_id:
                    proposal_code = proposal.code
                    break

        input_unit_selected = input_values['units']
        default_inputs = self.get_default_input(mode)
        input_values['units'] = default_inputs['units']

        ctx = {
            'title': self.get_name(),
            'target': url_for('.calc_{}_{}'.format(self.get_code(),
                                                   self.modes[mode].code)),
            'message': message,
            'modes': self.modes,
            'current_mode': mode,
            'inputs': inputs,
            'outputs': self.get_outputs(mode),
            'input_values': input_values,
            'output_values': output.output,
            'output_extra': output.extra,
            'proposals': proposals,
            'proposal_id': proposal_id,
            'proposal_code': proposal_code,
            'for_proposal_id': for_proposal_id,
            'calculation_id': calculation_id,
            'calculation_proposal': calculation_proposal,
            'calculation_title': calculation_title,
            'overwrite': overwrite,
            'show_proposal_link': (
                (proposal_id is not None) and (
                    (proposal_id == calculation_proposal)
                    if (calculation_id is not None)
                    else ((for_proposal_id is not None) and
                          (proposal_id == for_proposal_id)))),
            'input_unit_selected': input_unit_selected,
        }

        ctx.update(self.get_extra_context())

        return ctx
