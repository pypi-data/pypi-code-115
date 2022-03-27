from eskills.core.statistics.filters import StatisticsFilter
from votebase.core.questionnaires.models import Survey
from votebase.core.voting.models import Voter


class StatisticsFilterMixin(object):
    model = Voter
    filter_class = StatisticsFilter  # TODO: move to settings
    survey = None
    country = None

    def get(self, request, *args, **kwargs):
        self.filter = self.filter_class(request, request.GET, queryset=self.get_whole_queryset())
        self.country = self.filter.data.get('country')

        if self.filter.is_valid():
            survey_slug = self.filter.data.get('survey')
            self.survey = Survey.objects.get(slug_i18n=survey_slug) if survey_slug else None

        return super().get(request, *args, **kwargs)

    def get_whole_queryset(self):
        return Voter.objects.relevant()

    def get_queryset(self):
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter': self.filter,
            'survey': self.survey,
            'country': self.country,
        })

        if self.filter.is_valid():
            # TODO: cache
            context.update(self.get_statistics())
        return context

    def get_statistics(self):
        raise NotImplementedError()
