
from django.db.models import Min


def distinct_by_annotation(queryset, field="id"):
    """
    We have problems with distinct clashing with the added field
    ROW_NUMBER used for ordering by PyODBC.  To avoid duplicates
    we're using an annotation to group by id.

    Note: This won't carry through to chained queries (I think)
    but the model is sound.
    """
    return queryset.annotate(Min(field))

