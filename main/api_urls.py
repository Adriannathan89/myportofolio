from django.urls import path

from main import api_views

app_name = "api"

urlpatterns = [
    path("awards/", api_views.award_list, name="award_list"),
    path("awards/<uuid:award_id>/", api_views.award_detail, name="award_detail"),
    path("awards/<uuid:award_id>/star/", api_views.toggle_star_award, name="toggle_star_award"),
    path("experiences/", api_views.experience_list, name="experience_list"),
    path("experiences/<uuid:experience_id>/", api_views.experience_detail, name="experience_detail"),
    path("experiences/<uuid:experience_id>/star/", api_views.toggle_star_experience, name="toggle_star_experience"),
]