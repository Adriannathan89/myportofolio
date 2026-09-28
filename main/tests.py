from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from main.models import Award, Experience


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

        response = self.client.get(reverse("main:create_award"))
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

        award_response = self.client.get(reverse("main:create_award"))
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

        page_response = self.client.get(reverse("main:show_award"))
        self.assertContains(page_response, "is-starred")
        self.assertContains(page_response, '<span class="star-count">1</span>')

        unstar_response = self.client.post(url)
        self.assertRedirects(unstar_response, reverse("main:show_award"))
        self.assertFalse(award.starred_by.filter(pk=self.user.pk).exists())

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

        self.assertEqual(self.client.get(reverse("main:create_award")).status_code, 403)
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
        self.assertEqual(award_form.status_code, 200)
        self.assertContains(award_form, 'value="Original award"')
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

        self.assertContains(award_page, reverse("main:update_award", args=[award.pk]))
        self.assertNotContains(award_page, reverse("main:create_award"))
        self.assertNotContains(award_page, f"delete-award-{award.pk}")
        self.assertNotContains(experience_page, reverse("main:create_experience"))
        self.assertContains(experience_page, "experience-card-link")
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
