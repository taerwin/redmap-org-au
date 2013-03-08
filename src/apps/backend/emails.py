'''
Created on 12/10/2012

@author: thomas
'''
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.models import Site


def advise_scientist_promotion(user):
    """Send an email to the user advising of a promotion to the Scientists group"""
    subject = 'REDMAP Promotion to Scientist'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    payload = {
        'user': user,
        'site': Site.objects.get_current(),
    }

    body = render_to_string('backend/email/text/scientist_promotion.html', payload)
    email = EmailMessage(subject, body, from_email, [to_email])
    email.send()


def advise_regional_admin_promotion(user):
    """Send an email to the user advising of a promotion to the Administrators group"""
    subject = 'REDMAP Promotion to Regional Administrator'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    payload = {
        'user': user,
        'site': Site.objects.get_current(),
    }

    body = render_to_string('backend/email/text/regional_admin_promotion.html', payload)
    email = EmailMessage(subject, body, from_email, [to_email])
    email.send()
