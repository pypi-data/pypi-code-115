from django import template

register = template.Library()


@register.simple_tag()
def survey_voters(survey, user=None):
    voters = survey.voter_set.all()
    return voters.filter(user=user) if user else voters
