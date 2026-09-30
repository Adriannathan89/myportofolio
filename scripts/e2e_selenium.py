#!/usr/bin/env python3
"""Run browser checks for authentication, authorization, and award stars."""

import os
import sys
import time
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

USER_PASSWORD = os.getenv("E2E_USER_PASSWORD")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD")
BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
XSS_STORAGE_KEY = "portfolioXssTriggered"
XSS_PAYLOAD = (
    '<img src="/__missing_xss_e2e_image__.png" '
    f'onerror="localStorage.setItem(\'{XSS_STORAGE_KEY}\', \'executed\')">'
)

parsed_base_url = urlsplit(BASE_URL)
if parsed_base_url.scheme not in {"http", "https"} or parsed_base_url.hostname not in {
    "localhost",
    "127.0.0.1",
    "::1",
}:
    sys.exit("E2E_BASE_URL harus menunjuk ke aplikasi lokal (localhost/loopback).")

if not USER_PASSWORD or not ADMIN_PASSWORD:
    sys.exit("E2E_USER_PASSWORD dan E2E_ADMIN_PASSWORD belum diisi di berkas .env.")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myportofolio.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from main.models import Award, Experience  # noqa: E402


def setup_users():
    user, _ = User.objects.get_or_create(username="burhan_test")
    user.set_password(USER_PASSWORD)
    user.is_active = True
    user.is_superuser = False
    user.is_staff = False
    user.save()

    admin, _ = User.objects.get_or_create(username="admin_test")
    admin.set_password(ADMIN_PASSWORD)
    admin.is_active = True
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()


def login(driver, wait, username, password):
    driver.get(f"{BASE_URL}/login/")
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    wait.until(EC.url_to_be(f"{BASE_URL}/"))
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "nav-user")))


def award_card(wait, title):
    return wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(concat(' ', normalize-space(@class), ' '), ' award-card ')]"
                f"[.//h2[normalize-space()='{title}']]",
            )
        )
    )


def assert_forbidden(driver, path):
    driver.get(f"{BASE_URL}{path}")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "403" in body_text or "Forbidden" in body_text, (
        f"Expected {path} to be forbidden for a normal user."
    )


def assert_post_forbidden(driver, path):
    csrf_cookie = driver.get_cookie("csrftoken")
    assert csrf_cookie, "Expected the browser to have a CSRF cookie."
    status_code = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        fetch(arguments[0], {
            method: "POST",
            credentials: "same-origin",
            headers: {"X-CSRFToken": arguments[1]}
        }).then(response => done(response.status)).catch(() => done(0));
        """,
        f"{BASE_URL}{path}",
        csrf_cookie["value"],
    )
    assert status_code == 403, f"Expected POST {path} to return 403, got {status_code}."


def assert_xss_payload_is_text(driver, wait, page_path, card_selector, body_selector):
    driver.get(BASE_URL)
    driver.execute_script("localStorage.removeItem(arguments[0]);", XSS_STORAGE_KEY)
    driver.get(f"{BASE_URL}{page_path}")

    def find_payload_card(browser):
        for card in browser.find_elements(By.CSS_SELECTOR, card_selector):
            headings = card.find_elements(By.TAG_NAME, "h2")
            if headings and headings[0].get_attribute("textContent") == XSS_PAYLOAD:
                return card
        return False

    card = wait.until(find_payload_card)
    body = card.find_element(By.CSS_SELECTOR, body_selector)
    assert body.get_attribute("textContent") == XSS_PAYLOAD
    assert not card.find_elements(By.TAG_NAME, "img"), (
        f"The {page_path} payload became a real image element."
    )

    # Give an injected image handler time to run; it would leave this marker.
    marker = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        const key = arguments[0];
        window.setTimeout(() => done(localStorage.getItem(key)), 750);
        """,
        XSS_STORAGE_KEY,
    )
    assert marker is None, f"Stored XSS executed on {page_path}: {marker}"


def main():
    setup_users()
    test_award = Award.objects.create(
        title=f"E2E Selenium Award {uuid.uuid4().hex[:10]}",
        description="Temporary award created by the Selenium E2E test.",
        issuer="E2E test",
        date_received=date.today(),
    )
    test_experience = Experience.objects.create(
        title=f"E2E Selenium Experience {uuid.uuid4().hex[:10]}",
        category="freelance",
    )
    # Seed legacy-style data directly so the browser verifies output escaping
    # even for records that predate server-side form validation.
    xss_award = Award.objects.create(
        title=XSS_PAYLOAD,
        description=XSS_PAYLOAD,
        issuer=XSS_PAYLOAD,
        date_received=date.today(),
    )
    xss_experience = Experience.objects.create(
        title=XSS_PAYLOAD,
        description=XSS_PAYLOAD,
        category="freelance",
        keyfeatures=[XSS_PAYLOAD],
    )

    driver = None
    try:
        options = webdriver.ChromeOptions()
        if "--headless" in sys.argv:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        else:
            options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        try:
            driver = webdriver.Chrome(options=options)
        except WebDriverException as error:
            sys.exit(f"Chrome/Chromedriver tidak dapat dijalankan: {error}")

        wait = WebDriverWait(driver, 10)

        # 1. CSRF token tersedia di form login dan cookie browser.
        try:
            driver.get(f"{BASE_URL}/login/")
        except WebDriverException:
            print(
                f"Server belum berjalan di {BASE_URL}. "
                "Jalankan 'python manage.py runserver' terlebih dahulu."
            )
            return
        csrf = wait.until(EC.presence_of_element_located((By.NAME, "csrfmiddlewaretoken")))
        assert csrf.get_attribute("value")
        assert driver.get_cookie("csrftoken")
        print("[PASS] CSRF token dan cookie terverifikasi")

        # 2. Login akun biasa dan pastikan cookie sesi serta last_login terpasang.
        login(driver, wait, "burhan_test", USER_PASSWORD)
        assert driver.get_cookie("sessionid")
        assert driver.get_cookie("last_login")
        assert "Sesi Terakhir Login" in driver.page_source or "Last Login" in driver.page_source
        print("[PASS] Login user biasa dan cookie sesi berhasil")

        # 3. Akun biasa tidak dapat membuat Award/Experience atau mengubah Experience.
        assert_forbidden(driver, "/award/add/")
        assert_forbidden(driver, "/experience/add/")
        assert_forbidden(driver, f"/experience/{test_experience.pk}/")
        assert_post_forbidden(driver, f"/experience/{test_experience.pk}/delete/")
        assert Experience.objects.filter(pk=test_experience.pk).exists()
        assert_post_forbidden(driver, f"/award/{test_award.pk}/delete/")
        assert Award.objects.filter(pk=test_award.pk).exists()
        print("[PASS] Create/delete Award dan create/update/delete Experience dibatasi (403)")

        # 4. Akun biasa dapat memberi dan membatalkan star pada Award.
        driver.get(f"{BASE_URL}/award/")
        card = award_card(wait, test_award.title)
        card.find_element(By.CLASS_NAME, "button-star").click()
        modal = wait.until(
            EC.visibility_of_element_located((By.ID, f"star-award-{test_award.pk}"))
        )
        modal.find_element(By.CLASS_NAME, "star-confirm-button").click()
        wait.until(EC.url_to_be(f"{BASE_URL}/award/"))

        card = award_card(wait, test_award.title)
        star_button = card.find_element(By.CLASS_NAME, "button-star")
        wait.until(lambda _: "is-starred" in star_button.get_attribute("class"))
        assert card.find_element(By.CLASS_NAME, "star-count").text == "1"

        star_button.click()
        modal = wait.until(
            EC.visibility_of_element_located((By.ID, f"star-award-{test_award.pk}"))
        )
        modal.find_element(By.CLASS_NAME, "star-confirm-button").click()
        wait.until(EC.url_to_be(f"{BASE_URL}/award/"))

        card = award_card(wait, test_award.title)
        star_button = card.find_element(By.CLASS_NAME, "button-star")
        wait.until(lambda _: "is-starred" not in star_button.get_attribute("class"))
        assert card.find_element(By.CLASS_NAME, "star-count").text == "0"
        print("[PASS] Star dan unstar Award berhasil")

        # 5. Logout menghapus last_login dan mengembalikan tautan login.
        driver.get(f"{BASE_URL}/logout/")
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Login")))
        cookie_last_login = driver.get_cookie("last_login")
        assert cookie_last_login is None or cookie_last_login["value"] == ""
        print("[PASS] Logout dan pembersihan cookie berhasil")

        # 6. Anonymous visitors see legacy XSS payloads as literal text.
        assert_xss_payload_is_text(
            driver, wait, "/award/", ".award-card", ".award-description"
        )
        print("[PASS] Stored XSS Award tampil sebagai teks untuk pengunjung anonim")
        assert_xss_payload_is_text(
            driver,
            wait,
            "/experience/",
            ".experience-timeline-item",
            ".experience-description",
        )
        print("[PASS] Stored XSS Experience tampil sebagai teks untuk pengunjung anonim")

        # 7. Superuser dapat membuka form create Award dan Experience.
        login(driver, wait, "admin_test", ADMIN_PASSWORD)
        assert "admin_test" in driver.find_element(By.CLASS_NAME, "nav-user").text

        driver.get(f"{BASE_URL}/award/add/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.award-form")))
        wait.until(EC.presence_of_element_located((By.NAME, "title")))

        driver.get(f"{BASE_URL}/experience/add/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.award-form")))
        wait.until(EC.presence_of_element_located((By.NAME, "title")))
        driver.get(f"{BASE_URL}/experience/{test_experience.pk}/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form.award-form")))
        wait.until(EC.presence_of_element_located((By.NAME, "title")))
        print("[PASS] Superuser dapat membuka form Award dan Experience")

        print("\nSemua pengujian E2E berhasil!")
    finally:
        if driver is not None:
        driver.quit()
        test_award.delete()
        test_experience.delete()
        xss_award.delete()
        xss_experience.delete()


if __name__ == "__main__":
    main()
