from django import template

from ..money_words import bdt_amount_in_words

register = template.Library()


@register.filter
def bdt_in_words(value):
    if value is None:
        return ''
    return bdt_amount_in_words(value)
