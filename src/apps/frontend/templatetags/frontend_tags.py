'''
Created on 10/10/2012

@author: thomas
'''
import re
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django import template

from cms.models import Page
from redmapdb.models import Region, Person
from tagging.models import Tag
from redmap.common.tags import get_redmap_tag
from common.sql import distinct_by_annotation

register = template.Library()


TEMPLATE_PATHS = [
    "$prefix/$app/$model.html",
    "$prefix.html"]


def template_list_generator(prefix, instance):
    "Helper for resolving the best template for an instance"
    vars = dict(
        prefix=prefix, app=instance._meta.app_label,
        model=instance._meta.module_name)
    return [string.Template(t).substitute(**vars) for t in TEMPLATE_PATHS]


@register.simple_tag()
def render_link(object):
    "Generates a link for an instance"
    ts = template_list_generator("frontend/render/link", object)
    t = template.loader.select_template(ts)
    return t.render(Context({'object': object}))


@register.simple_tag()
def render_feature(object):
    "Generates a small feature for an object"
    ts = template_list_generator("frontend/render/feature", object)
    t = template.loader.select_template(ts)
    return t.render(Context({'object': object}))


@register.assignment_tag()
def get_scientist(id):
    """
    Get a scientist based on their profile id

    :model:`redmapdb.Person` id.

    """
    try:
        return Person.objects.get(pk=id)
    except Person.DoesNotExist:
        return ""


@register.filter
def as_bootstrap_field(field):
    template = get_template("frontend/tags/field.html")
    c = Context({"field": field})
    return template.render(c)


@register.filter
def as_bootstrap_checkbox(field):
    template = get_template("frontend/tags/checkbox.html")
    c = Context({"field": field})
    return template.render(c)


@register.filter
def get_range(value):
    return range(value)


@register.filter
def get_key(dictionary, key):
    return dictionary[key]


@register.filter
def is_scientist(user):
    return user.get_profile().is_scientist


@register.filter
def is_regional_admin(user):
    return user.get_profile().is_regional_admin


@register.filter
def is_site_admin(user):
    return user.get_profile().is_site_admin


@register.filter
def is_panel(url):

    is_this_a_panel_url = re.match(r'^/panel/', url)

    if is_this_a_panel_url:
        return True
    else:
        return False


@register.filter
def show_regional_pages(tag_list, region_slug):

    region = Region.objects.get(pk=region_slug)
    region_tag = Tag.objects.get_for_object(region)[0]

    if re.match(r'%s|%s' % (get_redmap_tag(), region_tag), tag_list):
        return True
    else:
        return False


@register.filter
def show_global_pages(tag_list):

    if re.match(r'%s' % get_redmap_tag(), tag_list):
        return True
    else:
        return False


@register.filter
def to_javascript_date(date):
    return mark_safe('new Date("{0}")'.format(date.isoformat()))


@register.assignment_tag(takes_context=True)
def get_scientists(context, for_region=None):

    if for_region:
        scientist_users = distinct_by_annotation(
            User.objects.filter(
                person__organisation__jurisdiction__region=for_region))

    else:
        scientist_users = User.objects.order_by('last_name').filter(
            groups__name="Scientists", is_active=True)

    return Person.objects.filter(
        organisation__isnull=False, user__in=scientist_users)
