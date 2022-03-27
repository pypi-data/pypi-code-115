from votebase.core.questionnaires.models import Survey


def published_active_surveys(request):
    return {
        'published_active_surveys': Survey.objects.published().active()
    }
