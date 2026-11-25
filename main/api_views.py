from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import (
    Award,
    Experience,
    Project,
)
from main.permissions import (
    IsPortfolioOwnerOrEditorOrReadOnly,
    IsPortfolioOwnerOrReadOnly,
)
from main.serializers import (
    AwardSerializer,
    ExperienceSerializer,
    ProjectSerializer,
)

#---------------------------------------- Award Section Api Views ----------------------------------------#
@api_view(['GET', 'HEAD', 'POST'])
@permission_classes([IsPortfolioOwnerOrReadOnly, IsPortfolioOwnerOrEditorOrReadOnly])
def award_list(request):
    if request.method in ('GET', 'HEAD'):
        awards = Award.objects.prefetch_related('starred_by').order_by('title', 'id')
        title = request.query_params.get('title', '').strip()
        if title:
            awards = awards.filter(title__icontains=title)
        return Response(AwardSerializer(awards, many=True, context={'request': request}).data)

    serializer = AwardSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsPortfolioOwnerOrReadOnly, IsPortfolioOwnerOrEditorOrReadOnly])
def award_detail(request, award_id):
    award = get_object_or_404(Award.objects.prefetch_related('starred_by'), id=award_id)
    if request.method in ('GET', 'HEAD'):
        return Response(AwardSerializer(award, context={'request': request}).data)
    if request.method == 'DELETE':
        award.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = AwardSerializer(award, data=request.data, partial=request.method == 'PATCH',
                                 context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_star_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)
    if award.starred_by.filter(id=request.user.id).exists():
        award.starred_by.remove(request.user)
    else:
        award.starred_by.add(request.user)
    return Response(AwardSerializer(award, context={'request': request}).data)


#---------------------------------------- Experience Section Api Views ----------------------------------------#
@api_view(['GET', 'HEAD', 'POST'])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_list(request):
    if request.method in ('GET', 'HEAD'):
        experiences = Experience.objects.prefetch_related('starred_by').order_by('title', 'id')
        title = request.query_params.get('title', '').strip()
        if title:
            experiences = experiences.filter(title__icontains=title)
        return Response(ExperienceSerializer(experiences, many=True, context={'request': request}).data)

    serializer = ExperienceSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_detail(request, experience_id):
    experience = get_object_or_404(Experience, id=experience_id)
    if request.method in ('GET', 'HEAD'):
        return Response(ExperienceSerializer(experience, context={'request': request}).data)
    if request.method == 'DELETE':
        experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ExperienceSerializer(experience, data=request.data, partial=request.method == 'PATCH',
                                      context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_star_experience(request, experience_id):
    experience = get_object_or_404(Experience, id=experience_id)
    if experience.starred_by.filter(id=request.user.id).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)
    return Response(ExperienceSerializer(experience, context={'request': request}).data)


#---------------------------------------- Project Api Views ----------------------------------------#
@api_view(['GET', 'HEAD', 'POST'])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_list(request):
    if request.method in ('GET', 'HEAD'):
        projects = Project.objects.order_by('title', 'id')
        title = request.query_params.get('title', '').strip()
        if title:
            projects = projects.filter(title__icontains=title)
        return Response(ProjectSerializer(projects, many=True, context={'request': request}).data)

    serializer = ProjectSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method in ('GET', 'HEAD'):
        return Response(ProjectSerializer(project, context={'request': request}).data)
    if request.method == 'DELETE':
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ProjectSerializer(project, data=request.data, partial=request.method == 'PATCH',
                                   context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


#---------------------------------------- Auth Api Views ----------------------------------------#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    # request.auth is the Token instance for token-based requests; it is None
    # for session-based requests, in which case there is nothing to revoke.
    if request.auth is not None:
        request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
