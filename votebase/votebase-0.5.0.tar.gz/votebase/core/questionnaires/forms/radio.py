from django import forms
from django.core.validators import EMPTY_VALUES
from django.db import transaction

from votebase.core.questionnaires.models import Option
from votebase.core.voting.models import Answer


class VoteRadioForm(forms.ModelForm):
    options = forms.ChoiceField(widget=forms.RadioSelect())

    class Meta:
        model = Answer
        fields = ('options', )

    def __init__(self, question, number=1, voter=None, *args, **kwargs):
        super(VoteRadioForm, self).__init__(*args, **kwargs)

        self.number = number
        self.question = question

        if not question.is_required:
            self.fields['options'].required = False

        self.fields['options'].label = self.question.get_label(number)
        self.fields['options'].choices = self.question.get_choices()

        # find answer
        if voter:
            self.set_initial(voter)

    def set_initial(self, voter):
        answers = Answer.objects.filter(voter=voter, question=self.question)

        try:
            answer = answers[0]
            if answer is not None and answer.option is not None:
                self.fields['options'].initial = answer.option.pk

        except IndexError:
            pass

    def save(self, voter, commit=True):
        self.instance.question = self.question
        self.instance.voter = voter

        option_pk = self.cleaned_data.get('options', None)

        if option_pk not in EMPTY_VALUES:
            option = Option.objects.get(pk=option_pk)
            self.instance.option = option

        with transaction.atomic():
            # delete previous answers
            Answer.objects.filter(voter=voter, question=self.question).delete()
            return super(VoteRadioForm, self).save(commit)


class VoterRadioForm(VoteRadioForm):
    options = forms.ChoiceField(widget=forms.RadioSelect())

    def __init__(self, question, voter, *args, **kwargs):
        self.show_quiz_correct_options = kwargs.pop('show_quiz_correct_options') if 'show_quiz_correct_options' in kwargs else False

        super(VoterRadioForm, self).__init__(question=question, voter=voter, *args, **kwargs)
        self.question = question
        self.voter = voter
        self.fields['options'].widget.attrs['disabled'] = 'disabled'

        # correct options
        if question.is_quiz and self.show_quiz_correct_options:
            self.fields['options'].widget.attrs['correct_options'] = \
                list(question.option_set.correct().values_list('id', flat=True))

    @staticmethod
    def get_result(question, voter):
        return int(Answer.objects.filter(
            voter=voter,
            question=question,
            option__is_correct=True
        ).exists())

        # old solution
        # Answer.objects.filter(voter=voter, question=question).values_list('option_id', flat=True)[0]
        # correct_options = question.option_set.filter(is_correct=True).values_list('id', flat=True)
        #
        # try:
        #     answer = Answer.objects.filter(voter=voter, question=question).values_list('option_id', flat=True)[0]
        # except IndexError:
        #     return not len(correct_options)
        #
        # return 1 if answer in correct_options else 0
