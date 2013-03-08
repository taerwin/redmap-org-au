from redmap.common.tags import get_redmap_tag

def redmap_tag(request):

    return {
        'redmap_tag': get_redmap_tag,
    }
