from django.urls import path
from django.utils.translation import pgettext_lazy

from votebase.core.statistics.views.graphs.general import AnswersView
from votebase.core.statistics.views.infographics import InfographicsView

urlpatterns = [
    path(pgettext_lazy('url', 'answers/'), AnswersView.as_view(), name='statistics_answers'),
    path(pgettext_lazy('url', 'infographics/'), InfographicsView.as_view(), name='statistics_infographics'),
]
