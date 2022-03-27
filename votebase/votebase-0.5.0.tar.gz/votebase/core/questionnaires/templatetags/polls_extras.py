from django import template

register = template.Library()


@register.filter()
def user_already_voted(survey, user):
    return survey.user_already_voted(user)
