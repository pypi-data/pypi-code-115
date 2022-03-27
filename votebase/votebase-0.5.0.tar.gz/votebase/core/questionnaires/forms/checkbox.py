from django import forms
from django.db import transaction

from votebase.core.questionnaires.models import Option
from votebase.core.voting.models import Answer


class VoteCheckboxForm(forms.Form):
    options = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple())

    def __init__(self, question, number=1, voter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question

        if not question.is_required:
            self.fields['options'].required = False

        self.fields['options'].label = self.question.get_label(number)
        self.fields['options'].choices = self.question.get_choices()

        # find answer
        if voter:
            self.set_initial(voter)

    def set_initial(self, voter):
        answers = Answer.objects\
            .filter(voter=voter, question=self.question)

        if answers is not None:
            self.fields['options'].initial = list(answers.values_list('option__pk', flat=True))

    def save(self, voter, commit=True):
        with transaction.atomic():
            # delete previous answers
            Answer.objects.filter(voter=voter, question=self.question).delete()

            for option_pk in self.cleaned_data['options']:
                if len(option_pk) != 0:
                    obj = Answer.objects.create(
                        option=Option.objects.get(pk=option_pk),
                        voter=voter,
                        question=self.question,
                    )
                    obj.save()

    class Meta:
        model = Answer
        fields = ('options', )


class VoterCheckboxForm(VoteCheckboxForm):
    options = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple())

    def __init__(self, question, voter, *args, **kwargs):
        self.show_quiz_correct_options = kwargs.pop('show_quiz_correct_options') if 'show_quiz_correct_options' in kwargs else False

        super().__init__(question=question, voter=voter, *args, **kwargs)
        self.voter = voter
        self.fields['options'].widget.attrs['disabled'] = 'disabled'

        # correct options
        if question.is_quiz and self.show_quiz_correct_options:
            self.fields['options'].widget.attrs['correct_options'] = \
                list(question.option_set.correct().values_list('id', flat=True))

    @staticmethod
    def get_result(question, voter):
        correct_options = question.option_set.filter(is_correct=True).values_list('id', flat=True)
        answers = Answer.objects.filter(voter=voter, question=question)
        correct_answers = answers.filter(option_id__in=correct_options).count()
        wrong_answers = answers.exclude(option_id__in=correct_options).count()

        numerator = float(correct_answers - wrong_answers)
        denominator = len(correct_options)

        # 0 correct options, but marked some => WRONG
        if denominator == 0 and answers.count() != 0:
            return 0

        # 0 correct options and not marked any => CORRECT
        if denominator == 0 and answers.count() == 0:
            return 1

        result = numerator / denominator
        return round(result, 2) if result >= 0 else 0
