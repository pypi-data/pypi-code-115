from django.forms import forms, fields
from django.forms.widgets import PasswordInput
from django.utils.translation import ugettext_lazy as _


class PasswordForm(forms.Form):
    password = fields.CharField(label=_('Password'), required=True,
        widget=PasswordInput())

    def __init__(self, survey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.survey = survey

    def clean_password(self):
        data = self.cleaned_data
        if self.survey.password != data.get('password', None):
            raise forms.ValidationError(_('Password is incorrect!'))
        return data.get('password')
