from itertools import chain

from django import forms
from django.forms import CheckboxInput
from django.forms.widgets import MultiWidget, RadioSelect
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class MatrixRadioInput(RadioSelect):
    def __init__(self, name, value, attrs=None, choices=(), idx=None):
        super().__init__(attrs, choices)
        self.name = name
        self.value = value
        self.idx = idx

    def render(self, *args, **kwargs):
        choice = self.choices[0]

        correct_options = ''
        if 'correct_options' in self.attrs:
            correct_options = f"[{','.join(map(str, self.attrs['correct_options']))}]"

        input_value = choice[0]
        is_checked = str(input_value) == str(self.value)
        input_id = f"{self.attrs['id']}_{self.idx}"

        return '<input type="radio" id="{}" value="{}" name="{}" class="form-check-input" {} {} {} {}><label class="form-check-label" for="{}"></label> '.format(
            input_id,
            input_value,
            self.name,
            correct_options,
            'checked="checked"' if is_checked else '',
            'disabled="disabled"' if self.attrs.get('disabled', None) == 'disabled' else '',
            'required="required"' if self.attrs.get('required', False) else '',
            input_id
        )


class BootstrapRadioTableFieldWidget(forms.RadioSelect):
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield MatrixRadioInput(self.name, self.value, self.attrs.copy(), [choice], i)

    def __getitem__(self, idx):
        choice = self.choices[idx]  # Let the IndexError propagate
        return MatrixRadioInput(self.name, self.value, self.attrs.copy(), [choice], idx)

    def render(self, name, value, attrs=None, renderer=None):
        self.name = name
        self.value = value
        self.attrs = attrs

        output = []
        for w in self:
            w.choice_label = ''
            correct_options = self.attrs.get('correct_options')
            is_correct_option = ''

            if correct_options:
                is_correct_option = w.choices[0][0] in self.attrs.get('correct_options', [])
                is_correct_option = 'data-correct-option="%s"' % str(is_correct_option).lower()

            output.append('<td %s><div class="form-check">%s</div></td>' % (is_correct_option, w.render()))

        return mark_safe(''.join(output))


class Matrix(MultiWidget):
    def __init__(self, rows=None, columns=None):
        widgets = []
        self.rows = rows
        self.columns = columns

        for row in rows:
            # widgets.append(BootstrapRadioTableFieldRenderer)  # OLD
            widgets.append(BootstrapRadioTableFieldWidget(choices=columns))
        super(Matrix, self).__init__(widgets)

    def render(self, name, value, attrs=None, renderer=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
                # value is a list of values, each corresponding to a widget
                # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []

        final_attrs = self.build_attrs(attrs, self.attrs)
        id_ = final_attrs.get('id', None)

        is_quiz = 'correct_options' in self.attrs

        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None

            option_id = self.rows[i][0]
            klass_correct = ""
            klass_valid = ""

            if is_quiz:
                klass_correct = "correct" if option_id in self.attrs['correct_options'] else "incorrect"
                is_valid = widget_value in self.attrs['correct_options'] and klass_correct == 'correct' or widget_value not in self.attrs['correct_options'] and klass_correct == 'incorrect'
                is_valid = is_valid and widget_value
                klass_valid = 'valid' if is_valid else 'invalid'

            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))

            rendered_output = widget.render(name + '_%s' % i, widget_value, final_attrs)
            rendered_headings = self.rows[i][1]
            output.append('<tr class="%s %s"><th class="option">%s</th>%s</td>' % (klass_correct, klass_valid, rendered_headings, rendered_output))

        return mark_safe('<div class="matrix table-responsive"><table class="table table-bordered %s">%s%s</table></div>' % (
                'quiz' if is_quiz else '',
                self._rendered_heading(),
                ''.join(output)  # self.format_output(output)
            ))

    def _rendered_heading(self):
        output = ['<th></th>']
        for column in self.columns:
            output.append('<th>%s</th>' % column[1])
        return '<tr>%s</tr>' % ''.join(output)

    def decompress(self, value):
        result = []
        for row in self.rows:
            result.append(None)
        return result


class BootstrapCheckboxSelectTableMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['']
        # Normalize to strings
        str_values = set([str(v) for v in value])
        enum = enumerate(chain(self.choices, choices))
        for i, (option_value, option_label) in enum:
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = ' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = CheckboxInput(
                final_attrs, check_test=lambda value: value in str_values)
            option_value = str(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(str(option_label))
            output.append('<td>%s</td>' % rendered_cb)
        output.append('')
        return mark_safe('\n'.join(output))


class MatrixMultiple(MultiWidget):
    def __init__(self, rows=None, columns=None):
        widgets = []
        self.rows = rows
        self.columns = columns

        for row in rows:
            widgets.append(BootstrapCheckboxSelectTableMultiple(choices=columns))
        super(MatrixMultiple, self).__init__(widgets)

    def render(self, name, value, attrs=None, renderer=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
                # value is a list of values, each corresponding to a widget
                # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []

        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None

            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            rendered_output = widget.render(
                name + '_%s' % i, widget_value, final_attrs)
            rendered_headings = self.rows[i][1]
            output.append(
                '<tr><th>%s</th>%s</td>' % (
                    rendered_headings, rendered_output))
        return mark_safe('<div class="table-responsive"><table class="table table-bordered">%s%s</table><div>' % (
                self._rendered_heading(), 
                ''.join(output)  # self.format_output(output)
            ))

    def _rendered_heading(self):
        output = ['<th></th>']
        for column in self.columns:
            output.append('<th>%s</th>' % column[1])

        return '<tr>%s</tr>' % ''.join(output)

    def decompress(self, value):
        result = []
        for row in self.rows:
            result.append(None)
        return result

