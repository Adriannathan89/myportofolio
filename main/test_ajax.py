from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from main.models import Award, Experience


class ExperienceAjaxTest(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_superuser(username="ajax_admin")
        self.editor = users.objects.create_user(username="ajax_editor")
        self.editor.groups.add(Group.objects.get(name="Editor"))
        self.regular = users.objects.create_user(username="ajax_regular")
        self.experience = Experience.objects.create(title="Original", category="research")
        self.create_url = "/experience/add-ajax/"
        self.update_url = f"/experience/{self.experience.pk}/update-ajax/"
        self.data = {
            "title": "<b>Research internship</b>",
            "description": "<p>Studied software.</p>",
            "category": "internship",
            "keyfeatures": '["<em>Published results</em>"]',
            "start_at": "2026-09-01",
            "ended_at": "",
        }

    def test_admin_creates_sanitized_experience_with_201(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.create_url, self.data)
        self.assertEqual(response.status_code, 201)
        created = Experience.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.title, "Research internship")
        self.assertEqual(created.description, "Studied software.")
        self.assertEqual(created.keyfeatures, ["Published results"])
        self.assertEqual(created.category, "internship")
        self.assertTrue(created.is_ongoing)

    def test_create_rejects_invalid_input_without_saving(self):
        self.client.force_login(self.admin)
        for changes, field in [({"title": ""}, "title"),
                               ({"category": "unknown"}, "category"),
                               ({"keyfeatures": '[{"bad": "value"}]'}, "keyfeatures"),
                               ({"start_at": "invalid-date"}, "start_at")]:
            with self.subTest(field=field):
                response = self.client.post(self.create_url, {**self.data, **changes})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])
                self.assertEqual(Experience.objects.count(), 1)

    def test_editor_regular_and_visitor_cannot_create(self):
        for user in (None, self.regular, self.editor):
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                response = self.client.post(self.create_url, self.data)
                self.assertEqual(response.status_code, 403)
                self.assertIn("message", response.json())
        self.assertEqual(Experience.objects.count(), 1)

    def test_editor_and_admin_update_with_200(self):
        for user in (self.editor, self.admin):
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.post(self.update_url, self.data)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["pk"], str(self.experience.pk))
                self.experience.refresh_from_db()
                self.assertEqual(self.experience.title, "Research internship")
                self.assertEqual(self.experience.description, "Studied software.")
                self.assertEqual(self.experience.keyfeatures, ["Published results"])

    def test_invalid_update_preserves_saved_values(self):
        self.client.force_login(self.editor)
        response = self.client.post(self.update_url, {**self.data, "title": "<b></b>"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Original")

    def test_regular_and_visitor_cannot_update(self):
        for user in (None, self.regular):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                response = self.client.post(self.update_url, self.data)
                self.assertEqual(response.status_code, 403)
                self.assertIn("message", response.json())
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Original")

    def test_missing_experience_returns_json_404(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            "/experience/00000000-0000-0000-0000-000000000000/update-ajax/", self.data
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIn("message", response.json())

    def test_get_cannot_write(self):
        self.client.force_login(self.admin)
        for url in (self.create_url, self.update_url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_csrf_required_and_modal_token_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in (self.create_url, self.update_url):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, self.data).status_code, 403)
        page = client.get(reverse("main:create_experience"))
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post(self.create_url, {**self.data, "csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 201)
        response = client.post(self.update_url, self.data, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_json_includes_raw_category_for_prefilling_edit_form(self):
        response = self.client.get(reverse("main:get_experience_json"))
        self.assertEqual(response.json()[0]["fields"]["category"], "research")


class AjaxReadAndAwardTest(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_superuser(username="read_admin")
        self.editor = users.objects.create_user(username="read_editor")
        self.editor.groups.add(Group.objects.get(name="Editor"))
        self.regular = users.objects.create_user(username="read_regular")
        self.award = Award.objects.create(title="Research prize", date_received="2026-09-01")
        self.award.starred_by.add(self.regular)
        Experience.objects.create(title="Research internship")

    def test_lists_and_search_are_public_for_all_roles(self):
        for user in (None, self.regular, self.editor, self.admin):
            self.client.logout()
            if user:
                self.client.force_login(user)
            for page, endpoint in (("show_award", "get_awards_json"),
                                   ("show_experience", "get_experience_json")):
                with self.subTest(user=user, page=page):
                    self.assertEqual(self.client.get(reverse(f"main:{page}")).status_code, 200)
                    response = self.client.get(reverse(f"main:{endpoint}"), {"title": "RESEARCH"})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(len(response.json()), 1)
                    empty = self.client.get(reverse(f"main:{endpoint}"), {"title": "missing"})
                    self.assertEqual(empty.json(), [])

    def test_award_json_includes_count_and_current_user_star_status(self):
        for user, expected in ((None, False), (self.regular, True), (self.editor, False)):
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.get(reverse("main:get_awards_json"))
            fields = response.json()[0]["fields"]
            self.assertEqual(fields["star_count"], 1)
            self.assertEqual(fields["is_starred"], expected)

    def test_award_create_ajax_permissions_validation_and_csrf(self):
        url = reverse("main:create_award_ajax")
        data = {"title": "<b>New prize</b>", "date_received": "2026-09-20"}
        for user in (None, self.regular, self.editor):
            self.client.logout()
            if user:
                self.client.force_login(user)
            self.assertEqual(self.client.post(url, data).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(url, data).status_code, 403)
        client.get(reverse("main:show_award"))
        token = client.cookies["csrftoken"].value
        invalid = client.post(url, {**data, "title": ""}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("title", invalid.json()["errors"])
        valid = client.post(url, data, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(valid.status_code, 201)
        self.assertEqual(Award.objects.get(pk=valid.json()["pk"]).title, "New prize")
