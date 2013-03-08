from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView
from backend.views import *
from redmapdb.models import *

urlpatterns = patterns(
    'backend',
    url(r'^verify/(?P<pk>\d+)/$', scientist_verify_wizard,
        name='verify_sightings'),

    url(r'^$', Dashboard.as_view(), name='dashboard'),

    url(r'^sightings/$', ActiveSightingList.as_view(),
        name="sightings_unvalidated"),
    url(r'^sightings/past/$', MySightingList.as_view(), name="sightings_past"),
    url(r'^sightings/all/$', AllSightingsList.as_view(),
        name="sightings_list"),
    url(r'^sightings/edit/(?P<pk>\d+)/$', SightingEdit, name='sighting_edit'),
    url(r'^sightings/delete/(?P<pk>\d+)/$', SightingDelete,
        name='sighting_delete'),
    url(r'^sightings/reassign/(?P<pk>\d+)/$', SightingReassign,
        name='sighting_reassign'),
    url(r'^sightings/spam/(?P<pk>\d+)/$', SightingSpam, name='sighting_spam'),

    url(r'^experts/assignments/$', manage_experts.as_view(),
        name='manage_experts'),

    url(r'^experts/assignments/add/$', AddSpeciesExpert, name='add_expert'),

    url(r'^experts/assignments/edit/(?P<pk>\d+)/$', AddSpeciesExpert,
        name='edit_expert'),

    url(r'^experts/assignments/delete/(?P<pk>\d+)/$',
        DeleteSpeciesExpert, name='delete_expert'),

    url(r'^experts/allocations/$', AdministratorAllocations.as_view(),
        name='administrator_allocations'),
    url(r'^experts/allocations/add/$', AdministratorAllocationEdit,
        name='administrator_allocation_add'),
    url(r'^experts/allocations/edit/(?P<pk>\d+)/$',
        AdministratorAllocationEdit, name='administrator_allocation_edit'),
    url(r'^experts/allocations/delete/(?P<pk>\d+)/$', AdministratorAllocationDelete, name='administrator_allocation_delete'),

    url(r'^experts/rules/$', validation_rules,
        name='validation_rules'),
    url(r'^experts/rules/add/$', add_validation_rule,
        name='add_validation_rule'),
    url(r'^experts/rules/edit/(?P<pk>\d+)/$', edit_validation_rule,
        name='edit_validation_rule'),
    url(r'^experts/rules/delete/(?P<pk>\d+)/$', delete_validation_rule,
        name='delete_validation_rule'),

    url(r'^experts/templates/$', EmailTemplates,
        name='manage_email_templates'),
    url(r'^experts/templates/add/$', AddEmailTemplate,
        name='add_email_template'),
    url(r'^experts/templates/edit/(?P<pk>\d+)/$', AddEmailTemplate,
        name='edit_email_template'),
    url(r'^experts/templates/delete/(?P<pk>\d+)/$',
        DeleteEmailTemplate, name='delete_email_template'),

    url(r'^experts/conditions/$', ValidationConditions,
        name='validation_conditions'),
    url(r'^experts/conditions/add/$', ValidationConditionAdd,
        name='validation_condition_add'),
    url(r'^experts/conditions/edit/(?P<pk>\d+)/$',
        ValidationConditionAdd, name='validation_condition_edit'),
    url(r'^experts/conditions/delete/(?P<pk>\d+)/$',
        ValidationConditionDelete, name='validation_condition_delete'),



    url(r'^admin/members/$', MemberIndex.as_view(), name="member_index"),
    url(r'^admin/members/add/$', MemberAdd, name='member_add'),
    url(r'^admin/members/edit/(?P<pk>\d+)/$', MemberAdd, name='member_edit'),
    url(r'^admin/members/delete/(?P<pk>\d+)/$', MemberDelete,
        name='member_delete'),
    url(r'^admin/members/resend-activation/(?P<user_id>\d+)/$',
        resend_member_activation, name='member_resend_activation'),

    url(r'^admin/scientists/$', ScientistIndex.as_view(),
        name='scientist_index'),
    url(r'^admin/scientists/add/$', AddScientist, name='add_scientist'),
    url(r'^admin/scientists/delete/(?P<pk>\d+)/$', DeleteScientist,
        name='delete_scientist'),

    url(r'^admin/administrators/$', RegionalAdministrators.as_view(),
        name='regional_administrators'),
    url(r'^admin/administrators/add/$', RegionalAdministratorAdd,
        name='regional_administrator_add'),
    url(r'^admin/administrators/delete/(?P<pk>\d+)/$',
        RegionalAdministratorDelete, name='regional_administrator_delete'),

    url(r'^admin/organisations/$', OrganisationIndex.as_view(),
        name="organisation_index"),
    url(r'^admin/organisations/add/$', OrganisationAdd,
        name='organisation_add'),
    url(r'^admin/organisations/edit/(?P<pk>\d+)/$', OrganisationAdd,
        name='organisation_edit'),
    url(r'^admin/organisations/delete/(?P<pk>\d+)/$',
        OrganisationDelete, name='organisation_delete'),

    url(r'^admin/beta/$', BetaInvites.as_view(), name="beta_invites"),
    url(r'^admin/beta/send/(?P<pk>\d+)/$', BetaSendInvite,
        name='beta_send_invite'),

)
