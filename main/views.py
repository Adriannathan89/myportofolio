from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import AwardForm
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
    context = {
        "name": "Adrian Nathanael Setiawan",
        "award_list": Award.objects.all(),
    }
    return render(request, "award.html", context)

def create_award(request):
    form = AwardForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("main:show_award")
    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }

    return render(request, "award_form.html", context)


@require_POST
def delete_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)
    award.delete()
    return redirect("main:show_award")
