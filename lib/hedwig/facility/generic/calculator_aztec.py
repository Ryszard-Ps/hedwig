# -*- encoding: utf-8 -*-
"""##Modulo adaptador de la calculadora AzTEC."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import OrderedDict

from aztec_calculator import Aztec

from ...error import CalculatorError, UserError
from ...type.misc import SectionedList
from ...type.simple import CalculatorMode, CalculatorResult, CalculatorValue
from ...view.calculator import BaseCalculator


class AZTECCalculator(BaseCalculator):
    """###Clase adapter para AzTEC.

    Atributos de la clase:

    - `LARGE` - (int) - Modo Large Observing Map Mode.
    - `SMALL` - (int) - Modo Small Observing Map Mode.
    - `PHOTHOMETRY` - (int) - Mode Photometry Observing Map Mode.
    - `version` - (int) - Versión del adaptador.
    - `DEFAULT_VALUES_LARGE` - (dict) - Valores por defecto para el modo LARGE
    - `DEFAULT_VALUES_SMALL` - (dict) - Valores por defecto para el modo SMALL
    - `DEFAULT_VALUES_PHOTHOMETRY` - (dict) - Valores por defecto para el modo PHOTHOMETRY
    """

    LARGE = 1
    SMALL = 2
    PHOTHOMETRY = 3

    modes = OrderedDict((
        (LARGE, CalculatorMode('large', 'Large Observing Map Mode')),
        (SMALL, CalculatorMode('small', 'Small Observing Map Mode')),
        (PHOTHOMETRY, CalculatorMode('phothometry', 'Photometry Observing\
            Map Mode')),
    ))

    version = 1

    DEFAULT_VALUES_LARGE = {
        'dd': 0,
        'ma': 0
    }
    DEFAULT_VALUES_SMALL = {
        'dd': 0
    }
    DEFAULT_VALUES_PHOTHOMETRY = {
        's': 0,
        'snr': 0
    }

    @classmethod
    def get_code(cls):
        """###Retorna el codigo de la calculadora.

        ** :Parameters: **

        - `cls` - Instancia de la clase.

        ** :rtype: ** str
        """
        return 'aztec'

    def __init__(self, facility, id_):
        """###Constructor AZTECCalculator.

        ** :Parameters: **

        - `facility` - Instancia del facility.
        - `id_` - id de la Instancia.
        """
        super(AZTECCalculator, self).__init__(facility, id_)
        self._calculator = Aztec(self.LARGE)

    def get_default_facility_code(self):
        """###Obtiene el codigo del facility.

        Se obtiene el codigo del facility para el facility.

        ** :rtype: ** str
        """
        return 'aztec'

    def get_name(self):
        """Obtener el nombre del Adaptador.

        ** :rtype: ** str
        """
        return 'AzTEC'

    def get_calc_version(self):
        """###Obtiene la versión de la calculadora.

        ** :rtype: ** str
        """
        return self._calculator.get_calculator_version()

    def get_inputs(self, mode, version=None):
        """###Obtiene los valores.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.
        - `version` - (int) - Versión de la calculadora.

        ** :rtype: ** SectionedList
        """
        if version is None:
            version = self.version

        inputs = SectionedList()

        if version == 1:
            if mode == self.LARGE:
                inputs.extend([
                    CalculatorValue(
                        'ma', 'Map area', None, '{}', 'arcmin\u00B2'
                    ),
                    CalculatorValue('dd', 'Desired depth', None, '{}', 'mJy')
                ])
            elif mode == self.SMALL:
                inputs.extend([
                    CalculatorValue('dd', 'Desired depth', None, '{}', 'mJy')
                ])
            elif mode == self.PHOTHOMETRY:
                inputs.extend([
                    CalculatorValue(
                        's', 'S\u2081.\u2081\u2098\u2098', None, '{}', 'mJy'
                    ),
                    CalculatorValue('snr', 'SNR', None, '{}', '')
                ])
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')
        return inputs

    def get_default_input(self, mode):
        """###Obtiene los valores de la vista.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.

        ** :rtype: ** dict
        """
        if mode == self.LARGE:
            return {'ma': 0, 'dd': 0}
        elif mode == self.SMALL:
            return {'dd': 0}
        elif mode == self.PHOTHOMETRY:
            return {'s': 0, 'snr': 0}
        else:
            raise CalculatorError('Unknown mode.')

    def parse_input(self, mode, input_, defaults=None):
        """Convierte las entradas de la vista.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.
        - `input_` - (dict) - Entradas de los formularios.
        - `defaults` - Valores por defecto de la calculadora.

        ** :rtype: ** dict

        """
        parsed = {}
        for field in self.get_inputs(mode):
            try:
                parsed[field.code] = float(input_[field.code])
                if parsed[field.code] <= 0.0:
                    raise UserError('Invalid value for {}.', field.name)
            except ValueError:
                if (not input_[field.code]) and (defaults is not None):
                    parsed[field.code] = defaults[field.code]
                else:
                    raise UserError('Invalid value for {}.', field.name)
        return parsed

    def __call__(self, mode, input_):
        """###Realiza las operaciones.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.
        - `input_` - (dict) - Valores de la operación.

        ** :rtype: ** CalculatorResult
        """
        extra = {}
        self._calculator.set_calculator_mode(mode)
        if mode == self.LARGE:
            output = self._calculator.calculate(
                map_area=input_['ma'],
                dd=input_['dd']
            )
        elif mode == self.SMALL:
            print(self._calculator.calculate(
                dd=input_['dd']
            ))
            output = self._calculator.calculate(
                dd=input_['dd']
            )
        elif mode == self.PHOTHOMETRY:
            output = self._calculator.calculate(
                s=input_['s'],
                snr=input_['snr']
            )
        else:
            raise CalculatorError('Unknown mode.')
        return CalculatorResult(output, extra)

    def get_outputs(self, mode, version=None):
        """Obtener las salidas de las operaciones.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.
        - `version` - (int) - Versión actual de la calculadora.

        ** :rtype: ** [CalculatorValue,]
        """
        if version is None:
            version = self.version
        if version == 1:
            if mode == self.LARGE:
                return [
                    CalculatorValue(
                        'Hr', 'Requided Time', None, '{:.2f}', 'Hr'
                    ),
                ]
            elif mode == self.SMALL:
                return [
                    CalculatorValue(
                        'Hr', 'Requided Time', None, '{:.2f}', 'Hr'
                    ),
                ]
            elif mode == self.PHOTHOMETRY:
                return [
                    CalculatorValue(
                        'Sec', 'Requided Time', None, '{:.2f}', 'Sec'
                    ),
                    CalculatorValue(
                        'arcsec', 'Positional Uncertainty',
                        None, '{:.2f}', 'arcsec'
                    ),
                ]
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')

    def convert_input_mode(self, mode, new_mode, input_):
        """Asigna los valores de un modo a otro.

        ** :Parameters: **

        - `mode` - (int) - Modo actual de la calculadora.
        - `new_mode` - (int) - Modo a cambiar de la calculadora.
        - `input_` - (dict) - Valores de entrada en los formularios.

        ** :rtype: ** dict
        """
        new_input = {}
        if new_mode == self.LARGE:
            new_input['ma'] = self.DEFAULT_VALUES_LARGE['ma']
            new_input['dd'] = self.DEFAULT_VALUES_LARGE['dd']
        elif new_mode == self.SMALL:
            new_input['dd'] = self.DEFAULT_VALUES_SMALL['dd']
        elif new_mode == self.PHOTHOMETRY:
            new_input['s'] = self.DEFAULT_VALUES_PHOTHOMETRY['s']
            new_input['snr'] = self.DEFAULT_VALUES_PHOTHOMETRY['snr']
        else:
            raise CalculatorError('Unknown mode.')
        return new_input

    def format_input(self, inputs, values):
        """Asigna formato a las entradas del formulario.

        ** :Parameters: **

        - `inputs` - (dict) - Entradas con que se mostraran en la vista.
        - `values` - (dict) - Valores de las entradas.

        ** :rtype: ** dict
        """
        return values
