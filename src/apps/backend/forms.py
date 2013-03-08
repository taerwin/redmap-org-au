from django import forms
from django.conf import settings
from django.forms import ModelForm, Form
from django.contrib.auth.models import User, Group
from redmapdb.models import Sighting, SpeciesAllocation, Region, Species,\
    Organisation, Person, AdministratorAllocation
from backend.models import ValidationMessageTemplate, SightingValidationRule,\
    SightingValidationCondition, ConditionSection
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from django.forms.models import inlineformset_factory
from django_filters import FilterSet
from django_filters.filters import ModelChoiceFilter, ChoiceFilter
from tagging.models import Tag
from tagging.utils import parse_tag_input
from models import RuleConditionTest
from common.sql import distinct_by_annotation


class VerifyStep(ModelForm):

    species = forms.ModelChoiceField(
        queryset=Species.objects.get_redmap(),
        widget=forms.widgets.Select(attrs={
            'data-placeholder': 'Species or Common name',
            'class': 'input-xlarge'
        }),
        empty_label="Other species", required=False)

    sighting_date = forms.DateField(required=True,
                                    widget=forms.DateInput(attrs={'class': 'input-small'}))

    photo_caption = forms.CharField(required=False,
                                    widget=forms.Textarea(attrs={
                                                          'rows': '3', 'class': 'input-block-level'}))

    def __init__(self, *args, **kwargs):
        super(VerifyStep, self).__init__(*args, **kwargs)

        for section in ConditionSection.objects.all():

            if not section.conditions.exists():
                continue

            if section.is_radiogroup:

                self.fields[section.name] = forms.ModelChoiceField(
                    queryset=section.conditions.all(),
                    widget=RadioSelect,
                    required=True,
                    label=section.radiogroup_label,
                    empty_label=None,
                )

            else:

                self.fields[section.name] = forms.ModelMultipleChoiceField(
                    queryset=section.conditions.all(),
                    widget=CheckboxSelectMultiple,
                    label='',
                    required=False,
                )

        sighting = self.instance
        if not self.instance.photo_url:
            photo_radiogroup = self.fields[settings.PHOTO_RADIOGROUP_SECTION]
            photo_radiogroup.required = False

        self.fields['time'].empty_label = 'Not sure'

    def clean(self):
        cleaned_data = super(VerifyStep, self).clean()

        species = cleaned_data.get('species')
        other_species = cleaned_data.get('other_species')

        if species and other_species:
            msg = u'You may not select more than one species'
            self._errors['species'] = self.error_class([msg])
            self._errors['other_species'] = self.error_class([msg])
        elif not species and not other_species:
            msg = u'You must select a species'
            self._errors['species'] = self.error_class([msg])
            self._errors['other_species'] = self.error_class([msg])

        conditions = []

        for section in ConditionSection.objects.all():

            if section.name in cleaned_data:
                section_conditions = cleaned_data[section.name]

                if section.is_radiogroup:
                    conditions.append(cleaned_data[section.name])
                else:
                    conditions += cleaned_data[section.name]

        cleaned_data['conditions'] = conditions

        return cleaned_data

    class Meta:
        model = Sighting
        fields = ['species', 'other_species', 'sex', 'size_method', 'size', 'weight', 'count',
                  'sighting_date', 'time', 'latitude', 'longitude', 'accuracy',
                  'activity', 'notes', 'photo_caption']


class VerifyStep3(Form):

    assessment = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'class': 'span6', 'rows': '12'}))
    is_displayed_on_site = forms.BooleanField(required=False)
    is_published = forms.BooleanField(required=False)
    template = forms.ModelChoiceField(
        queryset=ValidationMessageTemplate.objects.all(), empty_label=None)
    message = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'class': 'span6', 'rows': '12'}))

    def __init__(self, is_success, template_id, assessment, *args, **kwargs):
        super(VerifyStep3, self).__init__(*args, **kwargs)

        matching_rules =\
            SightingValidationRule.objects.filter(valid_sighting=is_success)
        all_templates = distinct_by_annotation(
            ValidationMessageTemplate.objects.filter(
                sightingvalidationrule__in=matching_rules))
        matching_template = all_templates.get(pk=template_id)

        self.fields['template'].queryset = all_templates
        self.fields['template'].initial = template_id
        self.fields['assessment'].initial = assessment
        self.fields['message'].initial = matching_template.template
        self.fields['is_displayed_on_site'].initial = is_success
        self.fields['is_published'].initial = is_success


class AddSpeciesAllocation(ModelForm):

    def __init__(self, *args, **kwargs):
        super(AddSpeciesAllocation, self).__init__(*args, **kwargs)

        self.fields['species'].queryset = Species.objects.get_redmap()
        self.fields['region'].empty_label = "All"
        self.fields['region'].required = False

        scientists = User.objects.filter(groups__name="Scientists").\
            filter(is_active=True).order_by('username')

        choices = {}
        for user in scientists:
            choices.update({user.id: user.profile.display_name})

        choices = choices.items()

        self.fields.insert(1, 'person', forms.ChoiceField(choices=choices))

    def clean(self):

        cleaned_data = self.cleaned_data
        person = User.objects.get(pk=cleaned_data.get('person'))
        cleaned_data.update({'person': person})

        return cleaned_data

    class Meta:
        model = SpeciesAllocation


class AddScientistForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(AddScientistForm, self).__init__(*args, **kwargs)

        scientists = User.objects.exclude(groups__name="Scientists").\
            filter(is_active=True).order_by('username')

        choices = {}
        for user in scientists:
            choices.update({user.id: user.profile.display_name})

        choices = choices.items()

        self.fields.insert(0, 'username', forms.ChoiceField(choices=choices))

    organisation = forms.ModelChoiceField(queryset=Organisation.objects.all())


class RegionalAdministratorAddForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(RegionalAdministratorAddForm, self).__init__(*args, **kwargs)

        admins = User.objects.exclude(groups__name="Regional Administrators").\
            filter(is_active=True).order_by('username')

        choices = {}
        for user in admins:
            choices.update({user.id: user.profile.display_name})

        choices = choices.items()

        self.fields.insert(0, 'username', forms.ChoiceField(choices=choices))

    organisation = forms.ModelChoiceField(queryset=Organisation.objects.all())


class AdministratorAllocationForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(AdministratorAllocationForm, self).__init__(*args, **kwargs)

        admins = User.objects.filter(groups__name="Regional Administrators")

        choices = {}
        for user in admins:
            choices.update({user.id: user.profile.display_name})

        choices = choices.items()

        self.fields.insert(1, 'person', forms.ChoiceField(choices=choices))

    def clean(self):

        cleaned_data = self.cleaned_data
        person = User.objects.get(pk=cleaned_data.get('person'))
        cleaned_data.update({'person': person})

        return cleaned_data

    class Meta:
        model = AdministratorAllocation


class RuleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(RuleForm, self).__init__(*args, **kwargs)

    class Meta:
        model = SightingValidationRule
        widgets = {
            'valid_photo': RadioSelect,
            'valid_sighting': RadioSelect
        }


class RuleConditionTestForm(ModelForm):
    condition = forms.ModelChoiceField(
        queryset=SightingValidationCondition.objects.all(),
        widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(RuleConditionTestForm, self).__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields['test'].label = self.instance.condition.name
        elif self.initial:
            self.fields['test'].label = self.initial['condition'].name

    class Meta:
        model = RuleConditionTest
        widgets = {
            'test': RadioSelect,
        }

        fields = [
            'test',
            'condition',
            'rule',
        ]


RuleConditionTestFormSet = inlineformset_factory(SightingValidationRule,
                                                 RuleConditionTest,
                                                 form=RuleConditionTestForm,
                                                 can_delete=False,
                                                 extra=0
                                                 )


class AddValidationRuleForm(ModelForm):

    num_rules = SightingValidationRule.objects.count()
    choices = {}
    i = 0
    while i <= num_rules:
        choices.update({i: i})
        i = i + 1
    choices = choices.items()

    rank = forms.ChoiceField(choices=choices)

    def __init__(self, *args, **kwargs):
        super(AddValidationRuleForm, self).__init__(*args, **kwargs)

        self.fields['name'].label = "<strong>Rule name</strong>"
        self.fields['rank'].label = "<strong>Rule priority</strong><br><i>\
            Note: Rules are processed in order with the first matching rule\
            activate.</i>"
        self.fields['valid_sighting'].label =\
            "<strong>Rule conditions</strong><br>Sighting is"
        self.fields['valid_photo'].label = "Photo is"
        self.fields['sighting_validation_condition'].label =\
            "Additional rule conditions"
        self.fields['validation_message_template'].label =\
            "<strong>Rule actions</strong><br>Activate this template"
        self.fields['sighting_validation_condition'].help_text = None
        self.fields.keyOrder = [
            'name', 'rank', 'valid_sighting', 'valid_photo',
            'sighting_validation_condition', 'validation_message_template'
        ]

    class Meta:
        model = SightingValidationRule
        widgets = {
            'valid_sighting': forms.widgets.RadioSelect(),
            'valid_photo': forms.widgets.RadioSelect(),
            'sighting_validation_condition': forms.widgets.CheckboxSelectMultiple()
        }


class AddEmailTemplateForm(ModelForm):

    class Meta:
        model = ValidationMessageTemplate
        widgets = {
            'template': forms.widgets.Textarea(attrs={'class': 'span5'}),
            'public_assessment': forms.widgets.Textarea(attrs={'class': 'span5'}),
        }


class UserAddForm(ModelForm):

    organisation = forms.ModelChoiceField(Organisation.objects.all())
    trust_level = forms.BooleanField(required=False)
    tag_list = forms.MultipleChoiceField(required=False, label="Tags")

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)

        tag_string = self.instance.profile.tag_list
        self.initial['tag_list'] = parse_tag_input(tag_string)

        self.fields['tag_list'].choices = Tag.objects.all(
        ).values_list('name', 'name')
        self.fields[
            'organisation'].initial = self.instance.profile.organisation
        self.fields['trust_level'].initial = self.instance.profile.trust_level
        self.fields['trust_level'].label = 'Trusted user'

    def save(self, *args, **kwargs):
        instance = super(UserAddForm, self).save(*args, **kwargs)

        profile = Person.objects.get(pk=instance.profile.pk)
        profile.organisation = self.cleaned_data.get('organisation')
        profile.trust_level = self.cleaned_data.get('trust_level')

        tags = self.cleaned_data['tag_list']
        if len(tags) > 0:
            profile.tag_list = ','.join(tag for tag in tags) + ','
        else:
            profile.tag_list = ''
        profile.save()

        return instance

    class Meta:
        model = User
        exclude = [
            'is_staff', 'is_superuser', 'last_login', 'date_joined',
            'groups', 'user_permissions', 'is_active', 'password'
        ]


class OrganisationAddForm(ModelForm):

    class Meta:
        model = Organisation


class EditSightingForm(ModelForm):

    species = forms.ModelChoiceField(
        queryset=Species.objects.get_redmap(),
        widget=forms.widgets.Select(attrs={
            'data-placeholder': 'Species or Common name',
            'class': 'input-xlarge'
        }),
        empty_label="Other species", required=False)

    def clean(self):
        cleaned_data = super(EditSightingForm, self).clean()

        species = cleaned_data.get('species')
        other_species = cleaned_data.get('other_species')

        if species and other_species:
            msg = u'You may not select more than one species'
            self._errors['species'] = self.error_class([msg])
            self._errors['other_species'] = self.error_class([msg])
        elif not species and not other_species:
            msg = u'You must select a species'
            self._errors['species'] = self.error_class([msg])
            self._errors['other_species'] = self.error_class([msg])

        return cleaned_data

    class Meta:
        model = Sighting
        fields = [
            'species', 'sex', 'weight', 'weight_method', 'size', 'size_method',
            'count', 'sighting_date', 'time', 'latitude', 'longitude',
            'accuracy', 'activity', 'notes', 'photo_caption', 'photo_url',
            'other_species'
        ]


class SightingReassignForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SightingReassignForm, self).__init__(*args, **kwargs)

        userlist = User.objects.filter(groups__name="Scientists")

        choices = {}
        for user in userlist:
            choices.update({user.id: user.profile.display_name})

        choices = choices.items()

        self.fields.insert(0, 'username', forms.ChoiceField(choices=choices))

    comment = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'class': 'input-xxlarge'}),
        label='Comment<br><small class="nobold lighter">Not displayed on\
            site</small>'
    )


class SightingSpamForm(forms.Form):

    comment = forms.CharField(
        widget=forms.widgets.Textarea(attrs={'class': 'input-xxlarge'}),
        label='Comment<br><small class="nobold lighter">Not displayed on\
            site</small>')


class ValidationConditionForm(ModelForm):

    choices = {'1': 1, '2': 2}
    step = forms.ChoiceField(choices=choices.items())

    class Meta:
        model = SightingValidationCondition


class NiceUserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.profile.display_name


class NiceUserFilter(ModelChoiceFilter):
    field_class = NiceUserChoiceField


class AssignedScientistFilter(NiceUserFilter):
    def filter(self, qs, value):
        if value is None:
            return qs

        return qs.get_sightings_for_user(value)


class OutOfRangeFilter(ChoiceFilter):
    CHOICES = (
        ('', '-- Range --'),
        ('in', 'In range'),
        ('out', 'Out of range'),
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('choices', self.CHOICES)
        super(OutOfRangeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        if not value:
            return qs
        value = {'out': True, 'in': False}[value]
        return qs.filter(**{self.name: value})


class SightingsListSearchForm(FilterSet):

    scientist = AssignedScientistFilter()
    is_out_of_range = OutOfRangeFilter()
    user = NiceUserFilter()

    class Meta:
        model = Sighting
        fields = ['user', 'species', 'region', 'is_out_of_range']
        order_by = [
            'logging_date', 'sighting_date', 'species__common_name',
            'user__username',
            '-logging_date', '-sighting_date', '-species__common_name',
            '-user__username',
        ]

    def __init__(self, data, *args, **kwargs):
        super(SightingsListSearchForm, self).__init__(data, *args, **kwargs)

        scientists = User.objects.filter(
            groups__name="Scientists", is_active=True)

        users = User.objects.order_by('first_name', 'username')

        self.filters['user'].extra.update({
            'queryset': users,
            'empty_label': '-- User --',
            'to_field_name': 'username'})
        self.filters['species'].extra.update({
            'queryset': Species.objects.all(),
            'empty_label': '-- Species --',
            'to_field_name': 'common_name'})
        self.filters['region'].extra.update({
            'queryset': Region.objects.all(),
            'empty_label': '-- Region --',
            'to_field_name': 'slug'})
        self.filters['scientist'].extra.update({
            'queryset': scientists,
            'empty_label': '-- Scientist --'})

        qs = self.qs

        self.filters['user'].extra['queryset'] = \
            distinct_by_annotation(users.filter(sightings__in=qs))

        self.filters['species'].extra['queryset'] = \
            distinct_by_annotation(Species.objects.filter(sightings__in=qs))

        self.filters['region'].extra['queryset'] = \
            distinct_by_annotation(Region.objects.filter(sighting__in=qs))

        self.filters['scientist'].extra['queryset'] = \
            distinct_by_annotation(scientists.filter(
                sightingtracking__sighting__in=qs))

        delattr(self, '_form')
        for filter_ in self.filters.values():
            delattr(filter_, '_field')
