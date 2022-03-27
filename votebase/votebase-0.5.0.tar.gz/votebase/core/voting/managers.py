from django.db import models


class AnswerManager(models.Manager):
    def get_vote_for_true_false(self, voter, question):
        rows = question.option_set.rows()
        result = []

        answered_options = self.model.objects.filter(
            voter=voter, question=question
        ).values_list('option__pk', flat=True)

        for row in rows:
            if row.pk in answered_options:
                result.append(True)
            else:
                result.append(False)
        return result

    def get_vote_for_matrix(self, voter, question):
        rows = question.option_set.rows()
        result = []

        values = dict(self.model.objects.filter(
            voter=voter, question=question
        ).values_list('option__pk', 'option_column__pk'))

        for row in rows:
            if row.pk in values:
                result.append(values[row.pk])
            else:
                result.append(None)

        return result

    def get_vote_for_multiplematrix(self, voter, question):
        rows = question.option_set.rows()
        answers = self.model.objects.filter(voter=voter, question=question)
        results = {}

        for row in rows:
            results[row.pk] = []
            row_answers = answers.filter(option=row)

            for answer in row_answers:
                results[answer.option_id].append(answer.option_column_id)

        return [results[row.pk] for row in rows]


class VoterQuerySet(models.query.QuerySet):
    def by_survey(self, survey):
        return self.filter(survey=survey)

    def by_user(self, user):
        return self.filter(user=user)

    def ended(self):
        return self.exclude(voting_ended=None)

    def not_ended(self):
        return self.filter(voting_ended=None)

    def without_quiz_result(self):
        return self.filter(
            votedquestion__question__is_quiz=True,
            quiz_result=None).distinct()

    def relevant(self):
        return self.exclude(is_irrelevant=True)

    def order_by_voting_ended(self):
        return self.order_by('voting_ended')
