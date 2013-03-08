from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import stringfilter
from django.template import Context, Template

register = template.Library()


@register.assignment_tag(takes_context=True)
def page_url(context, page):
    """
    Resolve the correct base url based on context.  Necessary because resource
    pages are reused within states.
    """
    if "region" in context:
        return page.get_public_url(context["region"])
    else:
        return page.get_public_url()


@register.simple_tag(takes_context=True)
def render_text(context, text):
    template_text = "{% load frontend_tags %}" + text
    return Template(template_text).render(context)


@register.filter
def truncatechars(value, length, suffix="..."):
    copy = str(value)
    if len(copy) < length:
        return copy
    else:
        return copy[:length] + suffix


@register.filter
def abbrstate(value):
        states = {
            'New South Wales': 'NSW',
            'Victoria': 'VIC',
            'Tasmania': 'TAS',
            'South Australia': 'SA',
            'Queensland': 'QLD',
            'Western Australia': 'WA',
            'Northern Territory': 'NT',
        }

        return states.get(value, value)


@register.assignment_tag(takes_context=True)
def active_region(context, a_region):
    """
    Work out if a region is active by looking at the "region" context variable.

    Note: this might break if used in this way (below) since it would since
    it would hide the template region variable.  Doing it wrong will always
    return True so it's hard to miss the bug.

    Good use:
        {% for nav_region in nav_regions %}
            {% active_region nav_region as is_active %}

    Bad use:
        {% for region in nav_regions %} {# BAD: overrides region variable #}
            {% active_region region as is_active %}
    """
    return a_region == context.get('region', None)


@register.assignment_tag(takes_context=True)
def overview_menu_active(context, request, regions):
    for region in regions:
        region_landing_page = reverse(
            'region_landing_page', kwargs={'region_slug': region.slug})
        if request.path == region_landing_page:
            return True

    return False


@register.filter
def startswith(value, lookup):
    return value.startswith(lookup)


@register.filter
@stringfilter
def indefinite_article(value, words="an,a,"):
    words = words.split(',')

    if not value:
        return words[2]

    vowels = 'aeiou'
    first = value[0].lower()

    return words[0 if first in vowels else 1]
