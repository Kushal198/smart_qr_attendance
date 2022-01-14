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

@register.simple_tag
def checkAttendance(day, object_list, class_days):
    test = [item for item in object_list if item['day'] == day]
    if len(test)>0 and test[0]['status'] == True and test[0]['day'] in class_days:
        return 'P'
    elif len(test) == 0 and day in class_days:
        return 'A'
    elif len(test) == 0 and day not in class_days:
        return '-'
    else:
        return 'A'
