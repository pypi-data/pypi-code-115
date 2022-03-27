import math

from django import forms
from django.db import transaction
from django.db.models import Q

from votebase.core.questionnaires.models import Option
from votebase.core.utils.fields import MatrixField
from votebase.core.voting.models import Answer


class VoteMatrixRadioForm(forms.Form):
    def __init__(self, question, number=1, voter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.rows = list(question.option_set.rows().prepare_as_list())
        self.columns = list(question.option_set.columns().prepare_as_list())

        self.fields['matrix'] = MatrixField(
            label=question.title, rows=self.rows, columns=self.columns,
            required=question.is_required,
            unique_answers=question.is_unique_answers,
            empty_row_enabled=question.is_empty_row_enabled)

        self.fields['matrix'].label = self.question.get_label(number)

        if voter:
            self.set_initial(voter)

    def save(self, voter, commit=True):
        options = self.cleaned_data.get('matrix', '').split('-')

        with transaction.atomic():
            # delete previous answers
            Answer.objects.filter(voter=voter, question=self.question).delete()

            for index, option_pk in enumerate(options):
                if option_pk is None or option_pk == '' or len(option_pk) == 0:
                    continue

                option_column = Option.objects.get(pk=option_pk)
                option = Option.objects.get(pk=self.rows[index][0])

                Answer.objects.create(
                    question=self.question,
                    voter=voter,
                    option=option,
                    option_column=option_column,
                )

    def set_initial(self, voter):
        self.fields['matrix'].initial = Answer.objects.get_vote_for_matrix(voter, self.question)


class VoterMatrixRadioForm(VoteMatrixRadioForm):
    def __init__(self, question, voter, *args, **kwargs):
        self.show_quiz_correct_options = kwargs.pop('show_quiz_correct_options') if 'show_quiz_correct_options' in kwargs else False

        super().__init__(question=question, voter=voter, *args, **kwargs)
        self.fields['matrix'].widget.attrs['disabled'] = 'disabled'

        # correct options
        if question.is_quiz and self.show_quiz_correct_options:
            self.fields['matrix'].widget.attrs['correct_options'] = \
                list(question.option_set.correct().values_list('id', flat=True))

    @staticmethod
    def get_result(question, voter):
        num_columns = question.option_set.columns().count()

        if num_columns != 2:
            raise ValueError('Incorrect number of columns (%d)' % num_columns)

        answers = Answer.objects.filter(voter=voter, question=question)

        rows = question.option_set.rows()
        columns = question.option_set.columns()
        num_rows = rows.count()

        selected_correctly = answers.filter(
            Q(option_id__in=rows.correct(), option_column_id__in=columns.correct()) |
            Q(option_id__in=rows.incorrect(), option_column_id__in=columns.incorrect())
        )
        num_selected_correctly = selected_correctly.count()

        # 4/4 = 1, 3/4 = 0.75, 2/4 = 0.5, 1/4 = 0.25, 0/4 = 0
        result = float(num_selected_correctly) / num_rows

        return math.floor(round(result, 2))  # eskills
        # return round(result, 2)            # votebase
