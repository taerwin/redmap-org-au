from django.contrib.sites.models import Site
from django import forms
from django.forms import ModelForm, SplitDateTimeWidget
from django.forms.models import inlineformset_factory
from django.utils.html import strip_tags
from ckeditor.widgets import CKEditorWidget
from datetime import datetime

from tagging.models import Tag
from zinnia.models import Category, Entry
from zinnia.managers import DRAFT, HIDDEN, PUBLISHED
from news.models import NewsImage
from nestedformsets.forms import NestedModelForm


class TaggedModelBaseForm(ModelForm):
    """
    This can be used to replace the string tagging widget with a
    ModelMultipleChoiceField.
    """

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(TaggedModelBaseForm, self).__init__(*args, **kwargs)
        self.fields['tags'].initial = Tag.objects.get_for_object(self.instance)

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        return ",".join([t.name for t in tags])

    def save(self, *args, **kwargs):
        instance = super(TaggedModelBaseForm, self).save(*args, **kwargs)
        instance.tags = self.cleaned_data['tags']
        return instance


class NewsImageForm(ModelForm):
    class Meta:
        model = NewsImage
        fields = ('image', 'caption', 'position')
        widgets = {
            'image': forms.FileInput,
            'caption': forms.Textarea(attrs={'rows': 4}),
            'position': forms.TextInput(attrs={'class': 'span1'}),
        }


NewsImageFormset = inlineformset_factory(Entry, NewsImage, form=NewsImageForm,
                                         extra=1, fields=('image', 'caption', 'position'))


class EntryAddForm(NestedModelForm, TaggedModelBaseForm):

    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'span4'}))
    slug = forms.CharField(widget=forms.TextInput(attrs={'class': 'span4'}))

    def __init__(self, user=None, *args, **kwargs):
        super(EntryAddForm, self).__init__(*args, **kwargs)
        self._user = user
        self._status = self.instance.status
        self.fields['start_publication'].label = 'Publish on'

    def save(self, commit=True):
        instance = super(EntryAddForm, self).save(False)

        if (self._status != instance.status) and (instance.status == PUBLISHED):
            instance.start_publication = datetime.now()

        if len(instance.excerpt) == 0:
            excerpt = strip_tags(instance.content).split()
            instance.excerpt = ' '.join(excerpt[:25]) + '...'

        if commit:
            instance.save()
            for form in self.formsets.get('gallery').forms:
                form.instance.entry = instance
            self.save_formsets()

        instance.authors.add(self._user)
        instance.sites.add(Site.objects.get_current())
        category, created = Category.objects.get_or_create(slug='news')
        instance.categories.add(category)

        return instance

    class Meta:
        model = Entry
        fields = (
            'title',
            'slug',
            'author',
            'image',
            'image_caption',
            'content',
            'excerpt',
            'status',
            'template',
            'start_publication',
        )
        widgets = {
            'content': CKEditorWidget(),
            'excerpt': CKEditorWidget(config_name='basic_toolbar'),
            'start_publication': SplitDateTimeWidget(),
        }

    class NestedMeta:
        formsets = {
            'gallery': NewsImageFormset,
        }


class ArticleAddForm(NestedModelForm, TaggedModelBaseForm):

    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'span4'}))
    slug = forms.CharField(widget=forms.TextInput(attrs={'class': 'span4'}))

    def __init__(self, user=None, *args, **kwargs):
        super(ArticleAddForm, self).__init__(*args, **kwargs)
        self._user = user
        self._status = self.instance.status
        self.fields['start_publication'].label = 'Publish on'

    def save(self, commit=True):
        instance = super(ArticleAddForm, self).save(False)

        if (self._status != instance.status) and (instance.status == PUBLISHED):
            instance.start_publication = datetime.now()

        if len(instance.excerpt) == 0:
            excerpt = strip_tags(instance.content).split()
            instance.excerpt = ' '.join(excerpt[:25]) + '...'

        if commit:
            instance.save()
            for form in self.formsets.get('gallery').forms:
                form.instance.entry = instance
            self.save_formsets()

        instance.authors.add(self._user)
        instance.sites.add(Site.objects.get_current())
        category, created = Category.objects.get_or_create(slug='articles')
        instance.categories.add(category)

        return instance

    content = forms.CharField(
        widget=CKEditorWidget(config_name='default'))

    class Meta:
        model = Entry
        fields = (
            'title',
            'slug',
            'author',
            'image',
            'image_caption',
            'content',
            'excerpt',
            'status',
            'template',
            'start_publication',
        )
        widgets = {
            'excerpt': CKEditorWidget(config_name='default'),
            'content': CKEditorWidget(config_name='basic_toolbar'),
            'start_publication': SplitDateTimeWidget(),
        }

    class NestedMeta:
        formsets = {
            'gallery': NewsImageFormset,
        }
