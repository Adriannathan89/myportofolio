import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist
from datetime import date
from pathlib import Path

from main.forms import ExperienceForm
from main.models import Award, Experience


@override_settings(AWARD_ACTION_KEY="test-award-key")
class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="PBP Teaching Assistant",
            description="Help students understand web development.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_main_page_does_not_render_experience_section(self):
        template_path = Path(__file__).resolve().parent.parent / "templates" / "index.html"
        template = template_path.read_text()

        self.assertNotIn('<section id="experience"', template)
        self.assertNotIn("Software Engineer Staff at Compfest 18", template)
        self.assertNotIn("Fullstack Developer at DDP0", template)

    def test_experience_seed_script_declares_required_records(self):
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "seed_experience.sh"
        self.assertTrue(script_path.is_file(), f"Expected seed script at {script_path}")
        if not script_path.is_file():
            return
        script = script_path.read_text()

        self.assertIn("Software Engineer Staff at Compfest 18", script)
        self.assertIn("Fullstack Developer at DDP0", script)
        self.assertIn("date(2026, 3, 1)", script)
        self.assertIn("date(2026, 6, 1)", script)
        self.assertIn("date(2026, 8, 31)", script)
        self.assertIn('"keyfeatures"', script)

    def test_award_seed_script_declares_required_records(self):
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "seed_award.sh"
        self.assertTrue(script_path.is_file(), f"Expected award seed script at {script_path}")
        if not script_path.is_file():
            return
        script = script_path.read_text()

        self.assertIn("Finalist — National Programming Contest (NPC) Junior", script)
        self.assertIn("Finalist — Indonesia National Competition in Informatics (NOI) 2024", script)
        self.assertIn("3rd Place — Diponegoro Logic Competition", script)
        self.assertIn('"thumbnail": "/static/img/Schematic.jpeg"', script)
        self.assertIn('"thumbnail": "/static/img/OSN.jpeg"', script)
        self.assertIn('"thumbnail": "/static/img/ANFORCOM.jpeg"', script)
        self.assertIn("date(2024, 10, 1)", script)
        self.assertIn("date(2024, 8, 1)", script)
        self.assertIn("date(2023, 9, 1)", script)

    def test_award_form_displays_all_fields(self):
        response = self.client.get(reverse("main:create_award"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "award_form.html")
        for field_name in ("title", "description", "thumbnail", "issuer", "date_received"):
            self.assertContains(response, f'name="{field_name}"')
        self.assertContains(response, 'type="date"')

    def test_award_form_rejects_submission_without_required_fields(self):
        response = self.client.post(reverse("main:create_award"), data={})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "award_form.html")
        self.assertContains(response, "This field is required.")
        self.assertEqual(Award.objects.count(), 0)

    def test_award_form_saves_valid_submission_and_redirects_to_awards(self):
        response = self.client.post(
            reverse("main:create_award"),
            data={
                "title": "Hackathon Winner",
                "description": "Won first place.",
                "thumbnail": "https://example.com/award.png",
                "issuer": "Tech Community",
                "date_received": "2026-09-16",
                "action_key": "test-award-key",
            },
            follow=True,
        )

        self.assertContains(response, "Award added successfully.")
        award = Award.objects.get(title="Hackathon Winner")
        self.assertEqual(award.description, "Won first place.")
        self.assertEqual(award.date_received, date(2026, 9, 16))

    def test_awards_json_endpoint_returns_serialized_awards(self):
        Award.objects.create(
            title="JSON Award",
            description="Serialized award.",
            issuer="Issuer",
            date_received=date(2026, 9, 16),
        )

        response = self.client.get("/api/awards/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = json.loads(response.content)
        self.assertEqual(payload[0]["model"], "main.award")
        self.assertEqual(payload[0]["fields"]["title"], "JSON Award")

    def test_awards_json_endpoint_filters_awards_by_title(self):
        Award.objects.create(title="Logic Competition", date_received=date(2026, 9, 16))
        Award.objects.create(title="Programming Contest", date_received=date(2026, 9, 16))

        response = self.client.get("/api/awards/?title=logic")

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["fields"]["title"], "Logic Competition")

    def test_award_page_filters_awards_and_preserves_search_query(self):
        Award.objects.create(title="Logic Competition", date_received=date(2026, 9, 16))
        Award.objects.create(title="Programming Contest", date_received=date(2026, 9, 16))

        response = self.client.get(reverse("main:show_award"), {"title": "logic"})

        self.assertContains(response, "Logic Competition")
        self.assertNotContains(response, "Programming Contest")
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'value="logic"')

    def test_award_page_renders_delete_popover_with_action_key_input(self):
        award = Award.objects.create(title="Protected Award", date_received=date(2026, 9, 16))

        response = self.client.get(reverse("main:show_award"))

        self.assertContains(response, f'popovertarget="delete-award-{award.id}"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'name="action_key"')

    def test_award_form_rejects_an_incorrect_action_key(self):
        response = self.client.post(
            reverse("main:create_award"),
            data={
                "title": "Unauthorized Award",
                "date_received": "2026-09-16",
                "action_key": "wrong-key",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid action key.")
        self.assertFalse(Award.objects.filter(title="Unauthorized Award").exists())

    @override_settings(AWARD_ACTION_KEY="")
    def test_award_form_rejects_submission_when_action_key_is_not_configured(self):
        response = self.client.post(
            reverse("main:create_award"),
            data={
                "title": "Unconfigured Award",
                "date_received": "2026-09-16",
                "action_key": "test-award-key",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid action key.")
        self.assertFalse(Award.objects.filter(title="Unconfigured Award").exists())

    def test_award_form_accepts_relative_thumbnail_path(self):
        response = self.client.post(
            reverse("main:create_award"),
            data={
                "title": "Local Certificate",
                "description": "Certificate stored in static files.",
                "thumbnail": "/static/img/local-certificate.jpeg",
                "issuer": "Local Organization",
                "date_received": "2026-09-16",
                "action_key": "test-award-key",
            },
        )

        self.assertRedirects(response, reverse("main:show_award"))
        award = Award.objects.get(title="Local Certificate")
        self.assertEqual(award.thumbnail, "/static/img/local-certificate.jpeg")

    def test_award_page_places_add_button_with_link_to_award_form(self):
        response = self.client.get(reverse("main:show_award"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{reverse("main:create_award")}"',
        )
        self.assertContains(response, "Add Award")

    def test_award_page_renders_delete_action_for_each_award(self):
        award = Award.objects.create(
            title="Award to Remove",
            description="An award that can be removed.",
            date_received=date(2026, 9, 16),
        )

        response = self.client.get(reverse("main:show_award"))

        self.assertContains(
            response,
            f'action="/award/{award.id}/delete/"',
        )
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, "Delete")

    def test_delete_award_removes_award_and_redirects_to_awards(self):
        award = Award.objects.create(
            title="Award to Remove",
            date_received=date(2026, 9, 16),
        )

        response = self.client.post(
            f"/award/{award.id}/delete/",
            data={"action_key": "test-award-key"},
            follow=True,
        )

        self.assertContains(response, "Award deleted successfully.")
        self.assertFalse(Award.objects.filter(pk=award.id).exists())

    def test_delete_award_keeps_award_when_action_key_is_incorrect(self):
        award = Award.objects.create(
            title="Protected Award",
            date_received=date(2026, 9, 16),
        )

        response = self.client.post(
            f"/award/{award.id}/delete/",
            data={"action_key": "wrong-key"},
            follow=True,
        )

        self.assertContains(response, "Invalid action key.")
        self.assertTrue(Award.objects.filter(pk=award.id).exists())

    @override_settings(AWARD_ACTION_KEY="")
    def test_delete_award_keeps_award_when_action_key_is_not_configured(self):
        award = Award.objects.create(
            title="Unconfigured Award",
            date_received=date(2026, 9, 16),
        )

        response = self.client.post(
            f"/award/{award.id}/delete/",
            data={"action_key": "test-award-key"},
            follow=True,
        )

        self.assertContains(response, "Invalid action key.")
        self.assertTrue(Award.objects.filter(pk=award.id).exists())

    def test_delete_award_rejects_get_requests(self):
        award = Award.objects.create(
            title="Protected Award",
            date_received=date(2026, 9, 16),
        )

        response = self.client.get(
            f"/award/{award.id}/delete/"
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Award.objects.filter(pk=award.id).exists())

    def test_award_grid_aligns_cards_to_their_content(self):
        stylesheet_path = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"
        stylesheet = stylesheet_path.read_text()

        self.assertIn(
            ".award-grid {\n"
            "    display: grid;\n"
            "    grid-template-columns: repeat(2, 1fr);\n"
            "    gap: 24px;\n"
            "    margin-top: 16px;\n"
            "    align-items: start;\n"
            "}",
            stylesheet,
        )

    def test_award_cards_have_fixed_dimensions_and_keep_thumbnail_top_visible(self):
        stylesheet_path = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"
        stylesheet = stylesheet_path.read_text()

        self.assertIn("height: 500px;", stylesheet)
        self.assertIn(
            ".award-thumbnail {\n"
            "    width: 100%;\n"
            "    height: 275px;",
            stylesheet,
        )
        self.assertIn("object-fit: cover;", stylesheet)
        self.assertIn("object-position: top;", stylesheet)

    def test_award_delete_action_is_pinned_to_the_card_bottom_right(self):
        stylesheet_path = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"
        stylesheet = stylesheet_path.read_text()

        card_start = stylesheet.index(".award-grid .award-card {")
        card_end = stylesheet.index("}\n", card_start)
        award_card_rules = stylesheet[card_start:card_end]

        self.assertIn("    position: relative;\n", award_card_rules)
        self.assertIn(
            ".award-actions {\n"
            "    position: absolute;\n"
            "    right: 16px;\n"
            "    bottom: 16px;\n"
            "}",
            stylesheet,
        )

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/a-page-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "PBP Teaching Assistant")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_form_offers_category_enum_as_a_dropdown(self):
        form = ExperienceForm()

        self.assertEqual(
            list(form.fields["category"].choices),
            [
                ("internship", "Internship"),
                ("research", "Research"),
                ("volunteer", "Volunteer"),
                ("part-time", "Part-Time"),
                ("full-time", "Full-Time"),
                ("freelance", "Freelance"),
            ],
        )
        self.assertIn('<select name="category"', form.as_p())

    def test_create_experience_form_displays_all_editable_fields(self):
        response = self.client.get(reverse("main:create_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_create_form.html")
        for field_name in (
            "title",
            "description",
            "category",
            "keyfeatures",
            "start_at",
            "ended_at",
            "action_key",
        ):
            self.assertContains(response, f'name="{field_name}"')

    def test_create_experience_saves_valid_submission(self):
        response = self.client.post(
            reverse("main:create_experience"),
            data={
                "title": "Software Engineering Intern",
                "description": "Built internal tools.",
                "category": "internship",
                "keyfeatures": '["Built dashboards"]',
                "start_at": "2025-01-15",
                "ended_at": "2025-06-15",
                "action_key": "test-award-key",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        experience = Experience.objects.get(title="Software Engineering Intern")
        self.assertEqual(experience.category, "internship")
        self.assertEqual(experience.keyfeatures, ["Built dashboards"])
        self.assertEqual(experience.start_at, date(2025, 1, 15))
        self.assertEqual(experience.ended_at, date(2025, 6, 15))

    def test_update_experience_form_is_prepopulated_and_offers_delete_confirmation(self):
        self.experience.start_at = date(2025, 1, 15)
        self.experience.save()

        response = self.client.get(
            reverse("main:update_experience", args=[self.experience.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_update_form.html")
        self.assertContains(response, 'value="PBP Teaching Assistant"')
        self.assertContains(response, 'value="2025-01-15"')
        self.assertContains(response, "Save")
        self.assertContains(response, "Delete")
        self.assertContains(response, f'popovertarget="delete-experience-{self.experience.id}"')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, f'action="/experience/{self.experience.id}/delete/"')

    def test_update_experience_saves_valid_submission(self):
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]),
            data={
                "title": "Updated Teaching Assistant",
                "description": "Guided students through Django.",
                "category": "full-time",
                "keyfeatures": '["Held office hours"]',
                "start_at": "2025-01-15",
                "ended_at": "2025-06-15",
                "action_key": "test-award-key",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Updated Teaching Assistant")
        self.assertEqual(self.experience.category, "full-time")
        self.assertEqual(self.experience.keyfeatures, ["Held office hours"])
        self.assertEqual(self.experience.start_at, date(2025, 1, 15))
        self.assertEqual(self.experience.ended_at, date(2025, 6, 15))

    def test_delete_experience_requires_valid_action_key(self):
        response = self.client.post(
            reverse("main:delete_experience", args=[self.experience.id]),
            data={"action_key": "wrong-key"},
            follow=True,
        )

        self.assertContains(response, "Invalid action key.")
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_delete_experience_removes_experience(self):
        response = self.client.post(
            reverse("main:delete_experience", args=[self.experience.id]),
            data={"action_key": "test-award-key"},
            follow=True,
        )

        self.assertContains(response, "Experience deleted successfully.")
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())

    def test_delete_experience_rejects_get_requests(self):
        response = self.client.get(
            reverse("main:delete_experience", args=[self.experience.id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_experience_page_filters_by_title_and_links_to_create_and_update_forms(self):
        other_experience = Experience.objects.create(
            title="Research Assistant",
            description="Investigated software quality.",
        )

        response = self.client.get(reverse("main:show_experience"), {"title": "teaching"})

        self.assertContains(response, self.experience.title)
        self.assertNotContains(response, other_experience.title)
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'value="teaching"')
        self.assertContains(
            response,
            f'href="{reverse("main:create_experience")}"',
        )
        self.assertContains(response, "Add Experience")
        self.assertContains(
            response,
            f'href="{reverse("main:update_experience", args=[self.experience.id])}"',
        )

    def test_experience_start_at_is_not_set_automatically(self):
        experience = Experience.objects.create(title="Experience Without Start Date")

        self.assertIsNone(experience.start_at)

    def test_experience_start_at_accepts_a_manually_selected_date(self):
        selected_start_date = date(2024, 1, 15)
        experience = Experience.objects.create(
            title="Experience With Start Date",
            start_at=selected_start_date,
        )

        self.assertEqual(experience.start_at, selected_start_date)

    def test_experience_model_does_not_include_thumbnail(self):
        with self.assertRaises(FieldDoesNotExist):
            Experience._meta.get_field("thumbnail")

    def test_experience_timestamps_default_to_current_time(self):
        before_create = timezone.now()
        experience = Experience.objects.create(title="Timestamped Experience")
        after_create = timezone.now()

        self.assertGreaterEqual(experience.created_at, before_create)
        self.assertLessEqual(experience.created_at, after_create)
        self.assertGreaterEqual(experience.updated_at, before_create)
        self.assertLessEqual(experience.updated_at, after_create)

    def test_experience_timestamps_accept_null_values(self):
        experience = Experience.objects.create(
            title="Experience Without Timestamps",
            created_at=None,
            updated_at=None,
        )

        self.assertIsNone(experience.created_at)
        self.assertIsNone(experience.updated_at)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_experience_page_renders_all_experience_fields(self):
        keyfeatures = [
            "Built the frontend",
            "Built the backend",
        ]
        self.experience.keyfeatures = keyfeatures
        self.experience.save()
        Experience.objects.filter(pk=self.experience.pk).update(
            start_at=date(2026, 3, 1),
            ended_at=date(2026, 8, 31),
        )

        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, self.experience.get_category_display())
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        for keyfeature in keyfeatures:
            self.assertContains(response, keyfeature)
        self.assertContains(response, "Mar 2026")
        self.assertContains(response, "Aug 2026")

    def test_experience_page_renders_cards_in_alternating_timeline(self):
        Experience.objects.create(
            title="Second Experience",
            description="Another experience.",
        )

        response = self.client.get(reverse("main:show_experience"))
        content = response.content.decode()

        self.assertContains(response, "experience-timeline")
        self.assertContains(response, "experience-timeline-item--left")
        self.assertContains(response, "experience-timeline-item--right")
        self.assertLess(
            content.index("experience-timeline-item--left"),
            content.index("experience-timeline-item--right"),
        )

    def test_experience_styles_define_responsive_font_sizes(self):
        stylesheet_path = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"
        stylesheet = stylesheet_path.read_text()

        self.assertIn("@media (max-width: 900px)", stylesheet)
        self.assertIn(".experience-card h2 {\n        font-size: 28px;", stylesheet)
        self.assertIn("font-size: 15px;", stylesheet)
        self.assertIn("@media (max-width: 600px)", stylesheet)
        self.assertIn(".experience-card h2 {\n        font-size: 24px;", stylesheet)
        self.assertIn("font-size: 14px;", stylesheet)
        self.assertIn("font-size: 12px;", stylesheet)

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experience has been added yet.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Completed")
        self.assertNotContains(response, "Ongoing")
