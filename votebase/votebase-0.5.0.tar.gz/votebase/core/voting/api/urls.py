from django.urls import path
from django.utils.translation import pgettext_lazy

from votebase.core.voting.api.views import VoteAPIView

app_name = 'voting'

urlpatterns = [
    path(pgettext_lazy("url", 'vote/'), VoteAPIView.as_view(), name='vote'),
]
