from django.db import models
from django.conf import settings
from django.template import Context, Template
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags, linebreaks
from django.contrib.auth.models import User

from registration.models import RegistrationProfile, RegistrationManager


class RedmapRegistrationManager(RegistrationManager):

    def create_inactive_user(self, username, email, password, site, first_name,
                             last_name, region, send_email=True):
        """
        Create a new, inactive ``User``, generate a
        ``RegistrationProfile`` and email its activation key to the
        ``User``, returning the new ``User``.

        By default, an activation email will be sent to the new
        user. To disable this, pass ``send_email=False``.

        """
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        profile = new_user.profile
        profile.region = region
        profile.save()

        registration_profile = self.create_profile(new_user)

        if send_email:
            registration_profile.send_activation_email(site)

        return new_user


class RedmapRegistrationProfile(RegistrationProfile):

    class Meta:
        proxy = True

manager = RedmapRegistrationManager()
manager.contribute_to_class(RedmapRegistrationProfile, 'objects')
