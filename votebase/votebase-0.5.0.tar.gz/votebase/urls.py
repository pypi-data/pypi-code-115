from django.conf.urls import include
from django.urls import path
from django.utils.translation import ugettext_lazy as _

app_name = 'votebase'

urlpatterns = [
    path(_('surveys/'), include('votebase.core.questionnaires.urls')),
    path(_('voting/'), include('votebase.core.voting.urls')),
    path(_('statistics/'), include('votebase.core.statistics.urls')),
]
