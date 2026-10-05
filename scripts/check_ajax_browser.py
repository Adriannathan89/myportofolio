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
        self.assertIn("JSON array", self.driver.find_element(By.ID, "toast-message").text)
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
            self.assertIn("HTML tags", self.driver.find_element(By.ID, "toast-message").text)
            self.fill("id_update-title", "Updated by " + user.username)
            # A lost network connection retains values and re-enables submission.
            self.driver.execute_script('window.savedFetch = window.fetch; window.fetch = () => Promise.reject(new TypeError("offline"));')
            submit.click()
            self.wait.until(lambda driver: "Could not reach" in driver.find_element(By.ID, "toast-message").text)
            self.wait.until(lambda driver: submit.is_enabled())
            self.assertEqual(self.driver.find_element(By.ID, "id_update-title").get_attribute("value"), "Updated by " + user.username)
            self.driver.execute_script("window.fetch = window.savedFetch;")
            submit.click()
            self.wait.until(lambda driver: any(card.text.startswith("Research\nUpdated by " + user.username)
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
            window.fetch = (...args) => String(args[0]).includes("/api/experiences/")
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
                self.wait.until(lambda driver: driver.find_element(By.ID, loading_id).is_displayed() is False)
                self.assertIn("title=Research", self.driver.execute_script("return window.fetchCalls[0]"))
                self.assertEqual(self.driver.execute_script("return window.pageIdentity"), "same-page")
                search.clear()
                search.send_keys("no-matching-item")
                self.wait.until(lambda driver: driver.find_element(By.ID, empty_id).is_displayed())
                # Pause a real fetch to make the loading state observable.
                self.driver.execute_script('window.fetch = (...args) => new Promise(resolve => { window.releaseFetch = () => resolve(window.savedFetch(...args)); });')
                self.driver.execute_script(f'{loader}("");')
                self.assertTrue(self.driver.find_element(By.ID, loading_id).is_displayed())
                self.driver.execute_script("window.releaseFetch();")
                self.wait.until(lambda driver: not driver.find_element(By.ID, loading_id).is_displayed())
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
