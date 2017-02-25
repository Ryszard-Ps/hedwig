"""## Modulo del Adapter para la calculadora RSR.

Este modulo contienen la funcionalidad que enlaza la calculadora RSR con el
sistema Hedwig.

El código fuente aparece de lado derecho de esta documentación.

también puede ser encontrado en el siguiente enlace:

[Repositorio de esta versión de hedwig](https://github.com/sezzh/hedwig)

Ruta del archivo:

```
lib/hedwig/facility/generic/calculator_rsr.py
```
"""
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

# ## RSRCalculator
class RSRCalculator(BaseCalculator):
    """Clase del Adapter para la calculadora RSR.

    Esta Clase sigue el patrón de diseño propuesto por la documentacion de
    Hedwig Proposal System.

    En orden para entender complemtamente el uso de este adaptador, se debe
    leer el articulo sobre:

    > Hedwig's facilities.

    ### Atributos de la clase:

    * EXPECTED => Refiere al primer modo de la calculadora.
    * TIME => Refiere al segundo modo de la calculadora.
    * modes => Refiere a los nombres designados para cada modo y
    la url a utilizarse.
    * DEFAULT_VALUES_EXPECTED => Valores por defecto de entrada.
    * DEFAULT_VALUES_TIME => Valores por defecto de entrada.
    * version => Atributo usado para almacenar la versión actual que se usa
    de la calculadora dentro de la tabla calculation.
    """

    EXPECTED = 1
    TIME = 2

    modes = OrderedDict((
        (EXPECTED, CalculatorMode('rms-exp', 'RMS expected in given time')),
        (TIME, CalculatorMode('rms-time', 'Time required for target RMS')),
    ))

    version = 1

    DEFAULT_VALUES_EXPECTED = {
        'Fl': 92.0,
        't': 10
    }

    DEFAULT_VALUES_TIME = {
        'Fl': 92.0,
        's': 10
    }

    @classmethod
    def get_code(cls):
        """Regresa el código de la calculadora.

        @classmethod

        Params:

        * cls => instancia de la clase.

        Este es un String que se utiliza para identificar inequivocamente
        a la calculadora con el facility que lo implementa.

        Returns:

        * String.

        """
        return 'rsr'

    def __init__(self, facility, id_):
        """Adapter's Constructor.

        Constructor de la Clase Adapter.

        Params:

        * facility => Instancia del facility.
        * id_ => id.
        """
        super(RSRCalculator, self).__init__(facility, id_)
        self._calculator = RSR(self.EXPECTED)
        self._unit_selected = 'mK'

    def get_default_facility_code(self):
        """Obtener el facility_code.

        Se obtiene el facility_code para el facility y así poder recuperar los
        los templates para esta calculadora.
        """
        return 'rsr'

    def get_name(self):
        """Obtener el nombre del Adapter.

        Returns:

        * String
        """
        return 'RSR'

    def get_calc_version(self):
        """Obtener la versión del package de la calculadora RSR.

        Returns:

        * String
        """
        return self._calculator.get_version()

    def get_inputs(self, mode, version=None):
        """Obtener los inputs para la vista.

        Params:

        * mode => modo actual de la calculadora.
        * version => (default = None) versión de la calculadora.

        Returns:

        * SectionedList
        """
        if version is None:
            version = self.version
        inputs = SectionedList()
        if mode == self.EXPECTED:
            inputs.extend([
                CalculatorValue(
                    'Fl', 'Frequency', None, '{}', 'GHz. (between: 73 & 111)'
                ),
                CalculatorValue(
                    't', 'Integration time', None, '{}', 'min.'
                ),
                CalculatorValue(
                    'units', 'Units', None, '{}', ''
                )
            ])
        elif mode == self.TIME:
            inputs.extend([
                CalculatorValue(
                    'Fl', 'Frequency', None, '{}', 'GHz. (between: 73 & 111)'
                ),
                CalculatorValue(
                    's', 'Sensitivity', None, '{}', 'mK / mJy'
                ),
                CalculatorValue(
                    'units', 'Units', None, '{}', ''
                )
            ])
        return inputs

    def get_default_input(self, mode):
        """Obtener valores por defecto para las vistas.

        Params:

        * mode => modo actual de la calculadora.
        """
        if mode == self.EXPECTED:
            return {
                'Fl': 92.0,
                't': 10.0,
                'units': ['mK', 'mJy']
            }
        elif mode == self.TIME:
            return {
                'Fl': 92.0,
                's': 10.0,
                'units': ['temperature', 'flux']
            }
        else:
            raise CalculatorError('Something goes wrong')

    def parse_input(self, mode, input_, defaults=None):
        """Convierte los inputs obtenidos del HTML.

        Adicionalmente los convierte a tipos situables para realizar los
        calculos correspondientes.

        Params:

        * mode => modo actual de la calculadora.
        * input_ => los inputs recibidos de las vistas HTML.
        * defaults => (default = None) valores por defecto de las calculadoras.

        Returns:

        * Dict
        """
        parsed = {}
        validated = False
        for field in self.get_inputs(mode):
            try:
                if field.code != 'units':
                    parsed[field.code] = float(input_[field.code])
                else:
                    parsed[field.code] = input_[field.code]
                if field.code == 't' or field.code == 's':
                    if not self._calculator.validate_sensitivity(
                        float(input_[field.code])
                    ):
                        raise UserError('Invalid value for: {}.', field.name)
            except ValueError:
                if (not input_[field.code]) and (defaults is not None):
                    parsed[field.code] = defaults[field.code]

                else:
                    raise UserError('Invalid value for: {}.', field.name)
            validated = self._calculator.validate_frequency(parsed['Fl'])
            if validated is False:
                raise UserError(
                    'Invalid value for the Frequency {}', parsed['Fl']
                )
        return parsed

    def __call__(self, mode, input_):
        """Ejecuta el calculo.

        Params:

        * mode => modo actual de la calculadora.
        * input_ => valores recibidos para realizar el calculo.

        Returns:

        * CalculatorResult
        """
        t_before = time.time()
        output = {}

        self._unit_selected = input_['units']
        self._calculator.set_mode(mode)

        if mode == self.EXPECTED:
            output = self._calculator.calculator(
                input_['Fl'], input_['t'], input_['units']
            )
        elif mode == self.TIME:
            output = self._calculator.calculator(
                input_['Fl'], input_['s'], input_['units']
            )
        else:
            raise CalculatorError('Unknown mode...')

        return CalculatorResult(output, {})

    def get_outputs(self, mode, version=None):
        """Obtener las salidas de las calculos.

        Params:

        * mode => modo actual de la calculadora.
        * version => (default = None) versión actual de la calculadora.

        Returns:

        * list [CalculatorValue,]
        """

        if version is None:
            version = self.version

        if version == 1:
            if mode == self.EXPECTED:
                if self._unit_selected == 'mK':
                    return [
                        CalculatorValue('mK', 'Result', None, '{}', 'mK'),
                    ]
                else:
                    return [
                        CalculatorValue('mJy', 'Result', None, '{}', 'mJy'),
                    ]
            elif mode == self.TIME:
                if self._unit_selected == 'temperature':
                    return [
                        CalculatorValue('time', 'Result', None, '{}', 'min'),
                    ]
                else:
                    return [
                        CalculatorValue('time', 'Result', None, '{}', 'min'),
                    ]
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')

    def convert_input_mode(self, mode, new_mode, input_):
        """Convierte la entrada de un modo en la entrada del otro.

        Params:

        * mode => modo actual de la calculadora.
        * new_mode => modo a cambiar de la calculadora.
        * input_ valores ingresados del HTML.

        Returns:

        * Dict
        """

        new_input = {}
        if mode == self.EXPECTED:

            new_input['Fl'] = self.DEFAULT_VALUES_EXPECTED['Fl']
            new_input['s'] = self.DEFAULT_VALUES_EXPECTED['t']
        elif mode == self.TIME:

            new_input['Fl'] = self.DEFAULT_VALUES_TIME['Fl']
            new_input['t'] = self.DEFAULT_VALUES_TIME['s']
        else:
            raise CalculatorError('Unknown mode.')
        return new_input

    def format_input(self, inputs, values):
        """Formatea los inputs para ser visibles en el formulario HTML.
        Params:

        * inputs => inputs que serán mostrados en el HTML.
        * values => valores de los inputs.

        Returns:

        * Dict
        """

        return values

    def view(self, db, mode, args, form):
        """Método encargado de cargar el HTML.

        Params:

        db => instancia de la DB.
        mode => modo actual de la calculadora.
        args => argumentos.
        form => forumario HTML.

        Returns:

        * Dict
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

                input_values = self.get_form_input(inputs, form)

                if 'submit_mode' in form:
                    parsed_input = self.parse_input(
                        mode, input_values,
                        defaults=self.get_default_input(mode))

                    new_mode = int(form['mode'])

                    if not self.is_valid_mode(mode):
                        raise HTTPError('Invalid mode.')

                    if new_mode != mode:
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

                    proposal = db.get_proposal(self.facility.id_, proposal_id,
                                               with_members=True)

                    if not auth.for_proposal(
                            self.facility.get_reviewer_roles(),
                            db, proposal).edit:
                        raise HTTPForbidden(
                            'Edit permission denied for this proposal.')

                    output = self(mode, parsed_input)

                    if overwrite:
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
                default_input = self.get_default_input(mode)

            input_values = self.format_input(inputs, default_input)

        proposal_code = None
        if (proposal_id is not None) and (proposals is not None):
            for proposal in proposals:
                if proposal.id == proposal_id:
                    proposal_code = proposal.code
                    break

        if 'units' not in input_values:
            default_inputs = self.get_default_input(mode)
            input_values['units'] = default_inputs['units']

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
