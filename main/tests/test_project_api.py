from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from main.models import Project


class ProjectAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin', password='admin-pass-123', email='admin@example.com'
        )
        cls.project = Project.objects.create(
            title='Portfolio Site',
            description='Django portfolio',
            tech_stack='Django, DRF',
            project_url='https://example.com',
        )
        cls.list_url = '/api/v1/projects/'
        cls.detail_url = f'/api/v1/projects/{cls.project.id}/'
        cls.payload = {
            'title': 'Flutter App',
            'description': 'Mobile client',
            'tech_stack': 'Flutter',
            'project_url': 'https://example.org',
            'project_image_url': '',
        }

    def test_public_list_and_detail_use_snake_case_fields(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['tech_stack'], 'Django, DRF')

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.project.id))

    def test_anonymous_write_is_unauthorized(self):
        self.assertEqual(self.client.post(self.list_url, self.payload, format='json').status_code, 401)
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'X'}, format='json').status_code, 401)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 401)
        self.assertEqual(Project.objects.count(), 1)

    def test_token_superuser_can_create_update_and_delete(self):
        token = self.client.post(
            '/api/v1/auth/token/',
            {'username': 'admin', 'password': 'admin-pass-123'},
            format='json',
        ).data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_url = f"{self.list_url}{response.data['id']}/"

        response = self.client.patch(created_url, {'title': 'Renamed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Renamed')

        self.assertEqual(self.client.delete(created_url).status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_revokes_token(self):
        token = self.client.post(
            '/api/v1/auth/token/',
            {'username': 'admin', 'password': 'admin-pass-123'},
            format='json',
        ).data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(key=token).exists())

        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
