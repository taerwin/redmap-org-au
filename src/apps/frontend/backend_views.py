from common.util import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, HttpResponseRedirect, render

from frontend.forms import AddFaqForm, AddSponsorForm, AddSponsorCategoryForm
from frontend.models import Faq, Sponsor, SponsorCategory


login_url = reverse_lazy('auth_login')


@login_required
@permission_required('frontend.change_sponsor')
def SponsorIndex(request, template_name="backend/sponsor_index.html"):

    sponsors = Sponsor.objects.all()

    return render(
        request,
        template_name,
        {'sponsors_list': sponsors}
    )


@login_required
@permission_required('frontend.change_sponsor')
def SponsorAdd(request, pk=None, template_name="backend/sponsor_add.html"):

    if pk:
        sponsor = get_object_or_404(Sponsor, pk=pk)
    else:
        sponsor = Sponsor()

    if request.POST:
        form = AddSponsorForm(request.POST, request.FILES, instance=sponsor)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('sponsor_index'))
    else:
        form = AddSponsorForm(instance=sponsor)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('frontend.delete_sponsor')
def SponsorDelete(request, pk=None, template_name="backend/sponsor_delete.html"):

    sponsor = Sponsor.objects.get(pk=pk)

    if pk and request.POST:
        sponsor.delete()
        return HttpResponseRedirect(reverse_lazy('sponsor_index'))

    return render(
        request,
        template_name,
        {'sponsor': sponsor}
    )

@login_required
@permission_required('frontend.change_faq')
def FaqIndex(request, template_name="backend/faq_index.html"):

    faqs = Faq.objects.all()

    return render(
        request,
        template_name,
        {'faqs': faqs}
    )

@login_required
@permission_required('frontend.change_faq')
def FaqEdit(request, pk=None, template_name="backend/faq_edit.html"):

    if pk:
        faq = get_object_or_404(Faq, pk=pk)
    else:
        faq = Faq()

    if request.POST:
        form = AddFaqForm(request.POST, request.FILES, instance=faq)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('faq_index'))
    else:
        form = AddFaqForm(instance=faq)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )

@login_required
@permission_required('frontend.delete_faq')
def FaqDelete(request, pk=None, template_name="backend/faq_delete.html"):

    faq = Faq.objects.get(pk=pk)

    if pk and request.POST:
        faq.delete()
        return HttpResponseRedirect(reverse_lazy('faq_index'))

    return render(
        request,
        template_name,
        {'faq': faq}
    )


@login_required
@permission_required('frontend.change_sponsorcategory')
def SponsorCategoryIndex(request, template_name="backend/sponsor_category_index.html"):

    categories = SponsorCategory.objects.all()

    return render(
        request,
        template_name,
        {'sponsor_categories': categories}
    )


@login_required
@permission_required('frontend.change_sponsorcategory')
def SponsorCategoryEdit(request, pk=None, template_name="backend/sponsor_category_edit.html"):

    if pk:
        category = get_object_or_404(SponsorCategory, pk=pk)
    else:
        category = SponsorCategory()

    if request.POST:
        form = AddSponsorCategoryForm(request.POST, request.FILES, instance=category)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy('sponsor_category_index'))
    else:
        form = AddSponsorCategoryForm(instance=category)

    return render(
        request,
        template_name,
        {'form': form, 'pk': pk}
    )


@login_required
@permission_required('frontend.delete_sponsorcategory')
def SponsorCategoryDelete(request, pk=None, template_name="backend/sponsor_category_delete.html"):

    category = SponsorCategory.objects.get(pk=pk)

    if pk and request.POST:
        category.delete()
        return HttpResponseRedirect(reverse_lazy('sponsor_category_index'))

    return render(
        request,
        template_name,
        {'category': category}
    )
