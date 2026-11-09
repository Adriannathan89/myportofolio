from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import (
    Award,
    Experience,
)
from main.permissions import (
    IsPortfolioOwnerOrEditorOrReadOnly,
    IsPortfolioOwnerOrReadOnly,
)
from main.serializers import (
    AwardSerializer,
    ExperienceSerializer,
)

#---------------------------------------- Award Section Api Views ----------------------------------------#
@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
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
@authentication_classes([SessionAuthentication])
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
@authentication_classes([SessionAuthentication])
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
@authentication_classes([SessionAuthentication])
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
@authentication_classes([SessionAuthentication])
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
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def toggle_star_experience(request, experience_id):
    experience = get_object_or_404(Experience, id=experience_id)
    if experience.starred_by.filter(id=request.user.id).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)
    return Response(ExperienceSerializer(experience, context={'request': request}).data)
