from django.urls import path

from main.views import delete_award, show_main, show_experience, show_award, create_award

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("award/", show_award, name="show_award"),
    path("award/add/", create_award, name="create_award"),
    path("award/<uuid:award_id>/delete/", delete_award, name="delete_award"),
]
