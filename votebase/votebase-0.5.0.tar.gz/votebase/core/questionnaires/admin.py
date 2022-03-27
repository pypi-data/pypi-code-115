from django.contrib import admin
from django.template.defaultfilters import yesno
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from modeltrans.admin import ActiveLanguageMixin

from votebase.core.questionnaires.models import Survey, Question, Option


class QuizFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('quiz')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_quiz'

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
        if self.value() == 'yes':
            return queryset.quizzes()

        if self.value() == 'no':
            return queryset.not_quizzes()


class QuestionInlines(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Survey)
class SurveyAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    search_fields = ['title_i18n', 'tag']
    list_display = ('id', 'title_i18n', 'tag', 'date_from', 'date_to', 'permission_level', 'statistics_policy', 'time_limit', 'attributes')
    list_display_links = ('id', 'title_i18n',)
    list_filter = ('is_published', 'is_active', QuizFilter,
                   'is_repeatable', 'is_quiz_result_visible', 'is_quiz_correct_options_visible',
                   'time_limit')
    # inlines = (QuestionInlines, )

    def attributes(self, instance):
        def image(value):
            return f'<img src="/static/admin/img/icon-{yesno(value, "yes,no")}.svg" alt="{value}">'

        return mark_safe('<br>'.join([
            f'{image(instance.is_published)} {_("Published")}',
            f'{image(instance.is_active)} {_("Active")}',
            f'{image(instance.is_repeatable)} {_("Repeatable")}',
            f'{image(instance.is_date_in_range())} {_("Date in range")}',
            f'{image(instance.is_quiz_result_visible)} {_("Quiz result visible")}',
            f'{image(instance.is_quiz_correct_options_visible)} {_("Correct options visible")}',
            f'{image(instance.is_secured())} {_("Secured")}',
        ]))


class OptionInline(ActiveLanguageMixin, admin.TabularInline):
    model = Option
    exclude = ('created', 'modified',)


@admin.register(Question)
class QuestionAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    search_fields = ['tag', 'title', 'category']
    list_display = ('tag', 'category_i18n', 'title_display', 'kind', 'weight', 'survey', 'is_required',
                    'is_quiz')
    list_display_links = ('tag', 'title_display',)
    list_filter = ('is_required', 'is_quiz', 'survey', 'category_i18n', 'tag', 'kind')
    inlines = (OptionInline, )

    def title_display(self, obj):
        return repr(obj)


@admin.register(Option)
class OptionAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ('title_display', 'tag', 'question', 'survey', 'weight', 'is_correct')
    list_display_links = ('title_display', )
    list_select_related = ['question', 'question__survey']
    list_filter = ['is_correct', 'question__survey', 'orientation']
    list_editable = ['tag', 'weight']
    search_fields = ['title', 'question__title', 'question__tag', 'tag']
    ordering = ['question__survey', 'question__weight', 'question__tag', 'tag']

    def title_display(self, obj):
        return repr(obj)

    def survey(self, obj):
        return obj.question.survey
