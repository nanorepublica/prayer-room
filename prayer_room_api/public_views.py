from collections import defaultdict

from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from .forms import PrayerSubmitForm
from .models import (
    HomePageContent,
    Location,
    PrayerInspiration,
    PrayerPraiseRequest,
    PrayerResource,
    Setting,
)


class LandingView(TemplateView):
    template_name = "prayer_wall/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = {
            item.key: item.value for item in HomePageContent.objects.all()
        }
        context["inspiration"] = PrayerInspiration.objects.order_by("?").first()
        context["settings"] = {
            item.name: item for item in Setting.objects.all()
        }
        return context


class PrayerWallView(ListView):
    template_name = "prayer_wall/wall.html"
    context_object_name = "prayers"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            PrayerPraiseRequest.objects.filter(
                approved_at__isnull=False, archived_at__isnull=True
            )
            .select_related("location")
            .order_by("-created_at")
        )
        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location__slug=location)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locations"] = Location.objects.filter(is_active=True)
        context["current_location"] = self.request.GET.get("location", "")
        return context

    def get_template_names(self):
        if self.request.htmx:
            return ["prayer_wall/_prayer_list.html"]
        return [self.template_name]


class PrayPrayerView(View):
    def post(self, request, pk):
        prayer = get_object_or_404(
            PrayerPraiseRequest,
            pk=pk,
            approved_at__isnull=False,
            archived_at__isnull=True,
        )
        prayer.prayer_count = F("prayer_count") + 1
        prayer.save(update_fields=["prayer_count"])
        prayer.refresh_from_db()
        return render(request, "prayer_wall/_prayer_card.html", {"prayer": prayer})


class FlagPrayerView(View):
    def post(self, request, pk):
        prayer = get_object_or_404(
            PrayerPraiseRequest,
            pk=pk,
            approved_at__isnull=False,
            archived_at__isnull=True,
        )
        prayer.flagged_at = now()
        prayer.save(update_fields=["flagged_at"])
        return HttpResponse(
            '<p class="text-sm text-stone-500 dark:text-stone-400 italic">Thank you for letting us know.</p>'
        )


class SubmitPrayerView(FormView):
    template_name = "prayer_wall/submit.html"
    form_class = PrayerSubmitForm

    def form_valid(self, form):
        prayer = form.save(commit=False)
        prayer.created_at = now()
        prayer.apply_banned_word_actions()
        prayer.save()
        if self.request.htmx:
            return render(self.request, "prayer_wall/_submit_success.html")
        return redirect("prayer-wall")

    def form_invalid(self, form):
        if self.request.htmx:
            return render(
                self.request,
                "prayer_wall/submit.html",
                {"form": form},
            )
        return super().form_invalid(form)


class ResourcesView(TemplateView):
    template_name = "prayer_wall/resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resources = (
            PrayerResource.objects.filter(is_active=True)
            .select_related("section")
            .order_by("sort_order")
        )
        sections = defaultdict(list)
        standalone = []
        for resource in resources:
            if resource.resource_type == PrayerResource.ResourceType.SECTION:
                sections[resource.pk]  # ensure section key exists
            elif resource.section_id:
                sections[resource.section_id].append(resource)
            else:
                standalone.append(resource)

        section_objects = {
            r.pk: r for r in resources
            if r.resource_type == PrayerResource.ResourceType.SECTION
        }
        context["grouped_resources"] = [
            (section_objects[sid], items)
            for sid, items in sections.items()
            if sid in section_objects
        ]
        context["standalone_resources"] = standalone
        return context
