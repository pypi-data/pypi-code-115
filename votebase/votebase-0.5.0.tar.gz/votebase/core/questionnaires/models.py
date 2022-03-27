from datetime import timedelta

import django
from crispy_forms.helper import FormHelper
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from modeltrans.fields import TranslationField
from pragmatic.mixins import SlugMixin
from python_pragmatic.strings import generate_hash
from tinymce.models import HTMLField

from votebase.core.questionnaires.querysets import SurveyQuerySet, OptionQuerySet


class Survey(SlugMixin, models.Model):
    FORCE_SLUG_REGENERATION = False

    MAX_DURATION = 60 * 12  # 12 hours

    PERMISSION_LEVEL_PUBLIC = 'PUBLIC'
    PERMISSION_LEVEL_REGISTERED = 'REGISTERED'
    PERMISSION_LEVEL_PRIVATE = 'PRIVATE'

    PERMISSION_LEVELS = (
        (PERMISSION_LEVEL_PUBLIC, _('Public - for everyone')),
        (PERMISSION_LEVEL_REGISTERED, _('Registered users only')),
        #        (PERMISSION_LEVEL_PRIVATE, _('Private - invites only')),
    )

    STATISTICS_POLICY_PUBLIC = 'PUBLIC'
    STATISTICS_POLICY_SECRET = 'SECRET'
    STATISTICS_POLICY_PRIVATE = 'PRIVATE'

    STATISTICS_POLICIES = (
        (STATISTICS_POLICY_PUBLIC, _('Public - for everyone')),
        (STATISTICS_POLICY_SECRET, _('Secret - for voters only')),
        (STATISTICS_POLICY_PRIVATE, _('Private - for creator only')),
    )

    title = models.CharField(_('title'), max_length=150)
    slug = models.SlugField(unique=True, max_length=SlugMixin.MAX_SLUG_LENGTH, blank=True)
    hash_key = models.CharField(_('hash key'), max_length=30, db_index=True, unique=True, blank=True)
    tag = models.CharField(_('tag'), max_length=40, db_index=True, blank=True)
    preface = models.TextField(_('preface'), blank=True)
    postface = models.TextField(_('postface'), blank=True)
    date_from = models.DateTimeField(_('valid from'), db_index=True,
                                     blank=True, null=True, default=now,
                                     help_text=_('Users can start voting beginning this date.'))
    date_to = models.DateTimeField(_('valid to'), db_index=True,
                                   blank=True, null=True, default=None,
                                   help_text=_('Users will be able to vote until this date. Keep blank to unlimited.'))
    time_limit = models.DurationField(_('time limit'), help_text=_('In minutes. Keep blank to infinite.'), blank=True, null=True, default=None,
                                    validators=[MinValueValidator(timedelta(minutes=1))])
    password = models.CharField(_('password'), null=True, blank=True, default=None, max_length=20)
    permission_level = models.CharField(_('permission level'), choices=PERMISSION_LEVELS, max_length=10,
        default=PERMISSION_LEVEL_PUBLIC)
    statistics_policy = models.CharField(_('statistics policy'), choices=STATISTICS_POLICIES, max_length=7,
        default=STATISTICS_POLICY_PRIVATE)
    is_active = models.BooleanField(_('active'), default=True, db_index=True, help_text=_('Current survey status. Users will not be able to start voting if inactive.'))
    is_repeatable = models.BooleanField(_('repeatable voting'), default=False, db_index=True,
        help_text=_('Set checked if users can vote multiple times in survey.'))
    is_quiz_result_visible = models.BooleanField(_('show quiz results'), default=False, db_index=True,
        help_text=_('Set checked if you want to show quiz results in percentage to voters.'))
    is_quiz_correct_options_visible = models.BooleanField(_('show quiz correct options'), default=False, db_index=True,
        help_text=_('Set checked if you want to show correct options to voters.'))
    is_published = models.BooleanField(_('published'), default=True,
        help_text=_('Set checked if users can see survey.')
    )
    # TODO: description
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    i18n = TranslationField(fields=('title', 'slug', 'preface', 'postface'))
    objects = SurveyQuerySet.as_manager()

    class Meta:
        verbose_name = _('survey')
        verbose_name_plural = _('surveys')
        ordering = ('-created', )

    def __str__(self):
        return self.title_i18n

    @cached_property
    def is_quiz(self):
        return self.question_set.filter(is_quiz=True).exists()

    def is_available(self):
        today = timezone.now()

        if not self.is_active:
            return False

        return (self.date_from is None or self.date_from <= today) and \
               (self.date_to is None or self.date_to >= today)

    def save(self, **kwargs):
        if self.hash_key in EMPTY_VALUES:
            self.hash_key = self.generate_unique_hash()
        super().save(**kwargs)

    def generate_unique_hash(self):
        while True:
            hash_key = generate_hash(length=30)
            if not Survey.objects.filter(hash_key=hash_key).count():
                break
        return hash_key

    def get_absolute_url(self):
        return self.get_voting_url()

    def get_voting_url(self):
        return reverse('votebase:voting', args=(self.slug_i18n,))

    def get_preview_url(self):
        return reverse('votebase:survey_preview', args=(self.slug_i18n,))

    def get_infographics_url(self):
        return f"{reverse('votebase:statistics_infographics')}?survey={self.slug_i18n}"

    def get_statistics_url(self):
        return f"{reverse('votebase:statistics_answers')}?survey={self.slug_i18n}"

    def get_new_voters_count(self, compare_date):
        return self.voter_set.filter(
            created__gte=compare_date).count()

    @property
    def categories(self):
        return list(set(self.question_set.order_by('weight').values_list('category', flat=True)))

    def has_categories(self):
        return len(self.categories) > 0 and self.categories[0] not in EMPTY_VALUES

    def is_date_in_range(self):
        now = django.utils.timezone.now()

        # limited by start and end
        if self.date_from and self.date_to:
            return self.date_from <= now <= self.date_to

        # limited by start
        if self.date_from:
            return self.date_from <= now

        # limited by end
        if self.date_to:
            return now <= self.date_to

        # unlimited
        #     if not self.date_from and not self.date_to:
        return True

    def is_secured(self):
        if self.password in EMPTY_VALUES:
            return False
        return self.password.strip() not in EMPTY_VALUES

    def user_already_voted(self, user):
        if not user.is_authenticated:
            return False
        return self.voter_set\
            .filter(user=user)\
            .exclude(voting_ended=None)\
            .exists()

    def continue_voter(self, user):
        try:
            return self.voter_set.get(user=user, voting_ended=None)  # TODO: constraint
        except ObjectDoesNotExist:
            return None


class Question(models.Model):
    KIND_RADIO = 'RADIO'
    KIND_CHECKBOX = 'CHECKBOX'
    KIND_DROPDOWN = 'DROPDOWN'
    KIND_TEXTFIELD = 'TEXTFIELD'
    KIND_TEXTAREA = 'TEXTAREA'
    KIND_MATRIX_RADIO = 'MATRIX_RADIO'
    KIND_MATRIX_CHECKBOX = 'MATRIX_CHECKBOX'

    KINDS = (
        (KIND_RADIO, _('Radio')),
        (KIND_CHECKBOX, _('Checkbox')),
        (KIND_DROPDOWN, _('Dropdown')),
        (KIND_TEXTFIELD, _('Textfield')),
        (KIND_TEXTAREA, _('Textarea')),
        (KIND_MATRIX_RADIO, _('Matrix radio')),
        (KIND_MATRIX_CHECKBOX, _('Matrix checkbox')),
    )

    survey = models.ForeignKey(Survey, verbose_name=_('survey'), on_delete=models.CASCADE)
    tag = models.CharField(_('tag'), max_length=10, db_index=True, blank=True)
    kind = models.CharField(_('kind'), choices=KINDS, max_length=15, db_index=True)
    title = HTMLField(_('title'))
    # title = MartorField(_('title'))
    category = models.CharField(_('category'), max_length=255, db_index=True, blank=True)
    weight = models.PositiveIntegerField(_('weight'), default=0, db_index=True)
    is_required = models.BooleanField(_('mandatory'), default=False)
    is_quiz = models.BooleanField(_('quiz'), default=False, db_index=True)
    is_unique_answers = models.BooleanField(_('unique answers'), help_text=_('for matrix questions'), default=False)
    is_empty_row_enabled = models.BooleanField(_('enabled empty rows'), help_text=_('for matrix questions with required answer'), default=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    i18n = TranslationField(fields=('title', 'category'))

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ('weight', 'created')
        # unique_together = [('survey', 'tag'), ]
        constraints = [
            # not empty tag
            models.UniqueConstraint(fields=['survey', 'tag'], name='unique_question_tag', condition=~Q(tag__in=EMPTY_VALUES))
        ]

    def __repr__(self):
        return strip_tags(self.title_i18n)

    def __str__(self):
        return self.tag if self.tag not in EMPTY_VALUES else '#' + str(self.pk)
        # return mark_safe(self.title_i18n)  # dangerous in admin breadcrumb

    def save(self, **kwargs):
        if not self.pk:
            self.weight = self.survey.question_set.all().count()
        super(Question, self).save(**kwargs)

    def get_absolute_url(self):
        url_name = 'questions_update_%s' % self.kind.lower()
        return reverse(url_name, args=(self.pk, ))

    def get_voting_form(self, post_data=None, number=1, voter=None):
        module_name = 'votebase.core.questionnaires.forms.%s' % self.kind.lower()
        form_class_name = 'Vote%sForm' % self.kind.title().replace('_', '')
        form_class = import_string(f'{module_name}.{form_class_name}')
        form = form_class(question=self, number=number, voter=voter, prefix=self.pk, data=post_data)

        if not getattr(form, 'helper', None):
            form.helper = FormHelper()
            form.helper.form_tag = False

        return form

    def get_voter_form_class(self):
        module_name = 'votebase.core.questionnaires.forms.%s' % self.kind.lower()
        class_name = 'Voter%sForm' % self.kind.title().replace('_', '')
        custom_voter_forms = getattr(settings, 'VOTEBASE_VOTER_FORMS', {})
        class_path = custom_voter_forms.get(self.kind, '{}.{}'.format(module_name, class_name))
        form_class = import_string(class_path)
        return form_class

    def get_voter_form(self, voter, number=1, *args, **kwargs):
        form_class = self.get_voter_form_class()
        form = form_class(question=self, voter=voter, number=number, prefix=self.pk, *args, **kwargs)

        if not getattr(form, 'helper', None):
            form.helper = FormHelper()
            form.helper.form_tag = False

        return form

    def get_choices(self):
        choices = cache.get('question_choices', version=self.pk)
        use_cache = getattr(settings, 'VOTEBASE_USE_QUESTION_CHOICES_CACHE', True)

        if not choices or not use_cache:
            choices = []

            option_set = self.option_set.all()

            for option in option_set:
                title = f'{option.title_i18n}'.strip()
                choice = (option.pk, mark_safe(title))
                choices.append(choice)

        cache.set('question_choices', choices, version=self.pk, timeout=60*60*12)

        return choices

    def get_number(self):
        """ Gets question order in a list """
        survey_questions = self.survey.question_set
        questions_list = list(survey_questions.values_list('id', flat=True))
        return questions_list.index(self.id) + 1

    def get_label(self, number):
        """ Gets HTML title  """

        if number:
            label = '<span class="counter"><span class="number">\
            %(number)s</span><span class="dot">.</span></span> %(title)s' % {
                'number': number,
                'title': self.title_i18n,
            }
        else:
            label = '%(title)s' % {
                'title': self.title_i18n,
            }

        return mark_safe(label)


class Option(models.Model):
    ORIENTATION_ROW = 'ROW'
    ORIENTATION_COLUMN = 'COLUMN'
    ORIENTATIONS = (
        (ORIENTATION_ROW, _('Row')),
        (ORIENTATION_COLUMN, _('Column')),
    )

    question = models.ForeignKey(Question, verbose_name=_('question'), on_delete=models.CASCADE)
    tag = models.CharField(_('tag'), max_length=10, db_index=True, blank=True)
    title = HTMLField(_('title'))
    orientation = models.CharField(
        _('orientation'), choices=ORIENTATIONS, default=ORIENTATION_ROW,
        max_length=6)
    is_correct = models.BooleanField(_('correct'), default=False, db_index=True)
    weight = models.PositiveIntegerField(_('weight'), default=0, db_index=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = OptionQuerySet.as_manager()
    i18n = TranslationField(fields=('title',))

    class Meta:
        verbose_name = _('option')
        verbose_name_plural = _('options')
        ordering = ('weight', 'created')
        constraints = [
            # not empty tag
            models.UniqueConstraint(fields=['question', 'tag'], name='unique_option_tag', condition=~Q(tag__in=EMPTY_VALUES))
        ]

    def __repr__(self):
        return strip_tags(self.title_i18n)

    def __str__(self):
        return self.tag if self.tag not in EMPTY_VALUES else '#' + str(self.pk)
        # return mark_safe(self.title_i18n)  # dangerous in admin breadcrumb

    def save(self, **kwargs):
        if not self.pk and not self.weight:
            # TODO: latest weight
            self.weight = self.question.option_set.all().count()

        super(Option, self).save(**kwargs)
