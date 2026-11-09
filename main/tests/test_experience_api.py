import uuid

from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient, APITestCase

from main.models import Experience


class ExperienceAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(username="owner", password="test-password")
        cls.editor = User.objects.create_user(username="editor", password="test-password")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.user = User.objects.create_user(username="regular", password="test-password")

    def setUp(self):
        self.item = Experience.objects.create(title="Research internship", category="research")
        self.list_url = "/api/v1/experiences/"
        self.detail_url = f"{self.list_url}{self.item.pk}/"
        self.star_url = f"{self.detail_url}star/"
        self.payload = {
            "title": "New experience", "description": "Description", "category": "internship",
            "keyfeatures": ["Feature"], "start_at": "2026-01-01", "ended_at": None,
        }

    def test_public_list_detail_search_and_safe_fields(self):
        response = self.client.get(self.list_url, {"title": "RESEARCH"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.item.pk))
        self.assertEqual(response.data[0]["star_count"], 0)
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("email", response.data[0])
        self.assertNotIn("password", response.data[0])
        self.assertEqual(self.client.get(self.list_url, {"title": "missing"}).data, [])
        self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        self.assertEqual(self.client.get(f"{self.list_url}{uuid.uuid4()}/").status_code, 404)

    def test_visitors_and_regular_users_cannot_write(self):
        for user in (None, self.user):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
                self.assertEqual(self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code, 403)
                self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
                self.assertEqual(Experience.objects.count(), 1)
                self.item.refresh_from_db()
                self.assertEqual(self.item.title, "Research internship")

    def test_editor_can_edit_but_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"title": "Edited"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Edited")
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.item.pk, title="Edited").exists())

    def test_owner_can_create_replace_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Experience.objects.filter(pk=response.data["id"]).exists())
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "New experience")
        self.assertEqual(self.client.delete(self.detail_url).status_code, 204)
        self.assertFalse(Experience.objects.filter(pk=self.item.pk).exists())

    def test_input_is_cleaned_and_invalid_values_are_rejected(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [({"title": "<b></b>"}, "title"),
                               ({"category": "unknown"}, "category"),
                               ({"keyfeatures": [{"bad": "value"}]}, "keyfeatures")]:
            with self.subTest(field=field):
                response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
                self.assertEqual(Experience.objects.count(), 1)
        response = self.client.post(self.list_url, {
            **self.payload, "title": " <b>Clean</b> ", "description": "<p>Text</p>",
            "keyfeatures": [" <em>Feature</em> "],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        created = Experience.objects.get(pk=response.data["id"])
        self.assertEqual((created.title, created.description, created.keyfeatures), ("Clean", "Text", ["Feature"]))

    def test_star_requires_login_and_uses_current_user(self):
        self.assertEqual(self.client.post(self.star_url, {}, format="json").status_code, 403)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.star_url, {"user": self.owner.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["star_count"], 1)
        self.assertTrue(response.data["is_starred"])
        self.assertTrue(self.item.starred_by.filter(pk=self.user.pk).exists())
        self.assertFalse(self.item.starred_by.filter(pk=self.owner.pk).exists())
        self.client.force_authenticate(user=self.owner)
        self.assertFalse(self.client.get(self.detail_url).data["is_starred"])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.star_url, {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(self.item.starred_by.exists())

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        self.assertEqual(client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(Experience.objects.count(), 1)
