from django import template

from votebase.core.questionnaires.models import Question
from votebase.core.statistics.managers import OptionsStatsManager, TextStatsManager, MatrixStatsManager
from votebase.core.voting.models import Voter

register = template.Library()


@register.simple_tag(takes_context=True)
def question_statistics(context, question, filter_params):
    from eskills.core.statistics.filters import StatisticsFilter
    filter_class = StatisticsFilter  # TODO: move to settings
    filter = filter_class(context['request'], filter_params, queryset=Voter.objects.relevant())

    if isinstance(question, int):
        question = Question.objects.get(id=question)

    if 'TEXT' in question.kind:
        manager = TextStatsManager(question, filter.qs)
    elif 'MATRIX' in question.kind:
        manager = MatrixStatsManager(question, filter.qs)
    else:
        manager = OptionsStatsManager(question, filter.qs)

    return manager.render()
