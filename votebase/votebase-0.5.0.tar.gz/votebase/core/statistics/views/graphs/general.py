from django.db.models.aggregates import Avg
from django.views.generic.list import ListView

from pragmatic.mixins import StaffRequiredMixin
from votebase.core.questionnaires.models import Question
from votebase.core.statistics.mixins import StatisticsFilterMixin
from votebase.core.utils.helpers import sorted_by_roman
from votebase.core.voting.models import VotedQuestion


class AnswersView(StaffRequiredMixin, StatisticsFilterMixin, ListView):
    model = Question
    template_name = 'statistics/survey_statistics.html'

    def get_queryset(self):
        # return self.survey.question_set.prefetch_related('answer_set')  # performance killer
        return self.survey.question_set.all() if self.survey else None  # answers are loaded using include_async instead

    def get_statistics(self):
        if self.survey.is_quiz:
            return {'statistics_categories': self.categories_info(survey=self.survey)}
        return {}

    def categories_info(self, survey):
        # questions
        questions = survey.question_set

        # voted questions
        segment_voted_questions = VotedQuestion.objects\
            .filter(question__survey=survey, voter__in=self.filter.qs)

        categories = list(set(questions.order_by('weight').values_list('category', flat=True)))
        categories = sorted_by_roman(categories)

        categories_info = []

        for category in categories:
            num_questions = questions.filter(category=category).count()
            voted_questions = segment_voted_questions.filter(question__category=category)
            quiz_result = voted_questions.aggregate(Avg('quiz_result'))['quiz_result__avg']
            percent = quiz_result * 100 if quiz_result is not None else None

            categories_info.append({
                'category': category,
                'percent': percent,
                'count_questions': num_questions
            })

        return categories_info
