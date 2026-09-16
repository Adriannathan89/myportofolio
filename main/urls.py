from django.urls import path

from main.views import (
    create_award,
    delete_award,
    get_awards_json,
    show_award,
    show_experience,
    show_main,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("award/", show_award, name="show_award"),
    path("award/add/", create_award, name="create_award"),
    path("award/<uuid:award_id>/delete/", delete_award, name="delete_award"),
    path("api/awards/", get_awards_json, name="get_awards_json"),
]
