from django.urls import path

from main.views import (
    create_award,
    create_experience,
    delete_award,
    delete_experience,
    get_awards_json,
    show_login,
    show_award,
    show_experience,
    show_main,
    show_user_profile,
    update_experience,
    update_award,
    logout_view,
    register,
    toggle_star_award,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/add/", create_experience, name="create_experience"),
    path("experience/<uuid:experience_id>/", update_experience, name="update_experience"),
    path("experience/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("award/", show_award, name="show_award"),
    path("award/add/", create_award, name="create_award"),
    path("award/<uuid:award_id>/", update_award, name="update_award"),
    path("award/<uuid:award_id>/delete/", delete_award, name="delete_award"),
    path("award/<uuid:award_id>/toggle-star/", toggle_star_award, name="toggle_star_award"),
    path("api/awards/", get_awards_json, name="get_awards_json"),
    path("register/", register, name="register"),
    path("profile/", show_user_profile, name="show_user_profile"),
    path("login/", show_login, name="login"),
    path("logout/", logout_view, name="logout"),
]
