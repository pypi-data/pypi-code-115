from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.template import loader
from django.utils.translation import ugettext as _

from django_rq import job

from eskills.core.utils.templatetags.utils import uri  # TODO: move to pragmatic or votebase?


def quiz_result(voter):
    if not voter.user:
        return

    from_email = settings.DEFAULT_FROM_EMAIL
    subject = _('Quiz result')
    template = loader.get_template('mails/quiz_result.html')
    context_data = {
        'survey': voter.survey,
        'voter': voter,
        'host_url': settings.HOST_URL,
    }
    message = template.render(context_data)
    recipient_list = [voter.user.email, ]

    result = send_mail(subject, message, from_email, recipient_list, fail_silently=False)

    if result != voter.is_quiz_result_sent:
        voter.is_quiz_result_sent = result
        #voter.save(update_fields=['is_quiz_result_sent'])
        voter.save()

    return result


@job
def send_quiz_result_to_voter_in_background(voter):
    quiz_result(voter)


def new_voters(survey, request):
    from_email = settings.DEFAULT_FROM_EMAIL
    threshold = 100  # TODO: settings

    if threshold == 1:
        subject = _('New voter in your survey')
        message = _('You have one new voter in your survey %(survey)s') % {
            'survey': survey.title_i18n,
        }

        message_html = _('You have one new voter in your survey <a href="%(url)s">%(survey)s</a>') % {
            'survey': survey.title_i18n,
            'url': uri({'request': request}, survey.get_statistics_url())
        }
    else:
        subject = _('New voters in your survey')
        message = _('You have %(voters_count)d new voters in your survey %(survey)s') % {
            'survey': survey.title_i18n,
            'voters_count': threshold,
        }
        message_html = _('You have %(voters_count)d new voters in your survey <a href="%(url)s">%(survey)s</a>') % {
            'survey': survey.title_i18n,
            'voters_count': threshold,
            'url': uri({'request': request}, survey.get_statistics_url())
        }

    from django.core.mail import EmailMultiAlternatives
    msg = EmailMultiAlternatives(subject, message, from_email, [admin[1] for admin in settings.ADMINS])
    msg.attach_alternative(message_html, "text/html")
    msg.send(fail_silently=True)
