from django import forms
from django.db import transaction

from votebase.core.voting.models import Answer


class VoteTextfieldForm(forms.ModelForm):
    def __init__(self, question, number=1, voter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.fields['custom'].label = self.question.get_label(number)
        self.fields['custom'].required = question.is_required

        # find answer
        if voter:
            self.set_initial(voter)

    def set_initial(self, voter):
        # find answer
        answers = Answer.objects.filter(voter=voter, question=self.question)

        try:
            answer = answers[0]

            if answer.custom is not None:
                self.fields['custom'].initial = answer.custom
        except IndexError:
            pass

    def save(self, voter, commit=True):
        self.instance.question = self.question
        self.instance.voter = voter

        with transaction.atomic():
            # delete previous answers
            Answer.objects.filter(voter=voter, question=self.question).delete()
            return super().save(commit)

    class Meta:
        model = Answer
        fields = ('custom', )
        widgets = {
            'custom': forms.TextInput(attrs={'class': 'input-block-level'}),
        }


class VoterTextfieldForm(VoteTextfieldForm):
    def __init__(self, question, voter, *args, **kwargs):
        super().__init__(question=question, voter=voter, *args, **kwargs)
        self.fields['custom'].widget.attrs['disabled'] = 'disabled'
