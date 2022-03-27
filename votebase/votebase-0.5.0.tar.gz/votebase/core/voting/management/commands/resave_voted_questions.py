from progressbar import ProgressBar
from django.core.management.base import BaseCommand
from votebase.core.voting.models import VotedQuestion


class Command(BaseCommand):
    def handle(self, *args, **options):
        survey_slug = args[0]

        voted_questions = VotedQuestion.objects.filter(question__survey__slug=survey_slug, quiz_result=None)
        progress = ProgressBar(voted_questions.count()).start()

        counter = 0

        for voted_question in voted_questions:
            voted_question.save()

            # UPDATE COUNTER
            counter += 1
            progress.update(counter)

        progress.finish()
