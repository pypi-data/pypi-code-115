from django import forms
from django.utils.translation import ugettext_lazy as _

from votebase.core.questionnaires.forms.radio import VoteRadioForm, VoterRadioForm


class VoteDropdownForm(VoteRadioForm):
    options = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options'].choices = [('', _('Select an option')), ] + self.fields['options'].choices


class VoterDropdownForm(VoterRadioForm):
    options = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options'].choices = [('', _('Select an option')), ] + self.fields['options'].choices
