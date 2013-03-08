from django import forms
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.forms.widgets import RadioFieldRenderer
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from redmapdb.models import FBGroup, Sighting, Species, Activity, Accuracy, \
    Person, Sex, SpeciesCategory, Count, Region
from frontend.models import Faq, Sponsor, SponsorCategory
from ckeditor.widgets import CKEditorWidget
import datetime
import uuid


class AddStep1(ModelForm):

    PHOTO_PERMISSION_REQUIRED = u"Photo permissions are required"
    OTHER_SPECIES_PHOTO_REQUIRED = \
        u"A photo is required for other species sightings"
    SPECIES_REQUIRED = u"Please specify the species you are reporting"

    photo_permission = forms.BooleanField(
        label="I own all rights to this photo, and give permission for "
              "Redmap Australia to display it on their site",
        required=False)
    other_species = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Other species', 'class': 'span3'}))

    progress_uuid = forms.CharField(max_length=36, widget=forms.widgets.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(AddStep1, self).__init__(*args, **kwargs)
        self.fields["species"].queryset = Species.objects.get_redmap()
        self.fields["species"].required = False
        self.fields["species"].widget.attrs[
            'data-placeholder'] = 'Species or Common name'
        self.fields["species"].widget.attrs['class'] = 'span5'
        self.fields["other_species"].required = False
        self.fields["photo_caption"].widget.attrs['rows'] = 5
        self.fields["photo_caption"].widget.attrs['cols'] = 30
        self.fields["photo_caption"].widget.attrs[
            'class'] = "input-block-level"

        try:
            request = kwargs.get('initial', None).get('request', None)
        except AttributeError:
            request = None

        if request:
            """
            Purpose: For basic safety the client web browser uploading an image needs an id to track
            their upload progress, but they need this before they start uploading and we don't want to
            allow them to set the id they follow from the client side as that gives to much client access
            to the server

            Solution: For each page load of the first step of the wizard form, we create a new uuid and add
            it to a list of uuids available for the current user session, django will handle the destruction
            of the session data, and when we receive an upload image request, we will check the post data
            contains a valid uuid for the user's session, and only then will ajax be able to track the valid
            uuid to gain the progress of the uploading image
            """

            new_uuid = str(uuid.uuid4())

            self.fields['progress_uuid'].initial = new_uuid

            if 'progress_uuids' in request.session:
                request.session['progress_uuids'].append(new_uuid)
            else:
                request.session['progress_uuids'] = [new_uuid]

    def clean(self):
        cleaned_data = self.cleaned_data

        species = cleaned_data.get('species')
        other_species = cleaned_data.get('other_species')
        if not species and not other_species:
            self._errors["species"] = self.error_class([self.SPECIES_REQUIRED])

        photo_url = cleaned_data.get('photo_url')

        if photo_url:
            if not cleaned_data.get('photo_permission'):
                self._errors["photo_permission"] = self.error_class(
                    [self.PHOTO_PERMISSION_REQUIRED])
        elif other_species:
            self._errors["photo_url"] = self.error_class(
                [self.OTHER_SPECIES_PHOTO_REQUIRED])

        return cleaned_data

    class Meta:
        model = Sighting
        fields = ['photo_url', 'photo_caption', 'species', 'other_species']
        widgets = {'photo_caption': forms.widgets.Textarea()}


class BootstrapRadioRenderer(RadioFieldRenderer):

    def render(self):
        return(mark_safe(u''.join([u'<label class="radio">%s%s</label>'
               % (force_unicode(w.tag()), force_unicode(w.choice_label))
            for w in self])))


class AddStep2(ModelForm):

    def __init__(self, *args, **kwargs):
        super(AddStep2, self).__init__(*args, **kwargs)
        self.fields["activity"].empty_label = None
        self.fields["activity"].widget.renderer = BootstrapRadioRenderer
        self.fields["accuracy"].empty_label = None
        self.fields["activity"].initial = Accuracy.objects.get(code='10000').pk

        self.fields['time'].empty_label = 'Not sure'

    def clean_sighting_date(self):
        sighting_date = self.cleaned_data.get('sighting_date')
        if sighting_date > datetime.datetime.now():
            raise forms.ValidationError('Cannot be in the future')
        return sighting_date

    class Meta:
        model = Sighting
        fields = ['latitude', 'longitude', 'accuracy', 'time',
                  'activity', 'sighting_date']
        widgets = {
            'latitude': forms.TextInput(attrs={'class': 'input-small', }),
            'longitude': forms.TextInput(attrs={'class': 'input-small', }),
            'sighting_date': forms.TextInput(
                attrs={'class': 'input-small', 'placeholder': 'DD-MM-YYYY'}),
            'time': forms.Select(attrs={'class': 'input-medium', }),
        }


class AddStep3(ModelForm):
    sex = forms.ModelChoiceField(Sex.objects.all(), empty_label=None)

    notes = forms.CharField(widget=forms.widgets.Textarea(
        attrs={'class': 'input-block-level', 'rows': 5, 'cols': 20}),
        required=False)

    class Meta:
        model = Sighting
        fields = ['count', 'sex', 'size', 'size_method', 'weight',
                  'weight_method', 'depth', 'water_temperature', 'habitat',
                  'notes']
        widgets = {
            'weight_method': forms.Select(attrs={'class': 'input-small'}),
            'size_method': forms.Select(attrs={'class': 'input-small'}),
            'size': forms.TextInput(attrs={'class': 'input-small'}),
            'weight': forms.TextInput(attrs={'class': 'input-small'}),
            'depth': forms.TextInput(attrs={'class': 'input-small'}),
            'water_temperature': forms.TextInput(
                attrs={'class': 'input-small'})}


class AddStep4(forms.Form):
    pass


class AddSponsorForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(AddSponsorForm, self).__init__(*args, **kwargs)
        self.fields['image_url'].help_text = \
            "Sponsor banner images should be 300x100 pixels"
        self.fields['website_url'].help_text = "http://<b>{{ website }}</b>"

    class Meta:
        model = Sponsor


class AddFaqForm(ModelForm):

    class Meta:
        model = Faq
        widgets = {
            'content': CKEditorWidget(),
        }


class AddSponsorCategoryForm(ModelForm):

    class Meta:
        model = SponsorCategory


class FBGroupForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(FBGroupForm, self).__init__(*args, **kwargs)
        self.fields['description'].label = 'Group name'

    class Meta:
        model = FBGroup
        fields = ['id', 'description', 'image_url']


class FilterSpeciesForm(forms.Form):
    species = forms.ModelChoiceField(
        Species.objects.get_redmap(),
        widget=forms.widgets.Select(attrs={
            'data-placeholder': 'select a species',
            'class': 'species-filter'}),
        empty_label='All species')

    def __init__(self, species, *args, **kwargs):
        self.species = species
        super(FilterSpeciesForm, self).__init__(*args, **kwargs)
        self.fields['species'].queryset =\
            Species.objects.get_redmap().filter(pk__in=self.species)


class JumpForm(forms.Form):

    jump_field_name = 'jump'
    empty_label = 'Jump'

    def __init__(self, *args, **kwargs):
        super(JumpForm, self).__init__(*args, **kwargs)

        self.fields[self.jump_field_name] = forms.ChoiceField(
            choices=self.make_choices())

    def make_choices(self):
        return [('', self.empty_label)]


class SpeciesJumpForm(JumpForm):

    jump_field_name = 'species'
    empty_label = 'Jump to species'

    def __init__(self, region=None, *args, **kwargs):
        self.region = region
        super(SpeciesJumpForm, self).__init__(*args, **kwargs)

    def make_choices(self):
        empty = super(SpeciesJumpForm, self).make_choices()
        species = Species.objects.get_redmap()
        return empty + [(self.make_url(s), s) for s in species]

    def make_url(self, species):
        category = species.speciesincategory_set.all()[0].species_category
        if self.region:
            return reverse('species_detail_by_region', kwargs={
                'region_slug': self.region.slug,
                'pk': species.pk,
                'category': category.pk})
        else:
            return reverse('species_detail', kwargs={
                'pk': species.pk,
                'category': category.pk})


class RegionJumpForm(JumpForm):

    jump_field_name = 'region'
    empty_label = 'Jump to a region'

    def make_choices(self):
        empty = super(RegionJumpForm, self).make_choices()
        regions = Region.objects.all()
        return empty + [(self.make_url(r), r) for r in regions]

    def make_url(self, region):
        return reverse('species_category_list_by_region', kwargs={
            'region_slug': region.slug})


class RegionCategoryJumpForm(RegionJumpForm):

    def __init__(self, category, *args, **kwargs):
        self.category = category
        super(RegionCategoryJumpForm, self).__init__(*args, **kwargs)

    def make_url(self, region):
        return reverse('species_list_by_region', kwargs={
            'region_slug': region.slug,
            'category': self.category.pk})
