from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# import time
from collections import OrderedDict

from ...error import CalculatorError, UserError
from ...type.misc import SectionedList
from ...type.simple import CalculatorMode, CalculatorResult, CalculatorValue
from ...view.calculator import BaseCalculator


class AZTECCalculator(BaseCalculator):
    LARGE = 1
    SMALL = 2
    PHOTHOMETRY = 3

    modes = OrderedDict((
        (LARGE, CalculatorMode('large', 'Large Observing Map Mode')),
        (SMALL, CalculatorMode('small', 'Small Observing Map Mode')),
        (PHOTHOMETRY, CalculatorMode('phothometry', 'Photometry\
         Observing Map Mode')),
    ))

    version = 1

    DEFAULT_VALUES_LARGE = {
        'Dd': 0.0,
        'Ma': 0.0
    }
    DEFAULT_VALUES_SMALL = {
        'Dd': 0.0,
        'NEFD': 0.0
    }
    DEFAULT_VALUES_PHOTHOMETRY = {
        'NEFD': 0.0,
        'S': 0.0,
        'SNR': 0.0,
        'FWHM': 0.0
    }

    @classmethod
    def get_code(cls):
        return 'aztec'

    def __init__(self, facility, id_):
        # Add instance of Calculator AzTEC
        super(AZTECCalculator, self).__init__(facility, id_)

    def get_default_facility_code(self):
        return 'aztec'

    def get_name(self):
        return 'AzTEC'

    def get_calc_version(self):
        return '0.0.0'

    def get_inputs(self, mode, version=None):
        if version is None:
            version = self.version

        inputs = SectionedList()

        if version == 1:
            if mode == self.LARGE:
                inputs.extend([
                    CalculatorValue(
                        'Ma', 'Map area', None, '{}', 'arcmin\u00B2'
                    ),
                    CalculatorValue('Dd', 'Desired depth', None, '{}', 'mJy')
                ])
            elif mode == self.SMALL:
                inputs.extend([
                    CalculatorValue('NEFD', 'NEFD', None, '{}', ''),
                    CalculatorValue('Dd', 'Desired depth', None, '{}', 'mJy')
                ])
            elif mode == self.PHOTHOMETRY:
                inputs.extend([
                    CalculatorValue('NEFD', 'NEFD', None, '{}', ''),
                    CalculatorValue(
                        'S', 'S\u2081.\u2081\u2098\u2098', None, '{}', ''
                    ),
                    CalculatorValue('SNR', 'SNR', None, '{}', ''),
                    CalculatorValue('FWHM', 'FWHM', None, '{}', '')
                ])
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')
        return inputs

    def get_default_input(self, mode):
        if mode == self.LARGE:
            return {'Ma': 0.0, 'Dd': 0.0}
        elif mode == self.SMALL:
            return {'NEFD': 0.0, 'Dd': 0.0}
        elif mode == self.PHOTHOMETRY:
            return {'NEFD': 0.0, 'S': 0.0, 'SNR': 0.0, 'FWHM': 0.0}
        else:
            raise CalculatorError('Unknown mode.')

    def parse_input(self, mode, input_, defaults=None):
        parsed = {}
        for field in self.get_inputs(mode):
            try:
                parsed[field.code] = float(input_[field.code])
            except ValueError:
                if (not input_[field.code]) and (defaults is not None):
                    parsed[field.code] = defaults[field.code]
                else:
                    raise UserError('Invalid value for {}.', field.name)
        return parsed

    def __call__(self, mode, input_):
        # t_before = time.time()
        extra = {}
        if mode == self.LARGE:
            # Add class calculator
            # output = self._calculator.calculator(input_['Ma'], input_['Dd'])
            output = {'Hr': 113.6400}
        elif mode == self.SMALL:
            output = {'Hr': 9.0200}
        elif mode == self.PHOTHOMETRY:
            output = {'sec': 1318.5100, 'arcsec': 0.0600}
        else:
            raise CalculatorError('Unknown mode.')
        return CalculatorResult(output, extra)

    def get_outputs(self, mode, version=None):
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
                        'sec', 'Requided Time', None, '{:.2f}', 'sec'
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
        new_input = input_.copy()
        # result = self(mode, input_)
        if new_mode == self.LARGE:
            new_input['Ma'] = self.DEFAULT_VALUES_LARGE['Ma']
            new_input['Dd'] = self.DEFAULT_VALUES_LARGE['Dd']
        elif new_mode == self.SMALL:
            new_input['NEFD'] = self.DEFAULT_VALUES_SMALL['NEFD']
            new_input['Dd'] = self.DEFAULT_VALUES_SMALL['Dd']
        elif new_mode == self.PHOTHOMETRY:
            new_input['NEFD'] = self.DEFAULT_VALUES_PHOTHOMETRY['NEFD']
            new_input['S'] = self.DEFAULT_VALUES_PHOTHOMETRY['S']
            new_input['SNR'] = self.DEFAULT_VALUES_PHOTHOMETRY['SNR']
            new_input['FWHM'] = self.DEFAULT_VALUES_PHOTHOMETRY['FWHM']
        else:
            raise CalculatorError('Unknown mode.')
        return new_input

    def format_input(self, inputs, values):
        return values
