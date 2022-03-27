def check_voting_prerequisites(request):
    return None


def get_questions(survey):
    return survey.question_set.all()
