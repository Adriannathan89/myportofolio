from django.urls import path
from rest_framework.authtoken import views as authtoken_views

from main import api_views

app_name = "api"

urlpatterns = [
    path("auth/token/", authtoken_views.obtain_auth_token, name="api_token_auth"),
    path("auth/logout/", api_views.api_logout, name="api_logout"),
    path("projects/", api_views.project_list, name="project_list"),
    path("projects/<uuid:project_id>/", api_views.project_detail, name="project_detail"),
    path("awards/", api_views.award_list, name="award_list"),
    path("awards/<uuid:award_id>/", api_views.award_detail, name="award_detail"),
    path("awards/<uuid:award_id>/star/", api_views.toggle_star_award, name="toggle_star_award"),
    path("experiences/", api_views.experience_list, name="experience_list"),
    path("experiences/<uuid:experience_id>/", api_views.experience_detail, name="experience_detail"),
    path("experiences/<uuid:experience_id>/star/", api_views.toggle_star_experience, name="toggle_star_experience"),
]