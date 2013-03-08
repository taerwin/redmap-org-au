from haystack.indexes import *
from haystack import site
from models import Species, Person


class SpeciesIndex(SearchIndex):

    common_name = CharField(model_attr='common_name', boost=1.125)
    text = CharField(document=True, use_template=True)

    def index_queryset(self):
        return Species.objects.get_redmap()



class PersonIndex(SearchIndex):

    name = CharField(boost=1.125)
    tag_list = CharField(model_attr='tag_list', boost=1.125)
    text = CharField(document=True, use_template=True)

    def prepare_name(self, obj):
        if obj.user:
            return "%s <%s>" % (obj.user.get_full_name(), obj.user.email)

    def index_queryset(self):
        return Person.objects.filter(user__isnull=False)


site.register(Person, PersonIndex)

site.register(Species, SpeciesIndex)
