from django.urls import path
from django.utils.translation import pgettext_lazy

from votebase.core.voting.views import VoteView, FinishView, \
    InactiveView, AlreadyVotedView, OnlyForRegisteredView, PasswordView, VoterDetailView, TimeExpiredView


urlpatterns = [
    path(pgettext_lazy('url', 'finish/<str:slug>/'), FinishView.as_view(slug_field='slug_i18n'), name='voting_finish'),
    path(pgettext_lazy('url', 'inactive/<str:slug>/'), InactiveView.as_view(slug_field='slug_i18n'), name='voting_inactive'),
    path(pgettext_lazy('url', 'password/<str:slug>/'), PasswordView.as_view(), name='voting_password'),
    path(pgettext_lazy('url', 'already-voted/<str:slug>/'), AlreadyVotedView.as_view(slug_field='slug_i18n'), name='voting_already_voted'),
    path(pgettext_lazy('url', 'expired/<str:slug>/'), TimeExpiredView.as_view(slug_field='slug_i18n'), name='voting_expired'),
    path(pgettext_lazy('url', 'only-for-registered/<str:slug>/'), OnlyForRegisteredView.as_view(slug_field='slug_i18n'), name='voting_for_registered'),
    path(pgettext_lazy('url', 'respondent/<str:hash_key>/'), VoterDetailView.as_view(), name='voting_voter'),
    path('<str:slug>/', VoteView.as_view(slug_field='slug_i18n'), name='voting'),
]
