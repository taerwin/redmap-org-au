from django import template
from django.conf import settings
from django.db.models import Model
from redmap.common.tags import get_redmap_tag
from redmapdb.models import Person, Region
from tagging.models import Tag, TaggedItem
from zinnia.models import Entry
from zinnia.managers import PUBLISHED

register = template.Library()


def only_tags(maybe_tag):
    """ Convert the passed in thing to an iterable of tags, using the following
        rules:

        * Tags are used as-is
        * Model instances are used in a `Tag.objects.get_for_object(...)` call
        * Strings are considered to be a comma-seperated list of tag names
        * Iterables are iterated over, using the above rules to extract tags
    """

    if isinstance(maybe_tag, Tag):
        yield maybe_tag

    elif isinstance(maybe_tag, Model):
        obj = maybe_tag
        tags = list(Tag.objects.get_for_object(obj))
        for tag in tags:
            yield tag

    elif isinstance(maybe_tag, basestring):
        tag_string = maybe_tag
        tag_list = filter(bool, tag_string.split(','))
        for tag_name in tag_list:
            try:
                yield Tag.objects.get(name=tag_name)
            except Tag.DoesNotExist:
                pass
    else:
        try:
            tag_list = iter(maybe_tag)
        except TypeError:
            raise StopIteration()

        for maybe_tag in tag_list:
            for tag in only_tags(maybe_tag):
                yield tag


@register.assignment_tag
def articles_with_tags(*args):
    """
    Get all articles (Entries in the 'articles' category) that are tagged with
    all of the tags passed in

    Every argument passed to this template tag is converted to one or more
    tags using the `only_tags` function
    """
    tags = set(only_tags(args))
    articles = Entry.published.filter(categories__slug="articles")

    tagged_entries = TaggedItem.objects.get_by_model(articles,
                                                     list(tags)).filter(status=PUBLISHED)

    return tagged_entries


@register.assignment_tag
def news_with_tags(*args):
    """
    Get all news items (Entries in the 'news' category) that are tagged with
    all of the tags passed in

    Every argument passed to this template tag is converted to one or more
    tags using the `only_tags` function
    """
    tags = set(only_tags(args))
    articles = Entry.published.filter(categories__slug="news")

    tagged_entries = TaggedItem.objects.get_intersection_by_model(
        articles, list(tags))

    return tagged_entries


@register.assignment_tag
def people_with_tags(*args):
    """
    Get all news items (Entries in the 'news' category) that are tagged with
    all of the tags passed in

    Every argument passed to this template tag is converted to one or more
    tags using the `only_tags` function
    """
    tags = set(only_tags(args))
    people = Person.objects.all()

    tagged_people = TaggedItem.objects.get_by_model(people, list(tags))

    return tagged_people


@register.filter
def region_tags(tags):
    passed_tags = set(only_tags(tags))
    region_tags = set(Tag.objects.usage_for_model(Region))

    matching_tags = passed_tags & region_tags

    print "passed_tags:", passed_tags
    print "All region tags:", region_tags
    print "Found matching region tags:", matching_tags

    return matching_tags
