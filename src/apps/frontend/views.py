import datetime

from common.util import reverse_lazy
from common.sql import distinct_by_annotation
from dateutil import parser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMultiAlternatives
from django.http import Http404
from django.shortcuts import HttpResponse, HttpResponseRedirect, render,\
    render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin

from formwizard.views import SessionWizardView
from frontend.forms import (
    AddStep1, AddStep2, AddStep3, AddStep4,
    FBGroupForm,
    FilterSpeciesForm, SpeciesJumpForm,
    RegionJumpForm, RegionCategoryJumpForm,
)
from frontend.models import Faq, Sponsor, SponsorCategory
from redmapdb.models import *
from tagging.models import Tag, TaggedItem
from zinnia.managers import DRAFT, HIDDEN, PUBLISHED
from zinnia.models import Entry
from redmap.common.util import dms2dd
from redmap.common.tags import get_redmap_tag
from redmap.common.views import UploadHandlerMixin
from django.views.decorators.csrf import csrf_exempt

import logging
logger = logging.getLogger()
logger = logging.getLogger("django.request")


class RedmapContextMixin(TemplateResponseMixin):

    def get_context_data(self, **kwargs):
        context = super(RedmapContextMixin, self).get_context_data(**kwargs)

        if 'region_slug' in self.kwargs:
            self.region = Region.objects.get(
                slug=self.kwargs.get('region_slug')
            )
        elif 'region_id' in self.kwargs:
            self.region = Region.objects.get(pk=self.kwargs.get('region_id'))
        else:
            self.region = None

        shown_species = Species.objects.sighted_species(self.region)

        if self.request.GET and 'species' in self.request.GET:
            try:
                species = Species.objects.get(
                    id=self.request.GET.get('species')
                )
                context['species_filter'] = species.pk
                context['species_filter_get'] =\
                    "species={0}".format(species.pk)
                form = FilterSpeciesForm(
                    shown_species, initial={'species': species.pk})

            except (Species.DoesNotExist, ValueError):
                form = FilterSpeciesForm(shown_species)
        else:
            form = FilterSpeciesForm(shown_species)

        context.update({
            'species_filter_form': form,
            'region': self.region,
            'is_region_page': self.kwargs.get('is_region_page', False),
        })

        return context


def get_exif(fn):
    '''
    Get image EXIF data if it is present
    '''
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS  # bindings to well-known EXIF tags

    ret = {}
    i = Image.open(fn)
    if hasattr(i, '_getexif'):
        info = i._getexif()
        if info is not None:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'GPSInfo':
                    new_value = {}

                    for t, v in value.items():
                        d = GPSTAGS.get(t, t)
                        new_value[d] = v

                    latitude_dms = [(tup[0] / tup[1])
                                    for tup in new_value['GPSLatitude']]

                    if new_value['GPSLatitudeRef'] == 'S':

                        new_value['GPSLatitude'] = dms2dd(
                            -latitude_dms[0],
                            latitude_dms[1],
                            latitude_dms[2]
                        )

                    else:
                        new_value['GPSLatitude'] = dms2dd(
                            latitude_dms[0],
                            latitude_dms[1],
                            latitude_dms[2]
                        )

                    longitude_dms = [(tup[0] / tup[1])
                                     for tup in new_value['GPSLongitude']]

                    if new_value['GPSLongitudeRef'] == 'W':

                        new_value['GPSLongitude'] = dms2dd(
                            -longitude_dms[0],
                            longitude_dms[1],
                            longitude_dms[2]
                        )

                    else:
                        new_value['GPSLongitude'] = dms2dd(
                            longitude_dms[0],
                            longitude_dms[1],
                            longitude_dms[2]
                        )

                    value = new_value

                ret[decoded] = value

    return ret


fs = FileSystemStorage(settings.MEDIA_ROOT + '/pictures')


class AddWizard(UploadHandlerMixin, SessionWizardView):
    file_storage = fs
    upload_handler = 'redmap.common.views.ProgressBarUploadHandler'

    def done(self, form_list, *args, **kwargs):

        sighting_data = {}
        for form in form_list:
            for field, value in form.cleaned_data.iteritems():
                sighting_data[field] = value

        instance = Sighting.objects.log_with_data(
            self.request.user,
            sighting_data
        )

        return render_to_response(
            'frontend/sighting_add_done.html',
            {
                'form_list': [form.cleaned_data for form in form_list]
            },
            context_instance=RequestContext(self.request)
        )

    def get_form_initial(self, step):
        initial = super(AddWizard, self).get_form_initial(step)

        if step == '0':
            species_id = self.request.GET.get('species')

            if species_id:
                initial.update({
                    'species': Species.objects.get(pk=species_id)
                })

        initial['request'] = self.request
        return initial

    def get_context_data(self, form, **kwargs):
        context = super(AddWizard, self).get_context_data(form, **kwargs)

        picture_data = self.get_cleaned_data_for_step('0')

        if picture_data:
            '''
            If there is submitted picture data, attach it to the request
            context for use on subsequent formwizard pages
            '''
            caption = picture_data['photo_caption']

            if picture_data['photo_url'] is not None:
                url = fs.path(picture_data['photo_url'])
            else:
                url = picture_data['photo_url']

            context.update({
                'picture_data': {
                    'photo_caption': caption,
                    'photo_url': url
                }
            })

            '''
            If there is a picture, try and extract EXIF data from it
            '''
            if url is not None:

                try:
                    exif = get_exif(url)
                    context.update({
                        'exif_data': exif
                    })

                    date_string = exif.get('DateTime') or\
                        exif.get('DateTimeDigitalized') or\
                        exif.get('DateTimeOriginal')

                    if date_string:
                        exif_date_format = '%Y:%m:%d %H:%M:%S'
                        try:
                            date = datetime.strptime(
                                date_string, exif_date_format)
                            hour = code = date.strftime('%H')
                            context.update({
                                'exif_date': date,
                                'exif_time': Time.objects.get(code=hour).id
                            })
                        except ValueError, Time.DoesNotExist:
                            pass

                except Exception:
                    logger.exception(
                        "Failed to decode exif data for {0}".format(url))

        accuracies = Accuracy.objects.all()
        accuracy_dict = {}
        for a in accuracies:
            try:
                a.code = int(a.code)
            except:
                a.code = a.code[0:-1]
            accuracy_dict.update({a.id: a.code})
        context.update({'accuracies': accuracy_dict})

        if int(self.storage.current_step) == 3:
            context.update({
                'step1': dict(self.get_cleaned_data_for_step('0')),
                'step2': dict(self.get_cleaned_data_for_step('1')),
                'step3': dict(self.get_cleaned_data_for_step('2'))
            })

        return context

    def get_template_names(self):
        step = int(self.storage.current_step)
        return 'frontend/AddWizard/Step_%d.html' % step

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddWizard, self).dispatch(*args, **kwargs)

add_wizard = AddWizard.as_view(
    [AddStep1, AddStep2, AddStep3, AddStep4]
)


def region_landing_page(request, region_slug):

    region = Region.objects.get(slug=region_slug)
    region_tag = Tag.objects.get_for_object(region)[0]

    categories = SponsorCategory.objects.all().order_by('-order')
    request.session['filter_by_region'] = int(region.pk)

    photo_sightings = Sighting.objects.get_public_photo()\
        .filter(region=region)[:15]

    context = {
        'region': region,
        'is_region_page': True,
        'recent_activity': photo_sightings[:5],
        'recent_news': TaggedItem.objects.get_union_by_model(
        Entry.published, (region_tag, get_redmap_tag())
        ).filter(categories__slug='news', status=PUBLISHED)[:4],
        'photo_sightings': photo_sightings,
    }

    return render(request, 'frontend/region.html', context)


class SightingDetailView(DetailView, RedmapContextMixin):

    context_object_name = 'sighting'
    model = Sighting
    template_name = 'frontend/sighting_detail.html'

    def get_object(self, queryset=None):
        """
        We don't always want a sighting to be publicly visible. If a sighting
        has yet to be validated (or is not validated), the only person who
        should be able to view this sighting is the sighter themselves.
        Based on this, we will perform a basic permissions check, to see if we
        should bother fetching the data for this sighting.
        """
        sighting = super(SightingDetailView, self).get_object()

        if sighting.user == self.request.user:
            return sighting

        if not sighting.is_published:
            raise Http404

        return sighting

    def get_context_data(self, **kwargs):
        context = super(SightingDetailView, self).get_context_data(**kwargs)

        context['recent_species_sightings'] =\
            Sighting.objects.get_recent(context['sighting'])
        context['recent_area_sightings'] =\
            Sighting.objects.get_recent_sightings_in_area(context['sighting'])

        try:
            context['species_in_category'] = SpeciesInCategory.objects.get(
                species=context['sighting'].species
            )
        except SpeciesInCategory.DoesNotExist:
            context['species_in_category'] = None

        context['sighting_tracking'] = context['sighting'].latest_tracker

        context['bounds_top_longitude'] =\
            round(float(context['sighting'].longitude) / .5) * .5
        context['bounds_top_latitude'] =\
            round(float(context['sighting'].latitude) / .5) * .5

        if context['bounds_top_longitude'] > context['sighting'].longitude:
            context['bounds_bottom_longitude'] =\
                round(float(context['sighting'].longitude) / .5) * .5 - .5
        else:
            context['bounds_bottom_longitude'] =\
                round(float(context['sighting'].longitude) / .5) * .5 + .5

        if context['bounds_top_latitude'] > context['sighting'].latitude:
            context['bounds_bottom_latitude'] =\
                round(float(context['sighting'].latitude) / .5) * .5 - .5
        else:
            context['bounds_bottom_latitude'] =\
                round(float(context['sighting'].latitude) / .5) * .5 + .5

        context['domain'] = Site.objects.get_current().domain
        context['fbappid'] = settings.FACEBOOK_APP_ID

        return context


class Homepage(ListView):

    queryset = Sighting.objects.get_public_photo()[:5]
    context_object_name = 'latest_sightings'
    model = Sighting
    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        context = super(Homepage, self).get_context_data(**kwargs)

        context['photo_sightings'] = Sighting.objects.get_public_photo()[:15]
        context['recent_news'] = TaggedItem.objects.get_by_model(
            Entry.published, get_redmap_tag()
        ).filter(categories__slug='news', status=PUBLISHED)[:4]

        if self.request.session.get('filter_by_region'):
            del self.request.session['filter_by_region']

        return context


class SpeciesInCategoryList(ListView, RedmapContextMixin):

    context_object_name = 'species_list'
    model = Species
    template_name = 'frontend/species_list.html'
    paginate_by = 0

    def get_queryset(self):

        category = get_object_or_404(
            SpeciesCategory, pk=self.kwargs['category'])

        region_slug = self.kwargs.get('region_slug', None)
        if region_slug:
            region = get_object_or_404(Region, slug=region_slug)
        else:
            region = None

        return Species.objects.get_redmap(category, region)

    def get_context_data(self, **kwargs):
        context = super(SpeciesInCategoryList, self).get_context_data(**kwargs)
        category = SpeciesCategory.objects.get(pk=self.kwargs['category'])

        context.update({
            'form': SpeciesJumpForm(self.region),
            'region': self.region,
            'region_jump_form': RegionCategoryJumpForm(category),
            'category': category,
        })

        return context


class Faqs(ListView):

    context_object_name = 'faqs'
    model = Faq
    template_name = 'frontend/faq_list.html'


class Scientists(ListView, RedmapContextMixin):

    context_object_name = 'scientists'
    model = Person
    template_name = 'frontend/scientist_list.html'

    def get_queryset(self):

        region_slug = self.kwargs.get('region_slug', None)

        if region_slug:

            allocations =\
                SpeciesAllocation.objects.filter(region__slug=region_slug)

            people = {}
            for allocation in allocations:
                people.update({str(allocation.person.id): allocation.person})

            return people

        else:
            return Person.objects.filter(user__groups__name='Scientists')


class Articles(ListView):

    context_object_name = 'articles'
    model = Entry
    template_name = 'frontend/article_list.html'

    def get_queryset(self):
        return Entry.published.filter(categories__title='Articles')


class SpeciesDetailView(DetailView):

    model = Species
    context_object_name = 'species'
    template_name = 'frontend/species_detail.html'

    def get_context_data(self, **kwargs):
        context = super(SpeciesDetailView, self).get_context_data(**kwargs)
        species = self.get_object()

        category = SpeciesCategory.objects.get(pk=self.kwargs['category'])
        context['category'] = category
        context['category_id'] = category.pk
        context['sightings'] =\
            Sighting.objects.get_public().filter(species=species)
        context['regions_of_interest'] = distinct_by_annotation(
            Region.objects.filter(speciesallocation__species=species))

        return context


def NewsletterSignup(request, template_name='frontend/newsletter_signup.html'):

    return render(request, template_name)


def NewsletterSignupPage(request, template_name='frontend/newsletter_signup_page.html'):

    return render(request, template_name)


def render_cluster(request, count):

    import Image
    import ImageFont
    import ImageDraw

    W = 100  # img.size[0]
    H = 100  # img.size[1]

    f = ImageFont.truetype(
        settings.WEBAPP_ROOT + '/static/fonts/FreeSans.ttf',
        48
    )
    img = Image.new('RGBA', (W, H))

    if count == '1':
        count = ''

    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, W, H), fill=(255, 0, 0))
    w, h = draw.textsize(count, f)
    draw.text(((W - w) / 2, (H - h)), count, font=f, fill='black')

    response = HttpResponse(mimetype='image/png')
    img.save(response, 'PNG')

    return response


class SightingsPhoto(ListView, RedmapContextMixin):

    context_object_name = 'photo_sightings'
    template_name = 'frontend/sighting_photo.html'
    paginate_by = 12

    def get_queryset(self):

        region_slug = self.kwargs.get('region_slug', None)

        if region_slug:
            sightings = Sighting.objects.get_public_photo().\
                filter(region__slug=region_slug).order_by('-sighting_date')
        else:
            sightings = Sighting.objects.get_public_photo(
            ).order_by('-sighting_date')

        if self.request.GET and 'species' in self.request.GET:
            try:
                species =\
                    Species.objects.get(id=self.request.GET.get('species'))
                sightings = sightings.filter(species=species)
            except Species.DoesNotExist:
                pass
            except ValueError:
                pass

        return sightings


class SightingsList(ListView, RedmapContextMixin):

    context_object_name = 'latest_sightings'
    template_name = 'frontend/sighting_latest.html'
    paginate_by = 20

    def get_queryset(self):

        region_slug = self.kwargs.get('region_slug', None)

        if region_slug:
            sightings =\
                Sighting.objects.get_public().filter(region__slug=region_slug)
        else:
            sightings = Sighting.objects.get_public()

        if self.request.GET and 'species' in self.request.GET:
            try:
                species =\
                    Species.objects.get(id=self.request.GET.get('species'))
                sightings = sightings.filter(species=species)
            except Species.DoesNotExist:
                pass
            except ValueError:
                pass

        return sightings


class SightingsMap(ListView, RedmapContextMixin):

    context_object_name = 'sightings'
    template_name = 'frontend/sighting_map.html'

    def get_queryset(self):

        region_slug = self.kwargs.get('region_slug', None)

        if region_slug:
            sightings =\
                Sighting.objects.get_public().filter(region__slug=region_slug)
        else:
            sightings = Sighting.objects.get_public()

        if self.request.GET and 'species' in self.request.GET:
            try:
                species =\
                    Species.objects.get(id=self.request.GET.get('species'))
                sightings = sightings.filter(species=species)
            except Species.DoesNotExist:
                pass
            except ValueError:
                pass

        return sightings


class SpeciesCategoryView(ListView, RedmapContextMixin):

    context_object_name = 'category_list'
    template_name = 'frontend/species_category_list.html'
    paginate_by = 12

    def get_queryset(self):
        return SpeciesCategory.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SpeciesCategoryView, self).get_context_data(**kwargs)

        context.update({
            'form': SpeciesJumpForm(),
            'region_jump_form': RegionJumpForm()
        })

        return context


class GroupsList(ListView):

    context_object_name = 'groups'
    template_name = 'frontend/groups_list.html'

    def get_queryset(self):
        return FBGroup.objects.all()

    def get_context_data(self, **kwargs):
        context = super(GroupsList, self).get_context_data(**kwargs)

        for group in context['groups']:
            group.members = FBGroup.objects.count_members(group)

        return context


def GroupView(request, pk=None, template_name='frontend/group_view.html'):

    group = get_object_or_404(FBGroup, pk=pk)
    action = request.POST.get('action')

    if action:

        if request.user.is_authenticated():

            if action == 'join':

                membership = PersonInGroup()
                membership.group = group
                membership.person = request.user
                membership.save()

            elif action == 'leave':

                membership =\
                    PersonInGroup.objects.filter(
                        group=group, person=request.user)
                membership.delete()

            elif action == 'delete':

                print 'Delete is unimplemented!'  # TODO ?

        else:
            messages.error(request, 'You must log in to join a group')
            return HttpResponseRedirect(reverse_lazy('auth_login'))

    members = PersonInGroup.objects.filter(group=group)

    ids = []
    for member in members:
        ids.append(member.person.id)

    sightings = Sighting.objects.get_public().filter(user__id__in=ids)

    if request.user.is_authenticated():
        is_member = PersonInGroup.objects.filter(
            group=group,
            person=request.user
        ).exists()
        is_owner = group.owner == request.user
    else:
        is_member = False
        is_owner = False

    return render(
        request,
        template_name,
        {
            'pk': pk,
            'group': group,
            'members': members,
            'count': len(members),
            'sightings': sightings,
            'is_member': is_member,
            'is_owner': is_owner,
        }
    )


@login_required
def GroupEdit(request, pk=None, template_name='frontend/group_edit.html'):

    if pk:
        group = FBGroup.objects.get(pk=pk)
    else:
        group = FBGroup()

    if request.POST:

        form = FBGroupForm(request.POST, request.FILES, instance=group)

        if form.is_valid():
            form.save()

            if not pk:

                group.owner = request.user
                group.save()

                membership = PersonInGroup()
                membership.group = group
                membership.person = request.user
                membership.save()

            return HttpResponseRedirect(reverse_lazy('my_groups'))
    else:
        form = FBGroupForm(instance=group)

    context = {
        'form': form,
        'group': group,
        'pk': pk
    }

    return render(request, template_name, context)


@login_required
def GroupDelete(request, pk=None, template_name='frontend/group_delete.html'):

    group = get_object_or_404(FBGroup, pk=pk)
    members = PersonInGroup.objects.filter(group=group)

    if request.POST:

        group.delete()
        return HttpResponseRedirect(reverse_lazy('my_groups'))

    return render(
        request,
        template_name,
        {
            'pk': pk,
            'group': group,
            'members': members,
            'count': len(members),
        }
    )
