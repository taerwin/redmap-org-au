from django import template
from django.http import QueryDict

register = template.Library()


@register.inclusion_tag("../templates/_navtabs.html", takes_context=True)
def navtabs(context, active, user):
    context['active'] = active
    return context


@register.inclusion_tag("../templates/_panel_sightings.html", takes_context=True)
def panel_sightings(context, active):
    context['active'] = active
    return context


@register.inclusion_tag("../templates/_panel_expert.html")
def panel_expert(active):
    return {
        'active': active
    }


@register.inclusion_tag("../templates/_panel_content.html")
def panel_content(active):
    return {
        'active': active
    }


@register.inclusion_tag("../templates/_panel_administration.html", takes_context=True)
def panel_administration(context, active, user):
    context['active'] = active
    return context


@register.simple_tag(takes_context=True)
def order_by(context, order_name, ordering):
    def normalize(order):
        if order[0] == '-':
            return order[1:]
        return order

    def swap(order):
        if order[0] == '-':
            return order[1:]
        return '-' + order

    get = context['request'].GET.copy()
    current_ordering = get.get(order_name, None)

    if ordering == current_ordering:
        ordering = swap(ordering)

    get[order_name] = ordering

    return get.urlencode()
