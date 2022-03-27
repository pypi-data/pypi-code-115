from django.urls import path
from django.utils.translation import pgettext_lazy

from votebase.core.questionnaires.views import PreviewView

urlpatterns = [
    path(pgettext_lazy('url', 'preview/<str:slug>/'), PreviewView.as_view(slug_field='slug_i18n'), name='survey_preview'),
]
