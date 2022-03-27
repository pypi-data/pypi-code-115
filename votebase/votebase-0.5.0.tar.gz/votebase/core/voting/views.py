from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.validators import EMPTY_VALUES
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from votebase import settings as votebase_settings
from votebase.core.questionnaires.models import Survey, Question
from votebase.core.utils import mail
from votebase.core.voting.forms import PasswordForm
from votebase.core.voting.models import Voter, VotedQuestion


def get_password_ident(survey):
    return 'password_%s' % survey.pk


def get_welcome_ident(survey):
    return 'welcome_%s' % survey.pk


class VoteView(DetailView):
    model = Survey
    template_name = 'voting/voting.html'
    slug_field = 'slug_i18n'

    def dispatch(self, request, *args, **kwargs):
        voting_prerequisites = import_string(votebase_settings.VOTING_PREREQUISITES)
        prerequisites_result = voting_prerequisites(request)

        if prerequisites_result is not None:
            return prerequisites_result

        # get survey
        self.survey = self.get_object()

        # Inactive survey
        if not self.is_active():
            return redirect(reverse('votebase:voting_inactive', args=(self.survey.slug_i18n, )))

        # Permission restriction
        if self.survey.permission_level == Survey.PERMISSION_LEVEL_REGISTERED and not request.user.is_authenticated:
            return redirect(reverse('votebase:voting_for_registered', args=(self.survey.slug_i18n, )))

        # Repeatable voting
        if not self.survey.is_repeatable and self.survey.user_already_voted(request.user):
            return redirect(reverse('votebase:voting_already_voted', args=(self.survey.slug_i18n, )))

        # Secured by password
        if get_password_ident(self.survey) not in request.session:
            if self.survey.is_secured():
                return redirect(reverse('votebase:voting_password', args=(self.survey.slug_i18n, )))

        # check existing previous voting
        # TODO: what about anonymous users voting?
        self.voter = self.survey.continue_voter(request.user)

        if self.voter is not None and self.survey.time_limit is not None:
            if self.voter.time_limit_expired():
                messages.warning(request, _("Time expired and your answers have been saved automatically"))

                # repeatable voting, finish current voter
                self.voter.end()

                return redirect(reverse('votebase:voting_expired', args=(self.survey.slug_i18n,)))

                # if not self.survey.is_repeatable:
                #     # Time limit expired
                #     return redirect(reverse('votebase:voting_expired', args=(self.survey.slug_i18n,)))
                # else:
                #     # start again
                #     # self.voter = None
                #     return redirect(request.META.get('HTTP_REFERER', reverse('home')))

        # create new voter (voting initialization)
        if self.voter is None:
            self.voter = Voter.objects.create(
                survey=self.survey,
                user=request.user,  # TODO: what about anonymous voting?
                voting_started=now(),
                language=self.request.LANGUAGE_CODE,
                ip_address=request.META['REMOTE_ADDR'],
            )

        # Get questions
        voted_questions = self.voter.votedquestion_set.all()

        if voted_questions.exists():
            # get existing voter questions
            self.questions = self.get_voter_questions(voted_questions)
        else:
            # generate new questions for voter and save the selection
            self.questions = self.get_new_questions()

            # Save voted questions list of voter
            for index, question in enumerate(self.questions):
                VotedQuestion.objects.update_or_create(
                    voter=self.voter,
                    question=question,
                    defaults={'weight': index}
                )

        return super(VoteView, self).dispatch(request, *args, **kwargs)

    def get_new_questions(self):
        questions_picker = import_string(votebase_settings.QUESTIONS_PICKER)
        questions = questions_picker(self.survey)
        return questions.prefetch_related('option_set').order_by('weight')

    def get_voter_questions(self, voted_questions):
        questions_pks = voted_questions.values_list('question__pk', flat=True)
        questions = Question.objects.filter(pk__in=questions_pks)
        return questions.prefetch_related('option_set').order_by('weight')

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'voter': self.voter,
            'question_forms': [question.get_voting_form(number=index + 1, voter=self.voter) for index, question in enumerate(self.questions)],
        })
        return context_data

    def post(self, request, slug):
        is_valid = True
        forms = []

        # Validate all forms
        for index, question in enumerate(self.questions):
            form = question.get_voting_form(request.POST, number=index + 1)
            if not form.is_valid():
                is_valid = False
            forms.append(form)

        if is_valid or 'bypass_validation' in request.GET:
            # Save all forms
            # TODO: check existing voted questions (continuous save)
            for form in forms:
                if form.is_valid():
                    form.save(self.voter)

            self.voter.end()

            # Send email about new voter if necessary
            try:
                threshold = 100  # TODO: settings
                if not self.survey.voter_set.count() % threshold:
                    mail.new_voters(self.survey, request)
            except ZeroDivisionError:
                pass

            messages.success(request, _('Your response has been successfully saved.'))
            return redirect(reverse('votebase:voting_finish', args=(self.survey.slug_i18n, )))
        else:
            messages.error(request, _('Make sure that you have answered all required questions.'))

        return self.render_to_response({
            'survey': self.survey,
            'voter': self.voter,
            'question_forms': forms,
        })

    def get_queryset(self):
        return super().get_queryset().prefetch_related('question_set')  # TODO: options

    def is_active(self):
        if not self.survey.is_active:
            return False

        if not self.survey.is_date_in_range():
            return False

        return True


class InactiveView(DetailView):
    template_name = 'voting/inactive.html'
    model = Survey


class OnlyForRegisteredView(DetailView):
    template_name = 'voting/only_for_registered.html'
    model = Survey


class AlreadyVotedView(LoginRequiredMixin, DetailView):
    template_name = 'voting/already_voted.html'
    model = Survey


class TimeExpiredView(LoginRequiredMixin, DetailView):
    template_name = 'voting/time_expired.html'
    model = Survey


class PasswordView(FormView):
    template_name = 'voting/password.html'
    form_class = PasswordForm

    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, slug_i18n=kwargs.get('slug'))
        self.password_ident = get_password_ident(self.survey)

        if self.password_ident in request.session:
            return redirect(reverse('votebase:voting', args=(self.survey.slug_i18n, )))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['survey'] = self.survey
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['survey'] = self.survey
        return form_kwargs

    def get_success_url(self):
        return self.survey.get_voting_url()

    def form_valid(self, form):
        if self.password_ident not in self.request.session:
            self.request.session[self.password_ident] = True
        return super(PasswordView, self).form_valid(form)


class FinishView(DetailView):
    template_name = 'voting/finish.html'
    model = Survey

    def dispatch(self, request, *args, **kwargs):
        voter_id = request.session.get('voter', None)
        self.voter = Voter.objects.get(pk=voter_id) if voter_id else None
        self.survey = self.get_object()

        # Redirect to voter results if survey is quiz
        #TODO: postface is hidden now, it should be displayed somewhere
        # if self.survey.is_quiz and self.survey.is_quiz_result_visible and self.voter:
        #     return redirect(self.voter.get_absolute_url())

        if self.survey.postface in EMPTY_VALUES:
            return redirect(self.get_finish_url())

        return super().dispatch(request, *args, **kwargs)

    def get_finish_url(self):
        handler = votebase_settings.FINISH_URL_HANDLER

        if not handler:
            return self.voter.get_absolute_url() if self.voter else reverse('home')

        return import_string(handler)(self.voter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['voter'] = self.voter
        context['finish_url'] = self.get_finish_url()
        return context


class VoterDetailView(DetailView):
    model = Voter
    slug_url_kwarg = 'hash_key'
    slug_field = 'hash_key'

    def dispatch(self, request, *args, **kwargs):
        self.survey = self.get_object().survey
        self.show_quiz_result = self.is_quiz_result_visible(request.user)
        self.show_quiz_correct_options = self.is_quiz_correct_options_visible(request.user)

        voter = self.get_object()

        if not voter.voting_ended:
            if voter.time_limit_expired():
                # messages.warning(request, _("Time limit expired"))
                voter.end()
                # return redirect(request.META.get('HTTP_REFERER', reverse('home')))
            elif voter.user == request.user:
                return redirect(voter.survey.get_voting_url())
            else:
                messages.error(request, _("Respondent didn't finished the survey yet"))
                return redirect(request.META.get('HTTP_REFERER', reverse('home')))

        return super().dispatch(request, *args, **kwargs)

    def is_quiz_result_visible(self, user):
        # return self.survey.is_quiz_result_visible or user.is_staff
        return self.survey.is_quiz_result_visible

    def is_quiz_correct_options_visible(self, user):
        # return self.survey.is_quiz_correct_options_visible or user.is_staff
        return self.survey.is_quiz_correct_options_visible

    def get_voter_forms(self, voter):
        use_cache = getattr(settings, 'VOTEBASE_USE_VOTER_FORM_CACHE', True)
        forms = cache.get('voter_forms', version=voter.pk)

        if not forms or not use_cache:
            # Get list of voted questions
            voter_questions = voter.voted_questions.all()

            forms = []
            for index, question in enumerate(voter_questions):
                kwargs = {
                    'voter': voter,
                    'number': index + 1,
                }

                if question.is_quiz:
                    kwargs['show_quiz_correct_options'] = self.show_quiz_correct_options

                forms.append(question.get_voter_form(**kwargs))

            # PicklingError at /sk/voting/respondent/845db705cb827c76e210f13f0906d7/
            # Can't pickle <function paginator_number at 0x7f904b298840>: it's not the same object as django.contrib.admin.templatetags.admin_list.paginator_number
            # cache.set('voter_forms', forms, version=voter.pk, timeout=60 * 60 * 12)

        return forms

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data.update({
            'survey': self.survey,
            'forms': self.get_voter_forms(self.object),
            'show_quiz_result': self.show_quiz_result,
            'show_quiz_correct_options': self.show_quiz_correct_options
        })

        return context_data
