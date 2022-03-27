from django import forms

from votebase.core.questionnaires.forms.textfield import VoteTextfieldForm, VoterTextfieldForm
from votebase.core.voting.models import Answer


class VoteTextareaForm(VoteTextfieldForm):
    class Meta:
        model = Answer
        fields = ('custom',)
        widgets = {
            'custom': forms.Textarea(attrs={'class': 'input-block-level'}),
        }


class VoterTextareaForm(VoterTextfieldForm):
    class Meta:
        model = Answer
        fields = ('custom', )
        widgets = {
            'custom': forms.Textarea(attrs={'class': 'input-block-level'}),
        }
