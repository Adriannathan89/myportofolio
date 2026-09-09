from django.shortcuts import render

from main.models import Experience


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