from django import template

register = template.Library()

@register.filter
def minutes_to_time(minutes):
    """Конвертирует минуты в формат ЧЧ:ММ"""
    if minutes is None:
        return "00:00"
    try:
        minutes = int(minutes)
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    except:
        return "00:00"

@register.filter
def sum_attribute(queryset, attribute):
    """Суммирует значения атрибута в queryset"""
    total = 0
    for item in queryset:
        value = getattr(item, attribute, 0)
        if value:
            try:
                total += float(value)
            except:
                pass
    return round(total, 1)