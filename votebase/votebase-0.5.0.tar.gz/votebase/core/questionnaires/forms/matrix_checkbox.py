from django import forms
from django.db import transaction

from votebase.core.questionnaires.models import Option
from votebase.core.utils.fields import MatrixField
from votebase.core.utils.widgets import MatrixMultiple
from votebase.core.voting.models import Answer


class VoteMatrixCheckboxForm(forms.Form):
    def __init__(self, question, number=1, voter=None, *args, **kwargs):
        super(VoteMatrixCheckboxForm, self).__init__(*args, **kwargs)
        self.question = question
        self.rows = question.option_set.rows().prepare_as_list()
        self.columns = \
            question.option_set.columns().prepare_as_list()

        self.fields['matrix'] = MatrixField(
            widget=MatrixMultiple, label=question.title, rows=self.rows,
            columns=self.columns, required=question.is_required,
            unique_answers=question.is_unique_answers,
            empty_row_enabled=question.is_empty_row_enabled)

        self.fields['matrix'].label = self.question.get_label(number)

        if voter:
            self.set_initial(voter)

    def set_initial(self, voter):
        self.fields['matrix'].initial = Answer.objects.get_vote_for_multiplematrix(voter, self.question)

    def save(self, voter, commit=True):
        options_list = self.cleaned_data.get('matrix', '').split('-')

        with transaction.atomic():
            # delete previous answers
            Answer.objects.filter(voter=voter, question=self.question).delete()

            for index, options in enumerate(options_list):
                options_items = options.split('|')
                for option_pk in options_items:

                    if option_pk is None or option_pk == '' or len(option_pk) is 0:
                        continue

                    option_column = Option.objects.get(pk=option_pk)
                    option = Option.objects.get(pk=self.rows[index][0])
                    Answer.objects.create(
                        question=self.question,
                        voter=voter,
                        option=option,
                        option_column=option_column,
                    )


class VoterMatrixCheckboxForm(VoteMatrixCheckboxForm):
    def __init__(self, question, voter, *args, **kwargs):
        super().__init__(question=question, voter=voter, *args, **kwargs)
        self.fields['matrix'].widget.attrs['disabled'] = 'disabled'  # not working :/
        self.fields['matrix'].widget.disabled = True  # workaround
