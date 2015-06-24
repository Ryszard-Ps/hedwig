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

from collections import OrderedDict
import time

from ...error import CalculatorError, UserError
from ...type import CalculatorMode, CalculatorResult, CalculatorValue
from ...view.calculator import BaseCalculator


class DummyCalculator(BaseCalculator):
    ADDITION = 1
    SUBTRACTION = 2

    modes = OrderedDict((
        (ADDITION,    CalculatorMode('add', 'Addition')),
        (SUBTRACTION, CalculatorMode('sub', 'Subtraction')),
    ))

    version = 1

    @classmethod
    def get_code(cls):
        """
        The the calculator "code".

        This is a short string used to uniquely identify the calculator
        within the facility which uses it.
        """

        return 'dummy'

    def get_name(self):
        return "Dummy Calculator"

    def get_inputs(self, mode, version=None):
        """
        Get the list of calculator inputs for a given version of the
        calculator.
        """

        if version is None:
            version = self.version

        if mode in (self.ADDITION, self.SUBTRACTION) and version == 1:
            return [
                CalculatorValue('a', 'First input', '{}', 'm'),
                CalculatorValue('b', 'Second input', '{}', 'm'),
            ]

        else:
            raise CalculatorError('Unknown mode or version.')

    def get_default_input(self, mode):
        """
        Get the default input values (for the current version).
        """

        return {'a': 1.0, 'b': 2.0}

    def convert_input_mode(self, mode, new_mode, input_):
        """
        Convert the inputs for one mode to form a suitable set of inputs
        for another mode.  Only called if the mode is changed.
        """

        new_input = input_.copy()

        new_input['b'] = - new_input['b']

        return new_input

    def convert_input_version(self, old_version, input_):
        """
        Converts the inputs from an older version so that they can be
        used with the current version of the calculator.
        """

        return input_

    def get_outputs(self, mode, version=None):
        """
        Get the list of calculator outputs for a given version of the
        calculator.
        """

        if version is None:
            version = self.version

        if version == 1:
            if mode == self.ADDITION:
                return [CalculatorValue('sum', 'Sum', '{}', 'mm')]
            elif mode == self.SUBTRACTION:
                return [CalculatorValue('diff', 'Difference', '{}', 'km')]
            else:
                raise CalculatorError('Unknown mode.')
        else:
            raise CalculatorError('Unknown version.')

    def parse_input(self, mode, input_):
        """
        Parse inputs as obtained from the HTML form (typically unicode)
        and return values suitable for calculation (perhaps float).
        """

        parsed = {}

        for field in self.get_inputs(mode):
            try:
                parsed[field.code] = float(input_[field.code])

            except ValueError:
                raise UserError('Invalid value for {}.', field.name)

        return parsed

    def __call__(self, mode, input_):
        """
        Perform a calculation, taking an input dictionary and returning
        a CalculatorResult object.

        The result object contains the essential output, a dictionary with
        entries corresponding to the list given by get_outputs.  It also
        contains any extra output for display but which would not be
        stored in the database as part of the calculation result.
        """

        t_before = time.time()

        if mode == self.ADDITION:
            output = {'sum': (input_['a'] + input_['b']) * 1000}
        elif mode == self.SUBTRACTION:
            output = {'diff': (input_['a'] - input_['b']) / 1000}
        else:
            raise CalculatorError('Unknown mode.')

        t_after = time.time()

        return CalculatorResult(output,
                                {'product': input_['a'] * input_['b'],
                                 't_elapsed': t_after - t_before})
