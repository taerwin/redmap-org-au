from celery import Celery
from datetime import date, timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django_facebook.models import OpenGraphShare
from redmapdb.models import Region, SightingTracking


celery = Celery('tasks')


@celery.task(name="process_stale_sightings", ignore_result=True)
def get_stale_sightings():

    global_admin = Group.objects.get(name="Administrators").user_set.all()[0]

    last_week = date.today() - timedelta(weeks=1)

    trackings = SightingTracking.active_assignments.filter(
        tracking_date__lte=last_week)

    for tracking in trackings:

        sighting = tracking.sighting

        sighting.reassign(global_admin, sighting.pick_expert(
        ), "Reassigning stale sighting")

        subject = '#%s - Stale Sighting' % sighting.pk
        from_email = settings.DEFAULT_FROM_EMAIL
        to = sighting.tracking.person.email
        if sighting.photo_url:
            image = 'http://' + Site.objects.get_current(
            ).domain + sighting.photo_url.url
        else:
            image = ''

        dictionary = {
            'species_name': sighting.species_name,
            'species_contact': sighting.tracking.person.first_name,
            'species_common_name': sighting.common_name,
            'domain': Site.objects.get_current().domain,
            'sighting_id': sighting.id,
            'image': image,
            'region': Region.objects.get(description='Tasmania'),
            'out_of_range': sighting.is_out_of_range,
        }
        text_content = render_to_string(
            'backend/email/text/stale_sighting.html', dictionary)
        html_content = render_to_string(
            'backend/email/html/stale_sighting.html', dictionary)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@celery.task
def send_facebook_opengraphshare(pk):
    share = OpenGraphShare.objects.get(pk=pk)
    result = share.send()
