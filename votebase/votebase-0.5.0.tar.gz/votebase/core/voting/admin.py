from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from votebase.core.voting.models import Voter, Answer


class QuizResultSentFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('quiz result sent')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_quiz_result_sent'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value
        # to decide how to filter the queryset.
        from votebase.core.questionnaires.models import Survey
        quizzes = Survey.objects.quizzes()

        if self.value() == 'yes':
            return queryset.filter(is_quiz_result_sent=True, round__survey__in=quizzes)

        if self.value() == 'no':
            return queryset.filter(is_quiz_result_sent=False, round__survey__in=quizzes)


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    actions = ['send_quiz_result', 'recalculate_quiz_result']
    list_display = ('user', 'survey', 'quiz_result', 'is_quiz_result_sent', 'is_api_voter', 'is_irrelevant', 'language', 'voting_duration', 'voting_started', 'voting_ended')
    list_filter = (QuizResultSentFilter, 'is_api_voter', 'is_irrelevant', 'language', 'survey')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'hash_key']
    list_editable = ['is_irrelevant', ]
    autocomplete_fields = ['user', 'survey']
    # readonly_fields = ['survey']
    list_select_related = ['user', 'survey']

    def send_quiz_result(self, request, queryset):
        for voter in queryset:
            voter.send_quiz_result()

    def recalculate_quiz_result(self, request, queryset):
        for voter in queryset:
            voter.calculate_quiz_result(recalculate=True)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'voter', 'survey', 'question', 'option', 'option_column', 'created']
    list_select_related = ['voter__user', 'voter__survey', 'question', 'option', 'option_column']
    list_filter = ['voter__survey']
    search_fields = ['option__title', 'question__title', 'question__tag']

    def survey(self, obj):
        return obj.voter.survey
