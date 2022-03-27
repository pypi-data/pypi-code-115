from django.views.generic import DetailView

from pragmatic.mixins import StaffRequiredMixin
from votebase.core.questionnaires.models import Survey


class PreviewView(StaffRequiredMixin, DetailView):
    model = Survey
    template_name = 'surveys/survey_preview.html'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('question_set')  # TODO: options

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        questions = self.get_object().question_set.all().prefetch_related('option_set')
        context_data['question_forms'] = [question.get_voting_form(number=index + 1) for index, question in enumerate(questions)]
        return context_data
