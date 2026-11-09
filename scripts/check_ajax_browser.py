#!/usr/bin/env python3
"""Exercise AJAX lists and modals in a browser against a temporary test database.

Run: env/bin/python scripts/check_ajax_browser.py
Requires Selenium and locally installed Chrome/Chromedriver. Set CHROME_BINARY
and CHROMEDRIVER_BINARY to override local installation/cache discovery.
"""

import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myportofolio.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from main.models import Award, Experience


def local_binary(env_name, executables, cache_pattern):
    if os.environ.get(env_name):
        return os.environ[env_name]
    for executable in executables:
        if found := shutil.which(executable):
            return found
    matches = sorted((Path.home() / ".cache/selenium").glob(cache_pattern))
    if matches:
        return str(matches[-1])
    raise RuntimeError(f"Install a local browser/driver or set {env_name}.")


class AjaxBrowserCheck(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.binary_location = local_binary(
            "CHROME_BINARY", ("google-chrome", "chromium", "chromium-browser"),
            "chrome/linux64/*/chrome",
        )
        for argument in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                         "--window-size=1365,1000"):
            options.add_argument(argument)
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        driver_path = local_binary("CHROMEDRIVER_BINARY", ("chromedriver",),
                                   "chromedriver/linux64/*/chromedriver")
        cls.driver = webdriver.Chrome(service=Service(driver_path), options=options)
        cls.addClassCleanup(cls.driver.quit)

    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_superuser(username="browser_admin")
        self.editor = users.objects.create_user(username="browser_editor")
        group, _ = Group.objects.get_or_create(name="Editor")
        group.permissions.set(Permission.objects.filter(
            content_type__app_label="main", codename__in=("change_award", "change_experience")
        ))
        self.editor.groups.add(group)
        self.regular = users.objects.create_user(username="browser_regular")
        self.experience = Experience.objects.create(
            title="Research internship", description="Original description",
            category="research", keyfeatures=["Published results"], start_at="2026-09-01",
        )
        self.award = Award.objects.create(title="Research prize", date_received="2026-09-01")
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get(self.live_server_url + "/")
        self.driver.delete_all_cookies()
        self.driver.get_log("browser")

    def tearDown(self):
        errors = [entry for entry in self.driver.get_log("browser")
                  if "Uncaught" in entry["message"]]
        self.assertEqual(errors, [], "Unexpected JavaScript error")

    def visit(self, path, user=None):
        self.driver.delete_all_cookies()
        self.client.logout()
        if user:
            self.client.force_login(user)
            self.driver.add_cookie({"name": "sessionid", "value": self.client.cookies["sessionid"].value})
        self.driver.get(self.live_server_url + path)
        self.wait.until(lambda driver: driver.find_elements(By.CSS_SELECTOR,
                        ".experience-card" if path.startswith("/experience") else ".award-card"))
        self.driver.execute_script('window.pageIdentity = "same-page";')

    def fill(self, field_id, value):
        field = self.driver.find_element(By.ID, field_id)
        field.clear()
        field.send_keys(value)

    def assert_same_page(self, url):
        self.assertEqual(self.driver.current_url, url)
        self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")

    def test_all_roles_load_lists_and_see_only_permitted_actions(self):
        for user, may_add, may_edit in ((None, False, False), (self.regular, False, False),
                                       (self.editor, False, True), (self.admin, True, True)):
            for path, model in (("/experience/", "experience"), ("/award/", "award")):
                with self.subTest(user=user, model=model):
                    self.visit(path, user)
                    self.assertEqual(bool(self.driver.find_elements(By.ID, f"add-{model}-modal")), may_add)
                    self.assertEqual(bool(self.driver.find_elements(By.ID, f"update-{model}-modal")), may_edit)
                    edit_selector = ".experience-card-edit-button" if model == "experience" else ".award-card-edit-link"
                    self.assertEqual(bool(self.driver.find_elements(By.CSS_SELECTOR, edit_selector)), may_edit)
                    self.assertTrue(self.driver.execute_script(
                        'const ids = [...document.querySelectorAll("[id]")].map(e => e.id); '
                        'return ids.length === new Set(ids).size;'
                    ))

    def test_experience_add_and_edit_without_reload_with_validation_and_retry(self):
        self.visit("/experience/", self.admin)
        url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, '[popovertarget="add-experience-modal"]').click()
        self.fill("id_create-title", "Added via AJAX")
        self.fill("id_create-description", "<b>Safe description</b>")
        self.fill("id_create-keyfeatures", '{"invalid": "object"}')
        submit = self.driver.find_element(By.CSS_SELECTOR, '#experience-create-form button[type="submit"]')
        submit.click()
        self.wait.until(lambda driver: driver.find_element(By.ID, "toast-title").text == "Failed to add experience")
        self.assertIn("list", self.driver.find_element(By.ID, "toast-message").text)
        self.assertEqual(self.driver.find_element(By.ID, "id_create-title").get_attribute("value"), "Added via AJAX")
        self.assertTrue(self.driver.execute_script('return document.getElementById("add-experience-modal").matches(":popover-open")'))
        self.fill("id_create-keyfeatures", '["<b>New feature</b>"]')
        submit.click()
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".experience-card")) == 2)
        self.assert_same_page(url)
        created = Experience.objects.get(title="Added via AJAX")
        self.assertEqual(created.description, "Safe description")
        self.assertEqual(created.keyfeatures, ["New feature"])
        self.assertEqual(self.driver.find_element(By.ID, "toast-title").text, "Success")
        self.assertFalse(self.driver.execute_script('return document.getElementById("add-experience-modal").matches(":popover-open")'))

        for user in (self.editor, self.admin):
            self.visit("/experience/", user)
            url = self.driver.current_url
            button = self.driver.find_element(By.CSS_SELECTOR, f'button[data-experience-id="{self.experience.pk}"]')
            button.click()
            self.wait.until(lambda driver: driver.find_element(By.ID, "id_update-title").is_displayed())
            self.assertEqual(self.driver.find_element(By.ID, "id_update-title").get_attribute("value"), self.experience.title)
            self.assertEqual(self.driver.find_element(By.ID, "id_update-category").get_attribute("value"), "research")
            self.assertEqual(self.driver.find_element(By.ID, "id_update-keyfeatures").get_attribute("value"), '["Published results"]')
            self.assertEqual(self.driver.find_element(By.ID, "id_update-start_at").get_attribute("value"), "2026-09-01")
            submit = self.driver.find_element(By.CSS_SELECTOR, '#experience-update-form button[type="submit"]')
            self.fill("id_update-title", "<b></b>")
            submit.click()
            self.wait.until(lambda driver: driver.find_element(By.ID, "toast-title").text == "Failed to update experience")
            self.assertIn("empty", self.driver.find_element(By.ID, "toast-message").text)
            self.fill("id_update-title", "Updated by " + user.username)
            # A lost network connection retains values and re-enables submission.
            self.driver.execute_script('window.savedFetch = window.fetch; window.fetch = () => Promise.reject(new TypeError("offline"));')
            submit.click()
            self.wait.until(lambda driver: "offline" in driver.find_element(By.ID, "toast-message").text)
            self.wait.until(lambda driver, submit=submit: submit.is_enabled())
            self.assertEqual(self.driver.find_element(By.ID, "id_update-title").get_attribute("value"), "Updated by " + user.username)
            self.driver.execute_script("window.fetch = window.savedFetch;")
            submit.click()
            self.wait.until(lambda driver, user=user: any(card.text.startswith("Research\nUpdated by " + user.username)
                            for card in driver.find_elements(By.CSS_SELECTOR, ".experience-card")))
            self.assert_same_page(url)
            self.experience.refresh_from_db()
            self.assertEqual(self.experience.title, "Updated by " + user.username)
            self.assertFalse(self.driver.execute_script('return document.getElementById("update-experience-modal").matches(":popover-open")'))

    def test_successful_experience_write_reports_failed_refresh(self):
        self.visit("/experience/?title=Research", self.admin)
        url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, '[popovertarget="add-experience-modal"]').click()
        self.fill("id_create-title", "Research saved before refresh failure")
        self.driver.execute_script('''
            window.savedFetch = window.fetch;
            window.fetch = (...args) => String(args[0]).includes("/api/v1/experiences/") && (!args[1]?.method || args[1].method === "GET")
                ? Promise.resolve(new Response("unavailable", {status: 500}))
                : window.savedFetch(...args);
        ''')
        self.driver.find_element(By.CSS_SELECTOR, '#experience-create-form button[type="submit"]').click()
        self.wait.until(lambda driver: "Failed to load" in driver.find_element(By.ID, "toast-title").text)
        self.assertTrue(Experience.objects.filter(title="Research saved before refresh failure").exists())
        self.assertTrue(self.driver.find_element(By.ID, "error").is_displayed())
        self.assertFalse(self.driver.execute_script('return document.getElementById("add-experience-modal").matches(":popover-open")'))
        self.assert_same_page(url)
        self.assertEqual(self.driver.find_element(By.ID, "experience-title-search").get_attribute("value"), "Research")
        # Retry the read without repeating the already successful POST.
        self.driver.execute_script('window.fetch = window.savedFetch; loadExperiences("Research");')
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".experience-card")) == 2)
        self.assertFalse(self.driver.find_element(By.ID, "error").is_displayed())

    def test_experience_star_without_reload(self):
        self.visit("/experience/", self.regular)
        url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, ".experience-card .button-star").click()
        modal = self.driver.find_element(By.CSS_SELECTOR, ".experience-card .award-star-modal")
        self.assertTrue(modal.is_displayed())
        self.assertIn("Research internship", modal.text)
        self.assertFalse(self.experience.starred_by.exists())
        modal.find_element(By.CSS_SELECTOR, ".cancel-button").click()
        self.assertFalse(self.experience.starred_by.exists())
        self.driver.find_element(By.CSS_SELECTOR, ".experience-card .button-star").click()
        modal.find_element(By.CSS_SELECTOR, ".star-confirm-button").click()
        self.wait.until(lambda driver: "Unstar" in driver.find_element(By.CSS_SELECTOR, ".experience-card .button-star").text)
        self.assert_same_page(url)
        self.assertTrue(self.experience.starred_by.filter(pk=self.regular.pk).exists())
        self.driver.find_element(By.CSS_SELECTOR, ".experience-card .button-star").click()
        self.assertIn("Remove your star", modal.text)
        modal.find_element(By.CSS_SELECTOR, ".star-confirm-button").click()
        self.wait.until(lambda driver: "Unstar" not in driver.find_element(By.CSS_SELECTOR, ".experience-card .button-star").text)
        self.assertFalse(self.experience.starred_by.exists())

    def test_standalone_experience_edit_uses_rest_patch_without_navigation(self):
        self.visit("/experience/", self.admin)
        self.driver.get(self.live_server_url + f"/experience/{self.experience.pk}/")
        self.driver.execute_script('''
            window.pageIdentity = "same-page";
            window.fetchCalls = [];
            window.savedFetch = window.fetch;
            window.fetch = (...args) => {
                window.fetchCalls.push({url: String(args[0]), method: args[1]?.method || "GET"});
                return window.savedFetch(...args);
            };
        ''')
        self.fill("id_title", "Updated via REST")
        self.driver.execute_script('document.querySelector("form.award-form").requestSubmit()')
        self.wait.until(lambda driver: Experience.objects.filter(pk=self.experience.pk, title="Updated via REST").exists())
        self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")
        calls = self.driver.execute_script("return window.fetchCalls")
        self.assertEqual(calls[0]["method"], "PATCH")
        self.assertIn("/api/v1/experiences/", calls[0]["url"])

    def test_standalone_experience_create_and_delete_use_rest(self):
        self.visit("/experience/", self.admin)
        self.driver.get(self.live_server_url + "/experience/add/")
        self.driver.execute_script('window.pageIdentity = "same-page";')
        self.fill("id_title", "Created via REST")
        self.driver.execute_script('document.querySelector("form.award-form").requestSubmit()')
        self.wait.until(lambda driver: Experience.objects.filter(title="Created via REST").exists())
        self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")
        self.driver.get(self.live_server_url + f"/experience/{self.experience.pk}/")
        self.driver.execute_script('window.pageIdentity = "same-page";')
        self.driver.execute_script('document.querySelector(".delete-button").click()')
        self.driver.execute_script('document.querySelector("form.award-delete-form").requestSubmit()')
        self.wait.until(lambda driver: not Experience.objects.filter(pk=self.experience.pk).exists())
        self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")

    def test_search_keeps_existing_results_visible_while_fetching(self):
        for path, loader, card in (("/experience/", "loadExperiences", ".experience-card"),
                                   ("/award/", "loadAwards", ".award-card")):
            with self.subTest(path=path):
                self.visit(path)
                self.driver.execute_script('''
                    window.savedFetch = window.fetch;
                    window.fetch = (...args) => new Promise(resolve => {
                        window.releaseFetch = () => resolve(window.savedFetch(...args));
                    });
                ''')
                self.driver.execute_script(f'{loader}("Research");')
                self.assertTrue(self.driver.find_element(By.CSS_SELECTOR, card).is_displayed())
                self.driver.execute_script('window.releaseFetch();')
                self.wait.until(lambda driver: driver.execute_script(
                    "return !document.querySelector(arguments[0]).classList.contains('empty-state-hidden')",
                    "#loading" if path == "/experience/" else "#award-loading") is False)

    def test_star_updates_without_refetching_list(self):
        for path, selector in (("/experience/", ".experience-card .button-star"),
                               ("/award/", ".award-card .button-star")):
            with self.subTest(path=path):
                self.visit(path, self.regular)
                self.driver.execute_script('''
                    window.fetchCalls = [];
                    window.savedFetch = window.fetch;
                    window.fetch = (...args) => {
                        window.fetchCalls.push({url: String(args[0]), method: args[1]?.method || "GET"});
                        return window.savedFetch(...args);
                    };
                ''')
                self.driver.find_element(By.CSS_SELECTOR, selector).click()
                self.wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, ".star-confirm-button").is_displayed())
                self.driver.find_element(By.CSS_SELECTOR, ".star-confirm-button").click()
                self.wait.until(lambda driver: driver.execute_script(
                    "return document.querySelector(arguments[0])?.textContent.includes('Unstar')", selector))
                calls = self.driver.execute_script("return window.fetchCalls")
                self.assertEqual([call["method"] for call in calls], ["POST"])
                self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")

    def test_experience_edit_modal_delete_targets_selected_item_and_requires_permission(self):
        other = Experience.objects.create(title="Other experience")
        self.visit("/experience/", self.editor)
        self.driver.find_element(By.CSS_SELECTOR, f'button[data-experience-id="{self.experience.pk}"]').click()
        self.wait.until(lambda driver: driver.find_element(By.ID, "id_update-title").is_displayed())
        self.assertFalse(self.driver.find_elements(By.ID, "experience-update-delete"))

        self.visit("/experience/", self.admin)
        for item in (self.experience, other):
            self.driver.find_element(By.CSS_SELECTOR, f'button[data-experience-id="{item.pk}"]').click()
            self.wait.until(lambda driver: driver.find_element(By.ID, "id_update-title").is_displayed())
            delete_button = self.driver.find_element(By.ID, "experience-update-delete")
            self.assertEqual(delete_button.text, "Delete")
            delete_button.click()
            self.wait.until(lambda driver: driver.execute_script(
                'return document.getElementById("delete-experience-modal").matches(":popover-open")'))
            self.assertFalse(self.driver.execute_script('return document.getElementById("update-experience-modal").matches(":popover-open")'))
            self.assertIn(item.title, self.driver.find_element(By.ID, "delete-experience-modal").text)
            if item.pk == self.experience.pk:
                self.driver.find_element(By.CSS_SELECTOR, '#delete-experience-modal .cancel-button').click()
                self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())
            else:
                self.driver.find_element(By.CSS_SELECTOR, '#delete-experience-modal button[type="submit"]').click()
                self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".experience-card")) == 1)
                self.assertFalse(Experience.objects.filter(pk=other.pk).exists())
                self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_award_edit_modal_delete_targets_selected_award_and_requires_permission(self):
        other = Award.objects.create(title="Other prize", date_received="2026-09-02")
        self.visit("/award/", self.editor)
        self.driver.find_element(By.CSS_SELECTOR, '.award-card-edit-link[aria-label="Edit Research prize"]').click()
        self.wait.until(lambda driver: driver.find_element(By.ID, "id_update-title").is_displayed())
        self.assertFalse(self.driver.find_elements(By.ID, "award-update-delete"))

        self.visit("/award/", self.admin)
        for title, item_id in (("Research prize", self.award.pk), ("Other prize", other.pk)):
            self.driver.find_element(By.CSS_SELECTOR, f'.award-card-edit-link[aria-label="Edit {title}"]').click()
            self.wait.until(lambda driver: driver.find_element(By.ID, "id_update-title").is_displayed())
            delete_button = self.driver.find_element(By.ID, "award-update-delete")
            self.assertEqual(delete_button.text, "Delete")
            delete_button.click()
            modal_id = f"delete-award-{item_id}"
            self.wait.until(lambda driver, modal_id=modal_id: driver.execute_script(
                'return document.getElementById(arguments[0]).matches(":popover-open")', modal_id))
            self.assertFalse(self.driver.execute_script('return document.getElementById("update-award-modal").matches(":popover-open")'))
            self.assertIn(title, self.driver.find_element(By.ID, modal_id).text)
            if item_id == self.award.pk:
                self.driver.find_element(By.CSS_SELECTOR, f'#{modal_id} .cancel-button').click()
                self.assertTrue(Award.objects.filter(pk=self.award.pk).exists())
            else:
                self.driver.find_element(By.CSS_SELECTOR, f'#{modal_id} button[type="submit"]').click()
                self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".award-card")) == 1)
                self.assertFalse(Award.objects.filter(pk=other.pk).exists())
                self.assertTrue(Award.objects.filter(pk=self.award.pk).exists())

    def test_award_add_without_reload_and_server_validation_toast(self):
        self.visit("/award/", self.admin)
        url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, '[popovertarget="add-award-modal"]').click()
        self.fill("id_title", "<b>AJAX prize</b>")
        self.fill("id_thumbnail", "javascript:alert(1)")
        self.driver.execute_script('document.getElementById("id_date_received").value = "2026-09-20";')
        submit = self.driver.find_element(By.CSS_SELECTOR, '#award-form button[type="submit"]')
        submit.click()
        self.wait.until(lambda driver: driver.find_element(By.ID, "toast-title").text == "Failed to add award")
        self.assertIn("http(s)", self.driver.find_element(By.ID, "toast-message").text)
        self.fill("id_thumbnail", "")
        submit.click()
        self.wait.until(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, ".award-card")) == 2)
        self.assert_same_page(url)
        self.assertTrue(Award.objects.filter(title="AJAX prize").exists())

    def test_debounce_loading_empty_and_failure_toasts_on_both_lists(self):
        for path, loader, input_id, empty_id, loading_id, error_id in (
            ("/experience/", "loadExperiences", "experience-title-search", "empty", "loading", "error"),
            ("/award/", "loadAwards", "award-title-search", "award-empty", "award-loading", "award-error"),
        ):
            with self.subTest(path=path):
                self.visit(path)
                self.driver.execute_script('''
                    window.fetchCalls = [];
                    window.savedFetch = window.fetch;
                    window.fetch = (...args) => {
                        window.fetchCalls.push(String(args[0]));
                        return window.savedFetch(...args);
                    };
                ''')
                search = self.driver.find_element(By.ID, input_id)
                search.send_keys("Re")
                search.send_keys("sea")
                search.send_keys("rch")
                self.assertEqual(self.driver.execute_script("return window.fetchCalls.length"), 0)
                self.wait.until(lambda driver: len(driver.execute_script("return window.fetchCalls")) == 1)
                self.wait.until(lambda driver, loading_id=loading_id: driver.find_element(By.ID, loading_id).is_displayed() is False)
                self.assertIn("title=Research", self.driver.execute_script("return window.fetchCalls[0]"))
                self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")
                search.clear()
                search.send_keys("no-matching-item")
                self.wait.until(lambda driver, empty_id=empty_id: driver.find_element(By.ID, empty_id).is_displayed())
                # Pause a real fetch to make the loading state observable.
                self.driver.execute_script('window.fetch = (...args) => new Promise(resolve => { window.releaseFetch = () => resolve(window.savedFetch(...args)); });')
                self.driver.execute_script(f'{loader}("");')
                self.assertTrue(self.driver.find_element(By.ID, loading_id).is_displayed())
                self.driver.execute_script("window.releaseFetch();")
                self.wait.until(lambda driver, loading_id=loading_id: not driver.find_element(By.ID, loading_id).is_displayed())
                # Aborts are expected when typing; they must not emit failure toasts.
                self.driver.execute_script('window.fetch = () => Promise.reject(new DOMException("Aborted", "AbortError"));')
                self.driver.execute_async_script(f'{loader}("").then(arguments[0]);')
                self.assertFalse(self.driver.execute_script('return document.getElementById("toast-component").matches(":popover-open")'))
                # HTTP and network failures must both show an error state and toast.
                for failing_fetch in ('() => Promise.resolve(new Response("failed", {status: 500}))',
                                      '() => Promise.reject(new TypeError("offline"))'):
                    self.driver.execute_script("window.fetch = " + failing_fetch)
                    self.driver.execute_async_script(f'{loader}("").then(arguments[0]);')
                    self.assertTrue(self.driver.find_element(By.ID, error_id).is_displayed())
                    self.assertTrue(self.driver.execute_script('return document.getElementById("toast-component").matches(":popover-open")'))
                    self.wait.until(lambda driver: "Failed to load" in driver.find_element(By.ID, "toast-title").text)

    def test_initial_load_failure_shows_toast_after_page_initialization(self):
        injection = self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": '''
            const originalFetch = window.fetch;
            window.fetch = (...args) => String(args[0]).includes("/api/")
                ? Promise.resolve(new Response("unavailable", {status: 500}))
                : originalFetch(...args);
        '''})["identifier"]
        try:
            for path, error_id in (("/experience/", "error"), ("/award/", "award-error")):
                with self.subTest(path=path):
                    self.driver.get(self.live_server_url + path)
                    self.wait.until(lambda driver: "Failed to load" in driver.find_element(By.ID, "toast-title").text)
                    self.assertTrue(self.driver.find_element(By.ID, error_id).is_displayed())
        finally:
            self.driver.execute_cdp_cmd("Page.removeScriptToEvaluateOnNewDocument", {"identifier": injection})

    def test_legacy_html_is_rendered_as_text_for_visitors(self):
        payload = '<img src="x" onerror="window.xssTriggered = true">'
        self.experience.title = payload
        self.experience.description = payload
        self.experience.keyfeatures = [payload]
        self.experience.save()
        self.award.title = payload
        self.award.description = payload
        self.award.issuer = payload
        self.award.save()
        for path, selector in (("/experience/", ".experience-card"), ("/award/", ".award-card")):
            self.visit(path)
            self.assertIn(payload, self.driver.find_element(By.CSS_SELECTOR, selector).text)
            self.assertFalse(self.driver.find_elements(By.CSS_SELECTOR, selector + " img"))
            self.assertIsNone(self.driver.execute_script("return window.xssTriggered || null"))


if __name__ == "__main__":
    labels = [f"__main__.AjaxBrowserCheck.{name}" for name in sys.argv[1:]] or ["__main__.AjaxBrowserCheck"]
    sys.exit(bool(DiscoverRunner(verbosity=2).run_tests(labels)))
