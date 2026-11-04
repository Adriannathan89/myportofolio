import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Award


class AwardAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser('owner', 'owner@example.com', 'test-password')
        self.visitor = User.objects.create_user('visitor', password='test-password')
        self.award = Award.objects.create(title='Scholarship', date_received='2026-09-16')
        self.list_url = reverse('api:award_list')
        self.detail_url = reverse('api:award_detail', args=[self.award.pk])
        self.star_url = reverse('api:toggle_star_award', args=[self.award.pk])
        self.payload = {'title': 'Prize', 'description': 'Awarded', 'issuer': 'School',
                        'thumbnail': '/static/img/award.png', 'date_received': '2026-10-01'}

    def test_public_list_detail_and_search(self):
        response = self.client.get(self.list_url, {'title': 'SCHOL'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], str(self.award.pk))
        self.assertEqual(response.data[0]['star_count'], 0)
        self.assertFalse(response.data[0]['is_starred'])
        self.assertNotIn('fields', response.data[0])
        self.assertEqual(self.client.get(self.list_url, {'title': 'missing'}).data, [])
        self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        self.assertEqual(self.client.head(self.list_url).status_code, 200)
        self.assertEqual(self.client.head(self.detail_url).status_code, 200)
        self.assertEqual(self.client.get(reverse('api:award_detail', args=[uuid.uuid4()])).status_code, 404)

    def test_owner_create_update_and_delete(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.list_url, self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Award.objects.filter(pk=response.data['id']).exists())
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'Changed'}, format='json').status_code, 200)
        self.assertEqual(self.client.put(self.detail_url, {'title': 'Incomplete'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertFalse(Award.objects.filter(pk=self.award.pk).exists())

    def test_guest_and_visitor_cannot_manage_awards(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format='json').status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {'title': 'Changed'}, format='json').status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Scholarship')
        self.assertEqual(Award.objects.count(), 1)

    def test_editor_can_update_but_not_create_or_delete(self):
        self.visitor.groups.add(Group.objects.get(name='Editor'))
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.client.patch(self.detail_url, {'title': 'Edited'}, format='json').status_code, 200)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Edited')
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, 'Prize')
        self.assertEqual(self.client.post(self.list_url, self.payload, format='json').status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)

    def test_validation_and_read_only_star_fields(self):
        self.client.force_authenticate(self.owner)
        for changes, field in [({'title': '   '}, 'title'), ({'title': '<img src="x">'}, 'title'),
                               ({'thumbnail': 'javascript:alert(1)'}, 'thumbnail'),
                               ({'thumbnail': '//example.com/image.png'}, 'thumbnail')]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        response = self.client.post(self.list_url, {**self.payload, 'starred_by': [self.visitor.pk],
                                    'star_count': 99, 'is_starred': True}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['star_count'], 0)
        self.assertFalse(response.data['is_starred'])

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.client.force_authenticate(self.visitor)
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_starred'])
        self.assertEqual(response.data['star_count'], 1)
        self.assertEqual(response.data['starred_by_names'], 'visitor')
        response = self.client.post(self.star_url)
        self.assertFalse(response.data['is_starred'])
        self.assertEqual(response.data['star_count'], 0)

    def test_session_csrf_token_from_award_page(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='visitor', password='test-password'))
        self.assertEqual(client.post(self.star_url).status_code, 403)
        self.assertEqual(client.get(reverse('main:show_award')).status_code, 200)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.star_url, HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_session_create_with_csrf_and_wrong_method(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='owner', password='test-password'))
        self.assertEqual(client.post(self.list_url, self.payload, format='json').status_code, 403)
        client.get(reverse('main:show_award'))
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.list_url, self.payload, format='json', HTTP_X_CSRFTOKEN=token).status_code, 201)
        self.assertEqual(client.delete(self.list_url, HTTP_X_CSRFTOKEN=token).status_code, 405)
