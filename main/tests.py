from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from main.forms import AwardForm, ExperienceForm
from main.models import Award, Experience


class XSSInputValidationTest(SimpleTestCase):
    def test_award_form_strips_tags_from_displayed_text_fields(self):
        form = AwardForm(
            data={
                "title": "<strong>Hackathon Winner</strong>",
                "description": "<p>Won first place.</p>",
                "thumbnail": "/static/img/award.png",
                "issuer": "<em>Tech Community</em>",
                "date_received": "2026-09-30",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["title"], "Hackathon Winner")
        self.assertEqual(form.cleaned_data["description"], "Won first place.")
        self.assertEqual(form.cleaned_data["issuer"], "Tech Community")

    def test_award_form_rejects_title_containing_only_html(self):
        form = AwardForm(
            data={
                "title": '<img src="x" onerror="alert(1)">',
                "date_received": "2026-09-30",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_award_form_only_accepts_local_or_http_thumbnail_urls(self):
        safe_form = AwardForm(
            data={
                "title": "Certificate",
                "thumbnail": "https://example.com/certificate.png",
                "date_received": "2026-09-30",
            }
        )
        self.assertTrue(safe_form.is_valid(), safe_form.errors)

        for thumbnail in (
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "//example.com/certificate.png",
        ):
            with self.subTest(thumbnail=thumbnail):
                form = AwardForm(
                    data={
                        "title": "Certificate",
                        "thumbnail": thumbnail,
                        "date_received": "2026-09-30",
                    }
                )
                self.assertFalse(form.is_valid())
                self.assertIn("thumbnail", form.errors)

    def test_experience_form_strips_tags_from_text_and_key_features(self):
        form = ExperienceForm(
            data={
                "title": "<strong>Research Assistant</strong>",
                "description": "<p>Analyzed software quality.</p>",
                "category": "research",
                "keyfeatures": '["<b>Reviewed code</b>", "<i>Prepared reports</i>"]',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["title"], "Research Assistant")
        self.assertEqual(form.cleaned_data["description"], "Analyzed software quality.")
        self.assertEqual(
            form.cleaned_data["keyfeatures"],
            ["Reviewed code", "Prepared reports"],
        )

    def test_experience_form_rejects_title_containing_only_html(self):
        form = ExperienceForm(
            data={
                "title": '<img src="x" onerror="alert(1)">',
                "category": "research",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_experience_form_rejects_non_text_key_features(self):
        form = ExperienceForm(
            data={
                "title": "Research Assistant",
                "category": "research",
                "keyfeatures": '["Valid feature", {"unexpected": "object"}]',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("keyfeatures", form.errors)


class AuthenticationAuthorizationTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="portfolio_user",
            password="Secur3-password!",
        )

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "new_portfolio_user",
                "password1": "Secur3-new-password!",
                "password2": "Secur3-new-password!",
            },
        )

        self.assertRedirects(response, reverse("main:login"))
        self.assertTrue(
            get_user_model().objects.filter(username="new_portfolio_user").exists()
        )

    def test_login_sets_session_and_last_login_cookie(self):
        response = self.client.post(
            reverse("main:login"),
            {"username": "portfolio_user", "password": "Secur3-password!"},
        )

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertIn("sessionid", response.cookies)
        self.assertTrue(response.cookies["last_login"].value)

        home_response = self.client.get(reverse("main:show_main"))
        self.assertContains(home_response, "Sesi Terakhir Login")

    def test_logout_clears_session_and_last_login_cookie(self):
        self.client.post(
            reverse("main:login"),
            {"username": "portfolio_user", "password": "Secur3-password!"},
        )

        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"), fetch_redirect_response=False)
        self.assertEqual(response.cookies["last_login"].value, "")

        home_response = self.client.get(reverse("main:show_main"))
        self.assertContains(home_response, "Login")
        self.assertNotContains(home_response, "portfolio_user")

    def test_anonymous_users_are_redirected_from_write_actions(self):
        award = Award.objects.create(title="Login required", date_received="2026-09-16")

        response = self.client.post(reverse("main:create_award"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("main:login")))

        response = self.client.get(reverse("main:create_experience"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("main:login")))

        response = self.client.post(reverse("main:toggle_star_award", args=[award.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(award.starred_by.exists())

    def test_regular_user_cannot_create_award_or_experience(self):
        self.client.force_login(self.user)

        award_response = self.client.post(reverse("main:create_award"))
        experience_response = self.client.get(reverse("main:create_experience"))

        self.assertEqual(award_response.status_code, 403)
        self.assertEqual(experience_response.status_code, 403)
        self.assertEqual(Award.objects.count(), 0)
        self.assertEqual(Experience.objects.count(), 0)

    def test_regular_user_cannot_update_or_delete_experience(self):
        self.client.force_login(self.user)
        experience = Experience.objects.create(title="Protected experience")

        update_response = self.client.post(
            reverse("main:update_experience", args=[experience.pk]),
            {"title": "Changed by regular user", "category": "freelance"},
        )
        delete_response = self.client.post(
            reverse("main:delete_experience", args=[experience.pk])
        )

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        experience.refresh_from_db()
        self.assertEqual(experience.title, "Protected experience")
        self.assertTrue(Experience.objects.filter(pk=experience.pk).exists())

    def test_regular_user_cannot_delete_award(self):
        self.client.force_login(self.user)
        award = Award.objects.create(title="Protected award", date_received="2026-09-16")

        response = self.client.post(reverse("main:delete_award", args=[award.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Award.objects.filter(pk=award.pk).exists())

    def test_regular_user_can_star_and_unstar_award(self):
        self.client.force_login(self.user)
        award = Award.objects.create(title="Starred award", date_received="2026-09-16")
        url = reverse("main:toggle_star_award", args=[award.pk])

        star_response = self.client.post(url)
        self.assertRedirects(star_response, reverse("main:show_award"))
        self.assertTrue(award.starred_by.filter(pk=self.user.pk).exists())

        api_response = self.client.get(reverse("main:get_awards_json"))
        award_data = next(
            item["fields"]
            for item in api_response.json()
            if item["pk"] == str(award.pk)
        )
        self.assertTrue(award_data["is_starred"])
        self.assertEqual(award_data["star_count"], 1)

        unstar_response = self.client.post(url)
        self.assertRedirects(unstar_response, reverse("main:show_award"))
        self.assertFalse(award.starred_by.filter(pk=self.user.pk).exists())
        api_response = self.client.get(reverse("main:get_awards_json"))
        award_data = next(
            item["fields"]
            for item in api_response.json()
            if item["pk"] == str(award.pk)
        )
        self.assertFalse(award_data["is_starred"])
        self.assertEqual(award_data["star_count"], 0)

    def test_star_action_rejects_get_requests(self):
        self.client.force_login(self.user)
        award = Award.objects.create(title="Post only star", date_received="2026-09-16")

        response = self.client.get(reverse("main:toggle_star_award", args=[award.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertFalse(award.starred_by.exists())

    def test_editor_can_only_update_awards_and_experiences(self):
        self.user.groups.add(Group.objects.get(name="Editor"))
        self.client.force_login(self.user)
        award = Award.objects.create(title="Original award", date_received="2026-09-16")
        experience = Experience.objects.create(title="Original experience")

        self.assertEqual(self.client.post(reverse("main:create_award")).status_code, 403)
        self.assertEqual(self.client.get(reverse("main:create_experience")).status_code, 403)
        self.assertEqual(
            self.client.post(reverse("main:delete_award", args=[award.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("main:delete_experience", args=[experience.pk])).status_code,
            403,
        )

        award_form = self.client.get(reverse("main:update_award", args=[award.pk]))
        self.assertEqual(award_form.status_code, 405)
        award_response = self.client.post(
            reverse("main:update_award", args=[award.pk]),
            {"title": "Updated award", "date_received": "2026-09-16"},
        )
        self.assertRedirects(award_response, reverse("main:show_award"))
        award.refresh_from_db()
        self.assertEqual(award.title, "Updated award")

        update_response = self.client.post(
            reverse("main:update_experience", args=[experience.pk]),
            {"title": "Updated by editor", "category": "freelance"},
        )
        self.assertRedirects(update_response, reverse("main:show_experience"))
        experience.refresh_from_db()
        self.assertEqual(experience.title, "Updated by editor")

        self.assertTrue(Award.objects.filter(pk=award.pk).exists())
        self.assertTrue(Experience.objects.filter(pk=experience.pk).exists())

    def test_editor_sees_only_update_controls(self):
        self.user.groups.add(Group.objects.get(name="Editor"))
        self.client.force_login(self.user)
        award = Award.objects.create(title="Visible award", date_received="2026-09-16")
        experience = Experience.objects.create(title="Visible experience")

        award_page = self.client.get(reverse("main:show_award"))
        experience_page = self.client.get(reverse("main:show_experience"))

        self.assertContains(award_page, "const HAS_CHANGE_AWARD = \"true\" === \"true\";")
        self.assertContains(award_page, "const UPDATE_AWARD_URL =")
        self.assertContains(award_page, "00000000-0000-0000-0000-000000000000")
        self.assertContains(award_page, "const HAS_DELETE_AWARD = \"false\" === \"true\";")
        self.assertNotContains(award_page, reverse("main:create_award"))
        self.assertNotContains(award_page, "const HAS_DELETE_AWARD = \"true\" === \"true\";")
        self.assertNotContains(experience_page, reverse("main:create_experience"))
        self.assertContains(
            experience_page,
            "const HAS_CHANGE_EXPERIENCE = \"true\" === \"true\";",
        )
        self.assertContains(experience_page, "const UPDATE_EXPERIENCE_URL =")
        update_page = self.client.get(reverse("main:update_experience", args=[experience.pk]))
        self.assertNotContains(update_page, f"delete-experience-{experience.pk}")

    def test_regular_user_cannot_update_award(self):
        self.client.force_login(self.user)
        award = Award.objects.create(title="Protected award", date_received="2026-09-16")

        response = self.client.post(
            reverse("main:update_award", args=[award.pk]),
            {"title": "Changed", "date_received": "2026-09-16"},
        )

        self.assertEqual(response.status_code, 403)
        award.refresh_from_db()
        self.assertEqual(award.title, "Protected award")


class AwardModalUpdateTest(TestCase):
    def setUp(self):
        self.award = Award.objects.create(title="Original", date_received="2026-09-16")
        self.editor = get_user_model().objects.create_user(username="modal_editor")
        self.editor.groups.add(Group.objects.get(name="Editor"))
        self.url = f"/award/{self.award.pk}/update-ajax/"
        self.data = {"title": "<b>Updated</b>", "description": "<p>New description</p>",
                     "issuer": "<i>University</i>", "date_received": "2026-09-17"}

    def test_editor_updates_award_with_json_response_and_sanitized_text(self):
        self.client.force_login(self.editor)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pk"], str(self.award.pk))
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, "Updated")
        self.assertEqual(self.award.description, "New description")
        self.assertEqual(self.award.issuer, "University")

    def test_invalid_update_returns_errors_and_preserves_award(self):
        self.client.force_login(self.editor)
        response = self.client.post(self.url, {**self.data, "title": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, "Original")

    def test_visitor_and_regular_user_cannot_update(self):
        regular_user = get_user_model().objects.create_user(username="modal_regular")
        for user in (None, regular_user):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                response = self.client.post(self.url, self.data)
                self.assertEqual(response.status_code, 403)
                self.assertIn("message", response.json())
        self.award.refresh_from_db()
        self.assertEqual(self.award.title, "Original")

    def test_missing_award_returns_json_404(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            "/award/00000000-0000-0000-0000-000000000000/update-ajax/", self.data
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("message", response.json())

    def test_update_endpoint_rejects_get(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(self.url).status_code, 405)


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile_user", password="Current-password-123!"
        )
        self.url = reverse("main:show_user_profile")

    def test_profile_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={self.url}',
        )

    def test_profile_renders_existing_user_in_safe_form(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "user_profile.html")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'value="profile_user"')
        self.assertContains(response, 'name="current_password"')
        self.assertContains(response, 'name="new_password"')
        self.assertContains(response, 'name="confirm_new_password"')
        self.assertNotContains(response, self.user.password)

    def test_profile_rejects_wrong_current_password(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "username": "changed_user",
            "current_password": "wrong-password",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current password is incorrect")
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "profile_user")

    def test_profile_updates_username_and_password_without_logging_out(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "username": "changed_user",
            "current_password": "Current-password-123!",
            "new_password": "New-strong-password-456!",
            "confirm_new_password": "New-strong-password-456!",
        })

        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "changed_user")
        self.assertTrue(self.user.check_password("New-strong-password-456!"))
        self.assertContains(self.client.get(self.url), 'value="changed_user"')
