from django import template
import datetime
from datetime import date
register = template.Library()

@register.simple_tag
def yesterday():
    yest= date.today() + datetime.timedelta(days=1)
    return yest

@register.simple_tag
def past7():
    yest = date.today() - datetime.timedelta(days=7)
    return yest

@register.simple_tag
def month():
    yest = date.today() - datetime.timedelta(days=30)
    return yest