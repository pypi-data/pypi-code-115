import roman

from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext as _


def error_email_confirmed(request):
    messages.error(request, _('You have not confirmed your email \
    address yet. If you did not receive confirmation, please click \
    <a href="%(url)s">here</a>.' % {
        'url': reverse('accounts_resend_confirmation'),
    }))


def sorted_by_roman(roman_categories):
    try:
        # create list of categories with arabic numbers
        arabic_categories = []
        for roman_category in roman_categories:
            roman_number = roman_category.split('.')[0]
            arabic_number = roman.fromRoman(roman_number)
            arabic_category = roman_category.replace('%s.' % roman_number, '%d.' % arabic_number)
            arabic_categories.append(arabic_category)

        # sort arabic categories
        arabic_categories = sorted(arabic_categories)

        # rebuild roman categories list
        for index, arabic_category in enumerate(arabic_categories):
            arabic_number = int(arabic_category.split('.')[0])
            roman_number = roman.toRoman(arabic_number)
            roman_category = arabic_category.replace('%d.' % arabic_number, '%s.' % roman_number)
            roman_categories[index] = roman_category
    except roman.InvalidRomanNumeralError:
        pass

    return roman_categories
