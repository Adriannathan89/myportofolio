import secrets

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import AwardActionKeyForm, AwardForm
from main.models import Award, Experience


def show_main(request):
    context = {
        "name": "Adrian Nathanael Setiawan",
        "npm": "2506591053",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "CS student at Universitas Indonesia. Currently exploring software development and data "
            "science. Also Building a Rust's Web Framework."
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Adrian Nathanael Setiawan",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_award(request):
    json_response = get_awards_json(request)
    award_list = [
        item.object
        for item in serializers.deserialize("json", json_response.content.decode("utf-8"))
    ]
    context = {
        "name": "Adrian Nathanael Setiawan",
        "award_list": award_list,
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "award.html", context)


def get_awards_json(request):
    title_query = request.GET.get("title", "").strip()
    awards = Award.objects.all()

    if title_query:
        awards = awards.filter(title__icontains=title_query)

    awards_json = serializers.serialize("json", awards)
    return HttpResponse(awards_json, content_type="application/json")


def _is_valid_action_key(action_key):
    configured_key = settings.AWARD_ACTION_KEY
    return bool(configured_key) and secrets.compare_digest(action_key, configured_key)

def create_award(request):
    form = AwardForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid() and _is_valid_action_key(form.cleaned_data["action_key"]):
        form.save()
        messages.success(request, "Award added successfully.")
        return redirect("main:show_award")
    if request.method == "POST" and form.is_valid():
        form.add_error("action_key", "Invalid action key.")
    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }

    return render(request, "award_form.html", context)


@require_POST
def delete_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)
    form = AwardActionKeyForm(request.POST)

    if not form.is_valid() or not _is_valid_action_key(form.cleaned_data.get("action_key", "")):
        messages.error(request, "Invalid action key.")
        return redirect("main:show_award")

    award.delete()
    messages.success(request, "Award deleted successfully.")
    return redirect("main:show_award")
