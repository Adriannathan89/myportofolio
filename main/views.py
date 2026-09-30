import datetime

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import AwardForm, ExperienceForm, UserUpdateForm
from main.models import Award, Experience


# ------------------------------- User Authentication Views ----------------------------------
def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registration successful. You can now log in.")
        return redirect("main:login")

    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }
    return render(request, "register.html", context)


def show_login(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Login successful.")
        response = redirect("main:show_main")
        response.set_cookie(
            "last_login", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return response

    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }

    return render(request, "login.html", context)


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response


@login_required(login_url="main:login")
def show_user_profile(request):
    form = UserUpdateForm(
        request.POST if request.method == "POST" else None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if form.cleaned_data["new_password"]:
            update_session_auth_hash(request, user)
        messages.success(request, "Profile updated successfully.")
        return redirect("main:show_user_profile")

    context = {
        "name": "Adrian Nathanael Setiawan",
        "user": request.user,
        "form": form,
    }

    return render(request, "user_profile.html", context)


def show_main(request):
    last_login = request.COOKIES.get(
        "last_login", "belum ada sesi login / Cookie tidak ditemukan"
    )

    context = {
        "name": "Adrian Nathanael Setiawan",
        "npm": "2506591053",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "CS student at Universitas Indonesia. Currently exploring software development and data "
            "science. Also Building a Rust's Web Framework."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Adrian Nathanael Setiawan",
        "title_query": title_query,
        "form": ExperienceForm(),
    }
    return render(request, "experience.html", context)


def show_award(request):
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Adrian Nathanael Setiawan",
        "title_query": title_query,
        "form": AwardForm(),
    }
    return render(request, "award.html", context)


# ---------------------------------- Model Getter Filtering ----------------------------------
def get_awards_json(request):
    title_query = request.GET.get("title", "").strip()
    awards = Award.objects.prefetch_related("starred_by")

    if title_query:
        awards = awards.filter(title__icontains=title_query)

    data = []

    for award in awards:
        starred_users = list(award.starred_by.all())
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_usernames = ", ".join(user.username for user in starred_users)

        data.append(
            {
                "pk": str(award.id),
                "fields": {
                    "title": award.title,
                    "description": award.description or "",
                    "date_received": award.date_received.isoformat(),
                    "thumbnail": award.thumbnail or "",
                    "issuer": award.issuer or "",
                    "starred_by_names": starred_by_usernames,
                    "star_count": len(starred_users),
                    "is_starred": is_starred,
                },
            }
        )

    return JsonResponse(data, safe=False)


def get_experience_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    data = []
    for experience in experiences:
        data.append(
            {
                "pk": str(experience.id),
                "fields": {
                    "title": experience.title,
                    "description": experience.description or "",
                    "thumbnail": getattr(experience, "thumbnail", None),
                    "category_display": experience.get_category_display(),
                    "keyfeatures": experience.keyfeatures or [],
                    "start_at": experience.start_at.isoformat()
                    if experience.start_at
                    else None,
                    "ended_at": experience.ended_at.isoformat()
                    if experience.ended_at
                    else None,
                    "is_ongoing": experience.is_ongoing,
                },
            }
        )

    return JsonResponse(data, safe=False)


# ---------------------------------- Award Form Model CRUD  ----------------------------------
@login_required(login_url="main:login")
def create_award(request):
    form = AwardForm(request.POST if request.method == "POST" else None)

    if not request.user.has_perm("main.add_award"):
        raise PermissionDenied("You do not have permission to add awards.")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Award added successfully.")
        return redirect("main:show_award")
    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }

    return render(request, "award_form.html", context)

@require_POST
def create_award_ajax(request):
    if not request.user.has_perm("main.add_award"):
        return JsonResponse({"message": "You do not have permission to add awards."}, status=403)

    form = AwardForm(request.POST)
    if form.is_valid():
        award = form.save()
        return JsonResponse({
            "message": "Award added successfully.",
            "pk": str(award.id),
        }, status=201)
    else:
        return JsonResponse({"errors": form.errors}, status=400)

@login_required(login_url="main:login")
def update_award(request, award_id):
    if not request.user.has_perm("main.change_award"):
        raise PermissionDenied("You do not have permission to update awards.")

    award = get_object_or_404(Award, id=award_id)
    form = AwardForm(request.POST if request.method == "POST" else None, instance=award)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Award updated successfully.")
        return redirect("main:show_award")

    return render(
        request,
        "award_update_form.html",
        {
            "name": "Adrian Nathanael Setiawan",
            "form": form,
            "award": award,
        },
    )


@login_required(login_url="main:login")
@require_POST
def delete_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)

    if not request.user.has_perm("main.delete_award"):
        raise PermissionDenied("You do not have permission to delete awards.")

    award.delete()
    messages.success(request, "Award deleted successfully.")
    return redirect("main:show_award")


@login_required(login_url="main:login")
@require_POST
def toggle_star_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)

    if award.starred_by.filter(pk=request.user.pk).exists():
        award.starred_by.remove(request.user)
        messages.success(request, f"Your star was removed from {award.title}.")
    else:
        award.starred_by.add(request.user)
        messages.success(request, f"You starred {award.title}.")

    return redirect("main:show_award")


# ---------------------------------- Experience Form Model CRUD  ----------------------------------
@login_required(login_url="main:login")
def create_experience(request):
    if not request.user.has_perm("main.add_experience"):
        raise PermissionDenied("You do not have permission to add experiences.")

    form = ExperienceForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience added successfully.")
        return redirect("main:show_experience")
    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
    }

    return render(request, "experience_create_form.html", context)


@login_required(login_url="main:login")
def update_experience(request, experience_id):
    if not request.user.has_perm("main.change_experience"):
        raise PermissionDenied("You do not have permission to update experiences.")

    experience = get_object_or_404(Experience, id=experience_id)
    form = ExperienceForm(
        request.POST if request.method == "POST" else None, instance=experience
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience updated successfully.")
        return redirect("main:show_experience")
    context = {
        "name": "Adrian Nathanael Setiawan",
        "form": form,
        "experience": experience,
    }

    return render(request, "experience_update_form.html", context)


@login_required(login_url="main:login")
@require_POST
def delete_experience(request, experience_id):
    if not request.user.has_perm("main.delete_experience"):
        raise PermissionDenied("You do not have permission to delete experiences.")

    experience = get_object_or_404(Experience, id=experience_id)
    experience.delete()
    messages.success(request, "Experience deleted successfully.")
    return redirect("main:show_experience")
