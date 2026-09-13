from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date
from pathlib import Path

from main.models import Experience


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

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/a-page-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "PBP Teaching Assistant")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

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
        thumbnail = "https://example.com/experience.png"
        keyfeatures = [
            "Built the frontend",
            "Built the backend",
        ]
        self.experience.thumbnail = thumbnail
        self.experience.keyfeatures = keyfeatures
        self.experience.save()
        Experience.objects.filter(pk=self.experience.pk).update(
            start_at=date(2026, 3, 1),
            ended_at=date(2026, 8, 31),
        )

        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, thumbnail)
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
