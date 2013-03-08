'''
Created on 12/10/2012

@author: thomas
'''
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.sites.models import Site


def alert_reassignee(sighting, by_user, to_user, comment):

    subject = 'Sighting #%s has been reassigned to you' % sighting.pk
    from_email = sighting.region.email
    to = to_user.email

    dictionary = {
        'user': to_user,
        'previous_user': by_user,
        'comment': comment,
        'sighting': sighting,
        'domain': Site.objects.get_current().domain,
    }

    text_content = render_to_string(
        'backend/email/text/reassign.html', dictionary)
    html_content = render_to_string(
        'backend/email/html/reassign.html', dictionary)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def alert_assignee(tracker, comment):
    "Email the expert and advise them they've been assigned the sighting"

    subject = '#%s - New sighting' % tracker.sighting.pk
    from_email = tracker.sighting.region.email
    to = tracker.person.email

    if tracker.sighting.photo_url:
        image = 'http://' + Site.objects.get_current(
        ).domain + tracker.sighting.photo_url.url
    else:
        image = ''

    dictionary = {
        'species_name': tracker.sighting.species_name,
        'species_contact': tracker.person.first_name,
        'species_common_name': tracker.sighting.common_name,
        'domain': Site.objects.get_current().domain,
        'sighting_id': tracker.sighting.id,
        'image': image,
        'region': tracker.sighting.region.description,
        'out_of_range': tracker.sighting.is_out_of_range,
        'comment': comment
    }

    text_content = render_to_string(
        'frontend/email/text/add_sighting.html', dictionary)

    html_content = render_to_string(
        'frontend/email/html/add_sighting.html', dictionary)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def thank_sighter(sighting):
    '''
    Send a thank you message to a sighter, after they log a sighting. This will
    include the basic sighting details, and an estimated time that the sighting
    will be validated within.
    '''
    from cms.models import CopyBlock
    import re

    subject = 'Your %s sighting has been logged' % sighting.common_name
    from_email = sighting.region.email
    to = sighting.user.email

    REPLACEMENTS = dict([
        ('{sighter}', sighting.user.profile.display_name),
        ('{species}', '%s (%s)' % (sighting.common_name, sighting.species_name)),
    ])
    r = re.compile('|'.join(REPLACEMENTS.keys()))

    def replacer(m):
        return REPLACEMENTS[m.group(0)]

    text_content, created = CopyBlock.objects.get_or_create(
        slug='thank_sighter_email_template_text',
        defaults={'text': 'Hi {sighter},\n\nThanks for your {species} sighting! Our scientists will take a look soon and validate this sighting for you. This usually happens within 7 days.\n\nRegards,\nRedmap'})

    html_content, created = CopyBlock.objects.get_or_create(
        slug='thank_sighter_email_template_html',
        defaults={'text': '<p>Hi {sighter},</p><p>Thanks for your {species} sighting! Our scientists will take a look soon and validate this sighting for you. This usually happens within 7 days.</p><p>Regards,<br>Redmap</p>'})

    text_content = r.sub(replacer, text_content.text)
    html_content = r.sub(replacer, html_content.text)

    text_content = strip_tags(text_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
