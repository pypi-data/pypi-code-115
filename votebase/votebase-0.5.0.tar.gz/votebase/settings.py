from django.conf import settings

QUESTIONS_PICKER = getattr(settings, 'VOTEBASE_QUESTIONS_PICKER', 'votebase.helpers.get_questions')
VOTING_PREREQUISITES = getattr(settings, 'VOTEBASE_VOTING_PREREQUISITES', 'votebase.helpers.check_voting_prerequisites')
FINISH_URL_HANDLER = getattr(settings, 'VOTEBASE_FINISH_URL_HANDLER', None)
