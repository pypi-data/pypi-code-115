from django.db.models import QuerySet, Q
from django.utils import timezone


class SurveyQuerySet(QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def available(self):
        today = timezone.now()
        return self.filter(Q(is_active=True) & (Q(date_from__lte=today) | Q(date_from__isnull=True)) & (Q(date_to__gte=today) | Q(date_to__isnull=True)))

    def unavailable(self):
        today = timezone.now()
        return self.exclude(Q(is_active=True) & (Q(date_from__lte=today) | Q(date_from__isnull=True)) & (Q(date_to__gte=today) | Q(date_to__isnull=True)))

    def quizzes(self):
        """ Gets quizzes only """
        return self.filter(question__is_quiz=True).distinct()

    def not_quizzes(self):
        """ Gets non-quizzes only """
        return self.exclude(question__is_quiz=True).distinct()


class OptionQuerySet(QuerySet):
    def rows(self):
        return self.filter(orientation=self.model.ORIENTATION_ROW)

    def columns(self):
        return self.filter(orientation=self.model.ORIENTATION_COLUMN)

    def prepare_as_list(self):
        return self.values_list('id', 'title_i18n')

    def correct(self):
        return self.filter(is_correct=True)

    def incorrect(self):
        return self.filter(is_correct=False)
