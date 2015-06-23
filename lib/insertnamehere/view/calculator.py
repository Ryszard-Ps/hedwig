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

from ..error import UserError
from ..type import CalculatorResult
from ..web.util import HTTPError, url_for


class BaseCalculator(object):
    def __init__(self, id_):
        self.id_ = id_

    def view(self, db, mode, form):
        """
        Web view handler for a generic calculator.
        """

        message = None

        inputs = self.get_inputs(mode)
        output = CalculatorResult(None, None)

        if form is not None:
            try:
                # Work primarily with the un-parsed "input_values" so that,
                # in the event of a parsing error, we can still put the user
                # data back in the form for correction.
                input_values = self.get_form_input(inputs, form)
                parsed_input = self.parse_input(mode, input_values)

                if 'submit_mode' in form:
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
                    output = self(mode, parsed_input)

                else:
                    raise HTTPError('Unknown action.')

            except UserError as e:
                message = e.message

        else:
            # When we didn't receive a form submission, get the default
            # values -- need to convert these to strings to match the
            # form input strings as explained above.
            default_input = self.get_default_input(mode)
            input_values = self.format_input(inputs, default_input)

        return {
            'title': self.get_name().title(),
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
        }

    def format_input(self, inputs, values):
        """
        Format the calculator inputs for display in the input form.

        This is because the input form needs to take string inputs so that
        we can give it back malformatted user input strings for correction.
        """

        return {x.code: x.format.format(values[x.code]) for x in inputs}

    def get_form_input(self, inputs, form):
        """
        Extract the input values from the submitted form.

        This example would be sufficient in the case of some input
        text boxes, but subclasses need to override to support other
        form elements such as checkboxes.
        """

        return {x.code: form[x.code] for x in inputs}

    def is_valid_mode(self, mode):
        """
        Determine whether the given mode is valid.

        Does this by seeing if it appears in the calculator's "modes"
        attribute (normally a dictionary).
        """

        return mode in self.modes