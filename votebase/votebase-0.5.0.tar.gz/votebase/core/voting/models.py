import hashlib
import random
from django.conf import settings

from django.core.cache import cache
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from python_pragmatic.strings import generate_hash

from votebase.core.questionnaires.models import Survey, Question, Option
from votebase.core.voting.managers import AnswerManager, VoterQuerySet


class Voter(models.Model):
    survey = models.ForeignKey(Survey, verbose_name=_('survey'), on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'),
        default=None, null=True, blank=True, on_delete=models.CASCADE)
    language = models.CharField(_('language'), max_length=2, choices=settings.LANGUAGES)
    quiz_result = models.FloatField(verbose_name=_('quiz result'), db_index=True,
        default=None, null=True, blank=True)
    hash_key = models.CharField(_('hash key'), max_length=255, db_index=True)
    ip_address = models.CharField(_('IP address'), max_length=255, blank=True)
    voting_started = models.DateTimeField(_('voting started'))
    voting_ended = models.DateTimeField(_('voting ended'),
        null=True, blank=True, default=None)
    voting_duration = models.PositiveIntegerField(_('voting duration'), db_index=True,
        null=True, blank=True, default=None)
    flag = models.CharField(_('custom flag'), max_length=256,
        blank=True)
    is_quiz_result_sent = models.BooleanField(_('quiz result sent'), default=False, db_index=True)
    is_api_voter = models.BooleanField(_('API voter'), default=False)
    is_irrelevant = models.BooleanField(_('irrelevant'), default=False, db_index=True)
    voted_questions = models.ManyToManyField(to=Question, through='voting.VotedQuestion', related_name='voter_set_voted')
    answered_questions = models.ManyToManyField(to=Question, through='voting.Answer', related_name='voter_set_answered')
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = VoterQuerySet.as_manager()

    class Meta:
        verbose_name = _('respondent')
        verbose_name_plural = _('respondents')
        ordering = ('-created', )
        constraints = [
            UniqueConstraint(
                fields=['survey', 'user'],
                condition=Q(voting_ended=None),
                name='unique_user_survey_voter'
            )  # ensures that each user can start voting in survey only once.
        ]

    def __str__(self):
        return self.user.get_full_name() if self.user else str(self.pk)

    def get_absolute_url(self):
        return reverse('votebase:voting_voter', args=(str(self.hash_key), ))

    @property
    def categories(self):
        return list(set(self.voted_questions.order_by('weight').values_list('category', flat=True)))

    def has_categories(self):
        return len(self.categories) > 0 and self.categories[0] not in EMPTY_VALUES

    def get_voting_duration_timedelta(self):
        return self.voting_ended - self.voting_started

    def get_question_result(self, question):
        try:
            return question.get_voter_form_class().get_result(question, self)
        except AttributeError:
            return None

    def get_quiz_result(self, questions=None):
        quiz_result_handler_name = getattr(settings, 'VOTEBASE_QUIZ_RESULT_HANDLER', 'votebase.core.voting.handlers.quiz_result')
        quiz_result_handler = import_string(quiz_result_handler_name)
        return quiz_result_handler(self, questions)

    def get_quiz_result_display(self):
        if not self.survey.is_quiz or not self.voting_ended:
            return ''

        if self.quiz_result is None:
            self.quiz_result = self.get_quiz_result()  # TODO: questions
            self.save(update_fields=['quiz_result'])

        rounded = round(self.quiz_result)

        return f'{rounded}%' if self.quiz_result == rounded else f'{self.quiz_result}%'

    def send_quiz_result(self):
        quiz_result_mail_handler_name = getattr(settings, 'VOTEBASE_QUIZ_RESULT_MAIL_HANDLER', 'votebase.core.utils.mail.send_quiz_result_to_voter_in_background')
        quiz_result_mail_handler = import_string(quiz_result_mail_handler_name)
        return quiz_result_mail_handler.delay(self)

    def generate_unique_hash(self):
        while True:
            hash_key = generate_hash(length=30)
            if not Voter.objects.filter(hash_key=hash_key).count():
                break
        return hash_key

    def save(self, **kwargs):
        if self.hash_key in EMPTY_VALUES:
            self.hash_key = self.generate_unique_hash()

        if self.voting_ended and not self.voting_duration:
            self.voting_duration = (self.voting_ended - self.voting_started).seconds

        super(Voter, self).save(**kwargs)

    def time_limit_expired(self):
        if self.survey.time_limit is None:
            return False
        return self.time_limit() < now()

    def time_limit(self):
        if self.survey.time_limit is None:
            return None
        return self.voting_started + self.survey.time_limit

    def end(self):
        # update datetime when voting ended
        if self.voting_ended is None:
            self.voting_ended = now()

        # Save voter quiz result
        if self.survey.is_quiz and self.quiz_result is None:
            # TODO: move to background queue
            self.calculate_and_send_quiz_result()

        self.save()

    def calculate_quiz_result(self, recalculate=False):
        # save quiz results of voted questions
        voted_questions = self.votedquestion_set.all()

        if not recalculate:
            voted_questions = voted_questions.filter(quiz_result=None, question__is_quiz=True)

        for voted_question in voted_questions:
            voted_question.save_quiz_result()

        # get overall quiz result
        if self.quiz_result is None or recalculate:
            self.quiz_result = self.get_quiz_result()

    def calculate_and_send_quiz_result(self):
        self.calculate_quiz_result()

        # Send email with quiz results to voter if permitted
        if self.survey.is_quiz_result_visible and not self.is_quiz_result_sent and self.user:
            self.send_quiz_result()


class VotedQuestion(models.Model):
    voter = models.ForeignKey(Voter, verbose_name=_('voter'), on_delete=models.CASCADE)
    question = models.ForeignKey(Question, verbose_name=_('question'), on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(_('weight'), default=0, db_index=True)
    page = models.PositiveIntegerField(_('page'), default=1)
    quiz_result = models.FloatField(verbose_name=_('quiz result'), db_index=True,
        default=None, null=True, blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('voted question')
        verbose_name_plural = _('voted questions')
        ordering = ('weight', 'pk')
        unique_together = [('voter', 'question'),]

    def __str__(self):
        return self.question.title_i18n

    def save(self, **kwargs):
        # save quiz result
        if self.quiz_result is None and self.question.survey.is_quiz and self.voter.voting_ended:
            self.save_quiz_result()
        super(VotedQuestion, self).save(**kwargs)

    def save_quiz_result(self):
        self.quiz_result = self.voter.get_question_result(self.question)  # TODO: resave once voter is ended
        self.save(update_fields=['quiz_result'])

    @property
    def answer_set(self):
        return Answer.objects.filter(question=self.question, voter=self.voter)


class Answer(models.Model):
    ORIENTATION_ROW = 'ROW'
    ORIENTATION_COLUMN = 'COLUMN'
    ORIENTATIONS = (
        (ORIENTATION_ROW, _('Row')),
        (ORIENTATION_ROW, _('Column')),
    )

    voter = models.ForeignKey(Voter, verbose_name=_('voter'), on_delete=models.CASCADE)
    question = models.ForeignKey(Question, verbose_name=_('question'), on_delete=models.CASCADE)
    custom = models.TextField(
        _('custom'), null=True, blank=True, default=None)
    option = models.ForeignKey(
        Option, verbose_name=_('option'), default=None, null=True, blank=True, on_delete=models.PROTECT)
    option_column = models.ForeignKey(
        Option, verbose_name=_('option column'), default=None, null=True,
        blank=True, related_name='option_column', on_delete=models.PROTECT)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = AnswerManager()

    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        ordering = ('-created', )
        unique_together = [('voter', 'question', 'option', 'option_column'), ]
        #
        constraints = [
            # TODO: unique_together = [('voter', 'question',), ] for RADIO question KIND
            UniqueConstraint(
                fields=['voter', 'question'],
                condition=~Q(custom=None),
                name='unique_voter_question_custom'
            )  # ensures that each user can have only one custom answer per question
        ]

    def __str__(self):
        return str(self.pk)
