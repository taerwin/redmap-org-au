from backend.forms import UserAddForm, OrganisationAddForm, AddScientistForm, \
    AdministratorAllocationForm, AddSpeciesAllocation, AddEmailTemplateForm, \
    AddValidationRuleForm, EditSightingForm, SightingSpamForm, SightingReassignForm, \
    VerifyStep, VerifyStep3, RuleConditionTestForm, RuleConditionTestFormSet, \
    RuleForm, ValidationConditionForm, RegionalAdministratorAddForm, \
    SightingsListSearchForm
from backend.models import ValidationMessageTemplate, ValidationResponse, \
    SightingValidationCondition, SightingValidationRule, RuleConditionTest
from common.generic_views import AuthMixin
from datetime import datetime
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site, get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F, Q
from django.forms import model_to_dict
from django.forms.models import inlineformset_factory
from django.shortcuts import HttpResponseRedirect, HttpResponse, \
    get_object_or_404, render, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from formwizard.views import SessionWizardView
from privatebeta.models import InviteRequest
from redmap.apps.backend import emails
from redmap.common.tags import get_redmap_tag
from redmap.common.util import reverse_lazy
from redmapdb.models import Sighting, SpeciesAllocation, SightingTracking, \
    Accuracy, Region, Organisation, Species, AdministratorAllocation
from registration.models import RegistrationProfile
from tagging.models import Tag, TaggedItem
from zinnia.models import Entry
import json
import operator
import re
import uuid
from cms.models import CopyBlock



login_url = reverse_lazy('auth_login')


def is_sighting_valid(wizard):

    conditions = wizard.get_cleaned_data_for_step('0').get('conditions')

    sighting = wizard.instance_dict['0']  # TODO: better as an arg really
    has_photo = bool(sighting.photo_url)

    rule = SightingValidationRule.objects.find_matching_rule(
        conditions, has_photo)

    if rule is not None:

        assessment = rule.validation_message_template.public_assessment

        if not assessment:

            if rule.valid_sighting:
                default_assessment, created = CopyBlock.objects.get_or_create(
                    slug='assessment_valid_sighting',
                    defaults={'text': 'The sighting has been reviewed and verified.'})
            else:
                default_assessment, created = CopyBlock.objects.get_or_create(
                    slug='assessment_invalid_sighting',
                    defaults={'text': 'The sighting could not be confirmed.'})

            assessment = default_assessment.text

    else:
        raise Exception("No rule found")

    return dict({
        'valid': rule.valid_sighting, 'photo': has_photo,
        'template_id': rule.validation_message_template.id,
        'assessment': assessment})


class ScientistVerifyWizard(AuthMixin, SessionWizardView):

    required_permissions = [
        'redmapdb.change_sighting',
        'redmapdb.change_sightingtracking',
    ]

    def get_responses(self):
        """
        Returns a list of condition ids.  Only includes the ones
        checked by the scientist (aka positive response).
        """
        return self.get_cleaned_data_for_step('0').get('conditions')

    def done(self, form_list, *args, **kwargs):
        """
        Process and save validation report
        """

        context = self.get_context_data(form=form_list)

        result = is_sighting_valid(self)

        sighting = context['sighting']
        for form in form_list:
            for field, value in form.cleaned_data.iteritems():
                setattr(sighting, field, value)

        sighting.save()

        if sighting.tracker is None:
            """
            This sighting has no active tracker, which probably means that it
            has already been verified in the past. We should create a new
            tracker for the current user.
            """
            sighting.assign(self.request.user, "Re-validating sighting")

        if not sighting.tracker.person == self.request.user:
            sighting.reassign(sighting, self.request.user, 'Reassigned\
                to %s' % self.request.user.profile)

        responses = self.get_responses()
        ValidationResponse.objects.record_responses(sighting, responses)

        is_valid = result.get('valid')

        if is_valid:
            if result.get('photo'):
                sighting.report_valid_with_photo(
                    ValidationResponse.objects
                        .get_photo_matches_species_response(sighting),
                    sighting.assessment, sighting.is_displayed_on_site,
                    sighting.is_published)
            else:
                sighting.report_valid_without_photo(
                    sighting.assessment, sighting.is_displayed_on_site,
                    sighting.is_published)
        else:
            sighting.report_invalid(sighting.assessment, sighting.is_published)

        if is_valid:
            subject = "#%s - Valid sighting" % sighting.pk
        else:
            subject = "#%s - Invalid sighting" % sighting.pk

        from_email = sighting.region.email
        to = sighting.user.email

        REPLACEMENTS = dict([
            ('{sighter}', sighting.user.username),
            ('{species}', sighting.species_name),
            ('{sighting_url}',
                reverse('sighting_detail', kwargs={'pk': sighting.pk})),
        ])

        def replacer(m):
            return REPLACEMENTS[m.group(0)]

        content = sighting.message
        r = re.compile('|'.join(REPLACEMENTS.keys()))
        content = r.sub(replacer, content)

        text_content = content
        html_content = "<pre>" + content + "</pre>"
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        transaction.commit()

        if is_valid and sighting.user.get_profile().has_facebook_account():
            sighting.post_to_facebook(request=self.request)

        return HttpResponseRedirect(reverse_lazy('dashboard'))

    def get_template_names(self):
        step = int(self.storage.current_step)
        return 'backend/ScientistVerifyWizard/Step_%d.html' % step

    def get_context_data(self, form, **kwargs):
        context = super(ScientistVerifyWizard, self).get_context_data(
            form=form, **kwargs)

        sighting = self.instance_dict['0']  # TODO: better as an arg really

        context['sighting'] = sighting

        if self.steps.current == "1":

            matching_rules = SightingValidationRule.objects.filter(
                valid_sighting=is_sighting_valid(self).get('valid'))

            context['validation_templates'] = \
                ValidationMessageTemplate.objects.filter(
                    sightingvalidationrule__in=matching_rules)

        accuracies = Accuracy.objects.all()
        accuracy_dict = {}

        for a in accuracies:

            try:
                a.code = int(a.code)
            except:
                a.code = a.code[0:-1]

            accuracy_dict.update({a.id: a.code})

        context.update({'accuracies': accuracy_dict})

        context.update({'sighting_tracking': sighting.sighting_tracking.all()})

        return context

    def get_form_kwargs(self, step):
        kwargs = super(ScientistVerifyWizard, self).get_form_kwargs(step=step)

        if step == "1":
            results = is_sighting_valid(self)
            kwargs["is_success"] = results.get('valid')
            kwargs["template_id"] = results.get('template_id')
            kwargs["assessment"] = results.get('assessment')

        return kwargs


@login_required
@permission_required('redmapdb.change_sighting')
@permission_required('redmapdb.change_sightingtracking')
def scientist_verify_wizard(request, pk):

    sighting = Sighting.objects.get(id=pk)
    instance_dict = {"0": sighting}

    wizard = ScientistVerifyWizard.as_view(
        [VerifyStep, VerifyStep3], instance_dict=instance_dict
    )
    return wizard(request)


class manage_experts(AuthMixin, ListView):

    context_object_name = "species_allocations"
    template_name = "backend/manage_experts.html"
    paginate_by = 8

    required_permissions = [
        'redmapdb.change_speciesallocation',
    ]

    def get_queryset(self):
        """
        Filters the queryset based on supplied keyword arguments
        """
        filters = self.request.GET
        kwargs = {}

        if 'username' in filters:
            kwargs.update({'person__username': filters['username']})

        if 'region' in filters:
            kwargs.update({'region__description': filters['region']})

        if 'species' in filters:
            kwargs.update({'species__pk': filters['species']})

        self.filters = filters

        members = SpeciesAllocation.objects.filter(**kwargs)

        return members

    def get_context_data(self, **kwargs):
        """
        Provides required filter data to template
        """
        context = super(manage_experts, self).get_context_data(**kwargs)
        context['user_list'] = [
            (u.username, u.profile.display_name, ) for u in User.objects.filter(groups__name="Scientists", is_active=True).order_by('username')]
        context['region_list'] = (
            Region.objects.all().values_list(
                'id', 'description').order_by('description'))
        context['species_list'] = [
            (s.id, '{0} ( {1} )'.format(s.species_name, s.common_name), ) \
            for s in Species.objects.get_redmap().order_by('species_name')]

        context['filters'] = self.filters
        url_args = ""

        for k, v in self.filters.lists():
            if k != 'page':
                url_args = url_args + "&%s=%s" % (k, v[0])

        context['filter_url_args'] = url_args

        return context


class PanelListView(AuthMixin, ListView):

    context_object_name = "allocations"
    template_name = "backend/sightings_unvalidated.html"
    paginate_by = 8

    required_permissions = [
        'redmapdb.change_sighting',
        'redmapdb.change_sightingtracking',
    ]

    def get_queryset(self):
        """
        Filters the queryset based on supplied keyword arguments
        """
        filters = self.request.GET
        kwargs = {}

        if 'username' in filters:
            kwargs.update({'sighting__user__username': filters['username']})

        if 'species' in filters:
            kwargs.update({
                'sighting__species__pk': filters['species']
            })

        self.filters = filters

        sightings = SightingTracking.active_assignments.filter(
            **kwargs).order_by('-sighting__logging_date')

        if self.request.user.profile.is_scientist:
            '''
            Filter this list so that scientists only see sightings assigned to
            them, or sightings which were assigned to them in the past.
            '''
            for tracker in sightings:

                if tracker.person == self.request.user:
                    continue

                old_trackers = SightingTracking.objects.filter(
                    sighting=tracker.sighting,
                    person=self.request.user).exclude(pk=tracker.id)

                if not old_trackers:
                    sightings = sightings.exclude(pk=tracker.pk)

        return sightings

    def get_context_data(self, **kwargs):
        """
        Provides required filter data to template
        """
        context = super(PanelListView, self).get_context_data(**kwargs)
        context['user_list'] = [
            (u.username, u.profile.display_name, ) for u in User.objects.filter(is_active=True).order_by('username')]
        context['species_list'] = [
            (s.id, '{0} ( {1} )'.format(s.species_name, s.common_name), ) \
            for s in Species.objects.get_redmap().order_by('species_name')]

        context['filters'] = self.filters
        url_args = ""

        for k, v in self.filters.lists():
            if k != 'page':
                url_args = url_args + "&%s=%s" % (k, v[0])

        context['filter_url_args'] = url_args

        return context


class Dashboard(AuthMixin, ListView):

    context_object_name = "allocations"
    template_name = "backend/dashboard.html"

    required_permissions = [
        'redmapdb.can_access_dashboard',
    ]

    def get_queryset(self):
        return (
            SightingTracking
                .active_assignments
                .filter(person=self.request.user)
                .order_by('-sighting__logging_date'))

    def get_context_data(self, **kwargs):

        context = super(Dashboard, self).get_context_data(**kwargs)
        context['recent_news'] = TaggedItem.objects.get_by_model(
            Entry.published, get_redmap_tag())[:3]
        return context


class ScientistIndex(AuthMixin, ListView):

    context_object_name = "scientists"
    template_name = "backend/scientist_index.html"

    required_permissions = [
        'auth.change_user',
    ]

    def get_queryset(self):
        return User.objects.filter(groups__name="Scientists")


@login_required
@permission_required('redmapdb.change_speciesallocation')
def AddSpeciesExpert(request, pk=None, template_name="backend/add_expert.html"):

    if pk:
        allocation = get_object_or_404(SpeciesAllocation, pk=pk)
    else:
        allocation = SpeciesAllocation()

    if request.POST:
        form = AddSpeciesAllocation(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('manage_experts'))
    else:
        form = AddSpeciesAllocation(instance=allocation)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('redmapdb.delete_speciesallocation')
def DeleteSpeciesExpert(request, pk=None,
                        template_name="backend/delete_expert.html"):

    allocation = SpeciesAllocation.objects.get(pk=pk)

    if pk and request.POST:
        allocation.delete()
        return HttpResponseRedirect(reverse_lazy('manage_experts'))

    return render(
        request,
        template_name,
        {'allocation': allocation}
    )


@login_required
@permission_required('auth.change_user')
def AddScientist(request):

    form = AddScientistForm(request.POST or None)

    if request.POST and form.is_valid():

        user_id = form.cleaned_data.get('username')
        user = User.objects.get(pk=user_id)
        organisation = form.cleaned_data.get('organisation')

        group = Group.objects.get(name="Scientists")
        group.user_set.add(user)

        person = user.get_profile()
        person.organisation = organisation
        person.save()

        emails.advise_scientist_promotion(user)

        messages.success(request, 'The member was successfully promoted')

        return redirect(reverse('scientist_index'))

    return render(request, "backend/add_scientist.html", {'form': form})


@login_required
@permission_required('auth.change_user')
def DeleteScientist(request, pk=None,
                    template_name="backend/delete_scientist.html"):

    user = User.objects.get(pk=pk)

    if pk and request.POST:

        group = Group.objects.get(name="Scientists")
        group.user_set.remove(user)

        return HttpResponseRedirect(reverse_lazy('scientist_index'))

    return render(
        request,
        template_name,
        {'user': user}
    )

@login_required
@permission_required('backend.change_sightingvalidationrule')
def validation_rules(request):

    rules = SightingValidationRule.objects.all()

    return render(
        request,
        "backend/validation_rules.html",
        {'rules': rules}
    )


@login_required
@permission_required('backend.add_sightingvalidationrule')
def add_validation_rule(request,
    template_name="backend/add_validation_rule.html"):

    rule = SightingValidationRule()
    conditions = SightingValidationCondition.objects.all()
    rule_conditions = [{'condition': c} for c in conditions]

    InitialRuleConditionTestFormSet = inlineformset_factory(
        SightingValidationRule,
        RuleConditionTest,
        form=RuleConditionTestForm,
        can_delete=False,
        extra=len(rule_conditions))

    if request.POST:
        form = RuleForm(request.POST, instance=rule)
        tests = InitialRuleConditionTestFormSet(request.POST, instance=rule,
            initial=rule_conditions)
        form_valid = form.is_valid()
        tests_valid = tests.is_valid()
        if form_valid and tests_valid:
            rule = form.save()
            tests.save()
            return HttpResponseRedirect(reverse('validation_rules'))
    else:
        form = RuleForm(instance=rule)

        tests = InitialRuleConditionTestFormSet(instance=rule,
            initial=rule_conditions)

    return render(request, template_name, {'form': form, 'tests': tests})


@login_required
@permission_required('backend.change_sightingvalidationrule')
def edit_validation_rule(request, pk,
    template_name="backend/add_validation_rule.html"):

    rule = get_object_or_404(SightingValidationRule, pk=pk)

    RuleConditionTest.objects.tests_for_rule(rule)


    if request.POST:

        tests = RuleConditionTestFormSet(request.POST, instance=rule)
        form = RuleForm(request.POST, instance=rule)
        form_valid = form.is_valid()
        tests_valid = tests.is_valid()

        if form_valid and tests_valid:

            form.save()
            tests.save()

            return HttpResponseRedirect(reverse('validation_rules'))
    else:
        tests = RuleConditionTestFormSet(instance=rule)
        form = RuleForm(instance=rule)

    context = {'form': form, 'tests': tests, 'pk': pk}
    return render(request, template_name, context)


@login_required
@permission_required('backend.delete_sightingvalidationrule')
def delete_validation_rule(request, pk, template_name="backend/delete_validation_rule.html"):

    rule = get_object_or_404(SightingValidationRule, pk=pk)

    if request.POST:
        rule.delete()
        return HttpResponseRedirect(reverse_lazy('validation_rules'))

    return render(
        request,
        template_name,
        {'rule': rule}
    )


@login_required
@permission_required('backend.change_validationmessagetemplate')
def EmailTemplates(request):

    templates = ValidationMessageTemplate.objects.all()

    return render(
        request,
        "backend/manage_email_templates.html",
        {'templates': templates}
    )


@login_required
@permission_required('backend.change_validationmessagetemplate')
def AddEmailTemplate(request, pk=None,
                     template_name="backend/add_email_template.html"):
    if pk:
        rule = get_object_or_404(ValidationMessageTemplate, pk=pk)
    else:
        rule = ValidationMessageTemplate()

    if request.POST:
        form = AddEmailTemplateForm(request.POST, instance=rule)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('manage_email_templates'))

    else:
        form = AddEmailTemplateForm(instance=rule)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('backend.delete_validationmessagetemplate')
def DeleteEmailTemplate(request, pk=None,
                        template_name="backend/delete_email_template.html"):

    rule = ValidationMessageTemplate.objects.get(pk=pk)

    if pk and request.POST:
        rule.delete()
        return HttpResponseRedirect(reverse_lazy('manage_email_templates'))

    return render(
        request,
        template_name,
        {'rule': rule}
    )


class MemberIndex(AuthMixin, ListView):

    context_object_name = "users"
    template_name = 'backend/member_index.html'
    paginate_by = 8

    required_permissions = [
        'auth.change_user',
    ]

    def get_queryset(self):
        """
        Filters the queryset based on supplied keyword arguments
        """
        filters = self.filters = self.request.GET
        args = []
        kwargs = {}

        qs = User.objects.all()

        if filters.get('activated', None) == "False":
            activate=RegistrationProfile.ACTIVATED
            qs = qs.filter(
                ~Q(registrationprofile__activation_key=activate) &
                 Q(registrationprofile__activation_key__isnull=False))

        if 'group' in filters:
            qs = qs.filter(groups__name=filters['group'])

        if 'search' in filters:
            def search_for_bit(bit):
                return (
                    Q(username__contains=bit) |
                    Q(email__contains=bit) |
                    Q(first_name__contains=bit) |
                    Q(last_name__contains=bit))

            search_words = filters['search'].split()
            search_q = reduce(operator.and_, map(search_for_bit, search_words))
            qs = qs.filter(search_q)

        return qs

    def get_context_data(self, **kwargs):
        """
        Provides required filter data to template
        """
        context = super(MemberIndex, self).get_context_data(**kwargs)
        context['group_list'] = Group.objects.order_by('name').values_list(
            'id', 'name')
        context['filters'] = self.filters
        url_args = ""

        for k, v in self.filters.lists():

            if k != 'page':
                url_args = url_args + "&%s=%s" % (k, v[0])

        context['filter_url_args'] = url_args

        return context


@login_required
@permission_required('auth.change_user')
def MemberAdd(request, pk=None, template_name="backend/member_add.html"):

    if pk:
        member = get_object_or_404(User, pk=pk)
    else:
        member = User()

    if request.POST:
        form = UserAddForm(request.POST, instance=member)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('member_index'))

    else:
        form = UserAddForm(instance=member)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('auth.change_user')
def MemberDelete(request, pk=None, template_name="backend/member_delete.html"):

    member = User.objects.get(pk=pk)

    if pk and request.POST:

        member.is_active = False
        member.save()

        return HttpResponseRedirect(reverse_lazy('member_index'))

    return render(
        request,
        template_name,
        {'member': member}
    )


class OrganisationIndex(AuthMixin, ListView):

    queryset = Organisation.objects.all()
    context_object_name = "organisations"
    template_name = 'backend/organisation_index.html'
    paginate_by = 8

    required_permissions = [
        'redmapdb.change_organisation',
    ]


@login_required
@permission_required('redmapdb.change_organisation')
def OrganisationAdd(request, pk=None,
                    template_name="backend/organisation_add.html"):

    if pk:
        organisation = get_object_or_404(Organisation, pk=pk)
    else:
        organisation = Organisation()

    if request.POST:
        form = OrganisationAddForm(
            request.POST, request.FILES, instance=organisation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('organisation_index'))

    else:
        form = OrganisationAddForm(instance=organisation)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('redmapdb.delete_organisation')
def OrganisationDelete(request, pk=None,
                       template_name="backend/organisation_delete.html"):

    organisation = Organisation.objects.get(pk=pk)

    if pk and request.POST:
        organisation.delete()
        return HttpResponseRedirect(reverse_lazy('organisation_index'))

    return render(
        request,
        template_name,
        {'organisation': organisation}
    )


class BaseSightingsList(AuthMixin, ListView):

    context_object_name = "sightings"
    template_name = "backend/sightings_list.html"
    paginate_by = 8

    required_permissions = [
        'redmapdb.change_sighting',
        'redmapdb.change_sightingtracking',
    ]

    @property
    def all_sightings(self):
        raise NotImplemented("all_sightings must be defined by the subclass")

    def get_queryset(self):
        """
        Return all sightings but filtered by GET vars.
        """
        sightings = self.all_sightings()
        self.search_form = SightingsListSearchForm(
            prefix="filter",
            queryset=self.all_sightings(),
            data=self.request.GET)

        return self.search_form.qs

    def get_context_data(self, **kwargs):
        """
        Provides required filter data to template.
        """
        context = super(BaseSightingsList, self).get_context_data(**kwargs)

        get = self.request.GET.copy()
        get.pop('page', None)

        context.update({
            'search_form': self.search_form,
            'filter_url_args': '&' + get.urlencode(),
            'UNKNOWN': settings.REQUIRES_VALIDATION,
        })

        return context


class AllSightingsList(BaseSightingsList):

    required_permissions = [
        'redmapdb.can_access_dashboard',
        'redmapdb.can_manage_sightings',
    ]

    def all_sightings(self):
        """
        Get all sightings. Completely unfiltered.
        """
        return Sighting.objects.all()


class MySightingList(BaseSightingsList):

    template_name = "backend/past_sightings_list.html"

    required_permissions = [
        'redmapdb.can_access_dashboard',
    ]

    def all_sightings(self):
        """
        Get the sightings assigned to the current user.
        """
        return Sighting.objects.get_sightings_for_user(self.request.user)


class ActiveSightingList(BaseSightingsList):

    template_name = "backend/active_sightings_list.html"

    required_permissions = [
        'redmapdb.can_access_dashboard',
    ]

    def all_sightings(self):
        """
        Only return sightings owned by user with an active tracker.
        """
        return Sighting.objects.get_sightings_for_user_by_active_assignments(self.request.user)


@login_required
@permission_required('redmapdb.change_sighting')
@permission_required('redmapdb.change_sightingtracking')
def SightingEdit(request, pk=None, template_name="backend/sighting_edit.html"):

    if pk:
        sighting = get_object_or_404(Sighting, pk=pk)
    else:
        sighting = Sighting()

    if request.POST:
        form = EditSightingForm(request.POST, instance=sighting)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('sightings_list'))

    else:
        sighting.sighting_date = sighting.sighting_date.strftime('%Y-%m-%d')
        form = EditSightingForm(instance=sighting)

    accuracies = Accuracy.objects.all()
    accuracy_dict = {}
    for a in accuracies:
        try:
            a.code = int(a.code)
        except:
            a.code = a.code[0:-1]
        accuracy_dict.update({a.id: a.code})

    trackings = sighting.sighting_tracking.all()
    for tracking in trackings:
        tracking.validation_response = ValidationResponse.objects.filter(
            sighting_tracking=tracking)

    return render(
        request,
        template_name,
        {
            'form': form,
            'pk': pk,
            'accuracies': accuracy_dict,
            'sighting': sighting,
            'sighting_tracking': trackings,
        }
    )


@login_required
@permission_required('redmapdb.delete_sighting')
def SightingDelete(request, pk=None,
                   template_name="backend/sighting_delete.html"):

    sighting = Sighting.objects.get(pk=pk)

    if pk and request.POST:
        sighting.delete()
        return HttpResponseRedirect(reverse_lazy('sightings_list'))

    return render(
        request,
        template_name,
        {'sighting': sighting}
    )


@login_required
@permission_required('redmapdb.change_sighting')
@permission_required('redmapdb.change_sightingtracking')
def SightingReassign(request, pk=None,
                     template_name="backend/sighting_reassign.html"):

    if pk:
        sighting = get_object_or_404(Sighting, pk=pk)

    if request.method == 'POST':

        data = request.POST
        user = User.objects.get(pk=data.get('username'))
        comment = data.get('comment')

        sighting.reassign(request.user, user, comment)

        return HttpResponseRedirect(reverse_lazy('sightings_unvalidated'))

    else:
        form = SightingReassignForm()

    return render(
        request,
        template_name,
        {
            'form': form,
            'sighting': sighting
        }
    )


@login_required
@permission_required('redmapdb.change_sighting')
@permission_required('redmapdb.change_sightingtracking')
def SightingSpam(request, pk=None, template_name="backend/sighting_spam.html"):

    sighting = get_object_or_404(Sighting, pk=pk)

    if request.POST:
        sighting.report_spam(request.POST.get('comment'))
        return HttpResponseRedirect(reverse_lazy('sightings_unvalidated'))

    return render(
        request,
        template_name,
        {'sighting': sighting, 'pk': pk, 'form': SightingSpamForm()}
    )


class BetaInvites(AuthMixin, ListView):

    context_object_name = 'invites'
    template_name = 'backend/beta.html'
    model = InviteRequest

    required_permissions = [
        'privatebeta.change_inviterequest',
    ]

    def get_queryset(self):
        return InviteRequest.objects.all().order_by('invited', '-created')


@login_required
@permission_required('auth.change_user')
@permission_required('privatebeta.change_inviterequest')
def BetaSendInvite(request, pk=None,
                   template_name="backend/beta_send_invite.html"):

    invite = get_object_or_404(InviteRequest, pk=pk)

    if invite.invited:
        return HttpResponseRedirect(reverse_lazy('beta_invites'))

    try:
        user = User.objects.get(email=invite.email)
    except User.DoesNotExist:
        user = None

    if request.POST:

        password = None

        if user is None:

            password = uuid.uuid1()
            user = User.objects.create_user(
                invite.email, invite.email, password)
            user.is_active = True
            user.save()

        subject = 'REDMAP Beta Invite'
        from_email = settings.DEFAULT_FROM_EMAIL
        to = invite.email
        dictionary = {
            'email': invite.email,
            'password': password,
            'domain': Site.objects.get_current().domain,
        }
        text_content = render_to_string(
            'backend/email/text/beta_invite.html', dictionary)
        html_content = render_to_string(
            'backend/email/html/beta_invite.html', dictionary)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        invite.invited = True
        invite.save()

        return HttpResponseRedirect(reverse_lazy('beta_invites'))

    return render(
        request,
        template_name,
        {
            'invite': invite,
            'user': user,
        }
    )


@login_required
@permission_required('backend.change_sightingvalidationcondition')
def ValidationConditions(request):

    conditions = SightingValidationCondition.objects.all()

    return render(
        request,
        "backend/validation_conditions.html",
        {'conditions': conditions}
    )


@login_required
@permission_required('backend.change_sightingvalidationcondition')
def ValidationConditionAdd(
    request, pk=None, template_name="backend/validation_condition_edit.html"):

    if pk:
        condition = get_object_or_404(SightingValidationCondition, pk=pk)
    else:
        condition = SightingValidationCondition()

    if request.POST:
        form = ValidationConditionForm(request.POST, instance=condition)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('validation_conditions'))
    else:
        form = ValidationConditionForm(instance=condition)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('backend.delete_sightingvalidationcondition')
def ValidationConditionDelete(
    request, pk=None, template_name="backend/validation_condition_delete.html"):

    condition = SightingValidationCondition.objects.get(pk=pk)

    if pk and request.POST:
        condition.delete()
        return HttpResponseRedirect(reverse_lazy('validation_conditions'))

    return render(
        request,
        template_name,
        {'condition': condition}
    )


class RegionalAdministrators(AuthMixin, ListView):

    context_object_name = "administrators"
    template_name = "backend/regional_administrators.html"

    required_permissions = [
        'redmapdb.change_administratorallocation',
        'auth.change_user',
    ]

    def get_queryset(self):
        return User.objects.filter(groups__name="Regional Administrators")


@login_required
@permission_required('redmapdb.change_administratorallocation')
@permission_required('auth.change_user')
def RegionalAdministratorAdd(
    request, template_name="backend/regional_administrator_add.html"):

    form = RegionalAdministratorAddForm(request.POST or None)

    if request.POST and form.is_valid():

        user_id = form.cleaned_data.get('username')
        user = User.objects.get(pk=user_id)
        organisation = form.cleaned_data.get('organisation')

        group = Group.objects.get(name="Regional Administrators")
        group.user_set.add(user)

        person = user.get_profile()
        person.organisation = organisation
        person.save()

        emails.advise_regional_admin_promotion(user)

        messages.success(request, 'The member was successfully promoted')

        return redirect(reverse('regional_administrators'))

    return render(request, template_name, {'form': form})


@login_required
@permission_required('redmapdb.delete_administratorallocation')
@permission_required('auth.change_user')
def RegionalAdministratorDelete(request, pk=None,
    template_name="backend/regional_administrator_delete.html"):

    user = User.objects.get(pk=pk)

    if pk and request.POST:
        group = Group.objects.get(name="Regional Administrators")
        group.user_set.remove(user)
        return HttpResponseRedirect(reverse_lazy('regional_administrators'))

    return render(
        request,
        template_name,
        {'user': user}
    )


class AdministratorAllocations(AuthMixin, ListView):

    context_object_name = "administrator_allocations"
    template_name = "backend/administrator_allocations.html"
    paginate_by = 8

    required_permissions = [
        'redmapdb.change_administratorallocation',
    ]

    def get_queryset(self):
        """
        Filters the queryset based on supplied keyword arguments
        """
        filters = self.request.GET
        kwargs = {}

        if 'username' in filters:
            kwargs.update({'person__username': filters['username']})

        if 'region' in filters:
            kwargs.update({'region__description': filters['region']})

        self.filters = filters

        return AdministratorAllocation.objects.filter(**kwargs)

    def get_context_data(self, **kwargs):
        """
        Provides required filter data to template
        """
        context = super(
            AdministratorAllocations, self).get_context_data(**kwargs)
        context['user_list'] = [
            (u.username, u.profile.display_name, ) for u in User.objects.filter(groups__name="Regional Administrators", is_active=True).order_by('username')]
        context['region_list'] = Region.objects.all().values_list(
            'id', 'description').order_by('description')
        context['filters'] = self.filters
        url_args = ""
        for k, v in self.filters.lists():
            if k != 'page':
                url_args = url_args + "&%s=%s" % (k, v[0])
        context['filter_url_args'] = url_args

        return context


@login_required
@permission_required('redmapdb.change_administratorallocation')
def AdministratorAllocationEdit(request, pk=None,
    template_name="backend/administrator_allocation_edit.html"):

    if pk:
        allocation = get_object_or_404(AdministratorAllocation, pk=pk)
    else:
        allocation = AdministratorAllocation()

    if request.POST:
        form = AdministratorAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('administrator_allocations'))
    else:
        form = AdministratorAllocationForm(instance=allocation)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('redmapdb.delete_administratorallocation')
def AdministratorAllocationDelete(request, pk=None,
    template_name="backend/administrator_allocation_delete.html"):

    allocation = AdministratorAllocation.objects.get(pk=pk)

    if pk and request.POST:
        allocation.delete()
        return HttpResponseRedirect(reverse_lazy('administrator_allocations'))

    return render(
        request,
        template_name,
        {'allocation': allocation}
    )


@login_required
@permission_required('auth.change_user')
def resend_member_activation(request, user_id):
    user = User.objects.get(pk=user_id)
    profile = user.get_profile()

    confirming = '__confirm__' in request.POST
    if profile.is_pending_activation and request.POST and confirming:
        current_site = get_current_site(request)
        registration = user.get_profile().pending_activation

        registration.send_activation_email(current_site)

        messages.success(request, 'Activation email has been resent.')
        return redirect(reverse('member_index'))

    if not profile.is_pending_activation:
        messages.warning(request, 
            'Cannot resend activation for this user as no activation is '
            'pending.')

    payload = {
        'user': user,
    }

    return render(request, "backend/resend_member_activation.html", payload)
