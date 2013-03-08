from haystack.indexes import *
from haystack import site
from zinnia.models import Entry


class EntryIndex(SearchIndex):

    title = CharField(model_attr='title', boost=1.125)
    slug = CharField(model_attr='slug', boost=1.125)
    tags = CharField(model_attr='tags', boost=1.125)
    text = CharField(document=True, use_template=True)

    def index_queryset(self):
        return Entry.published.all()


site.register(Entry, EntryIndex)
