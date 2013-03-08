from django import forms
from django.forms.widgets import RadioFieldRenderer
from django.contrib.auth.models import User
from django.forms import ModelForm
from redmapdb.models import Person
from django.utils.translation import ugettext_lazy as _

from redmapdb.models import Region


attrs_dict = {'class': 'required'}


class Person(ModelForm):

    first_name = forms.CharField(label='First name', max_length=255)
    last_name = forms.CharField(label='Last name', max_length=255)
    email = forms.CharField(max_length=255)

    is_available_formfield = forms.BooleanField(
        label='I am available',
        required=False,
        initial=False,
        help_text="By unchecking this box you will no longer be assigned new\
                    sightings")

    about_me = forms.CharField(
        widget=forms.widgets.Textarea(
            attrs={
                'class': 'span6',
                'rows': 5,
                'cols': 20
            }
        )
    )

    fieldsets = {
        'user_fields': ('first_name', 'last_name', 'email', 'about_me'),
        'misc_fields': ('image', 'occupation_interest', 'is_available_formfield'),
        'address_fields': ('postcode'),
        'phone_fields': ('phone', 'mobile'),
        'region_fields': ('region',),
    }

    def __init__(self, *args, **kwargs):
        super(Person, self).__init__(*args, **kwargs)

        self.fields['occupation_interest'].label = "Occupation / Interest"

        if not self.data:

            if bool(self.instance.is_available):
                self.fields['is_available_formfield'].initial =\
                    int(self.instance.is_available)

            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

        if not self.instance.user.get_profile().is_scientist and\
                not self.instance.user.get_profile().is_regional_admin:

            del self.fields['is_available_formfield']
            self.fieldsets['misc_fields'] = self.fieldsets['misc_fields'][:-1]

        self.unrequire_fields()

    def unrequire_fields(self):

        fields = ['mobile',
                  'phone',
                  'postcode',
                  'about_me',
                  ]
        for field in fields:
            self.fields[field].required = False

    def save(self, commit=True):
        instance = super(Person, self).save(commit=False)

        if 'is_available_formfield' in self.cleaned_data:
            instance.is_available =\
                int(self.cleaned_data.get('is_available_formfield', None))

        if commit:
            instance.save()

            self.instance.user.first_name = self.cleaned_data.get('first_name')
            self.instance.user.last_name = self.cleaned_data.get('last_name')
            self.instance.user.email = self.cleaned_data.get('email')
            self.instance.user.save()

        return instance

    class Meta:
        model = Person
        fields = ['phone', 'mobile', 'postcode', 'image', 'about_me',
                  'occupation_interest', 'region']


class RegionRadioFieldRenderer(RadioFieldRenderer):
    def __init__(self, name, value, attrs, choices):
        """Move the 'other' option to be the last"""
        other = choices[0]
        choices.remove(other)
        choices.append(other)
        super(RegionRadioFieldRenderer, self).__init__(name, value,
                                                       attrs, choices)


class RegionRadioSelect(forms.RadioSelect):
    renderer = RegionRadioFieldRenderer


class RedmapRegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("E-mail"))
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    region = forms.ModelChoiceField(
        Region.objects.all(), required=False, empty_label="Other region",
        widget=RegionRadioSelect)
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password"))
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password (again)"))

    def __init__(self, *args, **kwargs):
        super(RedmapRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all()

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        existing = User.objects.filter(
            username__iexact=self.cleaned_data['username'])
        if existing.exists():
            raise forms.ValidationError(
                _("A user with that username already exists."))
        else:
            return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(
                    _("The two password fields didn't match."))
        return self.cleaned_data
