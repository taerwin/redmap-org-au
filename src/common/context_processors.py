from redmap.common.tags import get_redmap_tag

<< << << < HEAD

== == == =
>>>>>> > cf53e7a54e78e374d5deb541eedcf0c071f32c50


def redmap_tag(request):

    return {
        'redmap_tag': get_redmap_tag,
    }
