# Experience AJAX Implementation Plan

**Goal:** Complete the user's Assignment 5 requirements using the existing Award and Experience flows, with TDD.

**Architecture:** Keep skeleton pages and manually assembled JsonResponse endpoints. Use the existing popover modal style for Experience creation and editing, ModelForms for validation, server permission checks, CSRF-protected fetch requests, and textContent/value for untrusted text.

**Tech stack:** Django, vanilla JavaScript, Selenium, Django test databases.

**Spec:** The assignment checklist supplied in this conversation and the request to apply Experience modals/AJAX with TDD.

**Constraints:** Editor may update only; admin may create/update; regular users and visitors may read. Award alone has stars in Assignment 4. Keep existing non-AJAX routes compatible. No new runtime dependencies.

## Task 1: Experience JSON writes

- [x] Write behavioral tests in `main/test_ajax.py` for create 201, invalid 400, forbidden 403, update 200, missing item 404, GET 405, sanitization, and CSRF.
- [x] Run `env/bin/python manage.py test main.test_ajax`; observe missing endpoint failures.
- [x] Add `create_experience_ajax(request)` and `update_experience_ajax(request, experience_id)` in `main/views.py` and routes in `main/urls.py`.
- [x] Include raw `category` in Experience JSON so the edit select can be prefilled.
- [x] Verify tests pass and protect existing Award stars/search/role behavior with endpoint tests.

## Task 2: Experience modals and failure notifications

- [x] Add browser checks in `scripts/check_ajax_browser.py` for prefilled edit, create/update without navigation, validation toasts, all four roles, safe text rendering, debounce, loading/empty/error states, and load-failure toasts on both list pages.
- [x] Run browser checks against a temporary Django test database; observe missing UI behavior failures.
- [x] Add `templates/components/experience_form_modal.html` and prefixed create/update ModelForms in the list view.
- [x] Replace Experience navigation with an accessible edit button, submit forms with fetch and CSRF, retain input on validation failure, close on success, and refresh the current search.
- [x] Add load-failure toasts to Award and Experience; ignored aborts must not show errors.
- [x] Verify browser checks pass.

## Task 3: Execution verification

- [x] Run `env/bin/python manage.py test`, `manage.py check`, and `git diff --check`.
- [x] Start `manage.py runserver --noreload` locally, read both list pages and endpoints, then stop the server.
- [x] Document test commands and the completed assignment checklist in README.

## Review focus

- Missing CSRF must reject writes; valid modal CSRF must permit authorized writes.
- Admin has both forms on one page; field IDs must be unique.
- Validation/network failures retain modal values and allow retry.
- Search aborts must not flash an error toast; failed refresh after successful writes must report a loading failure.
- Legacy stored HTML must render as text, including key features and server error messages.

## Execution record

Implementation tests use temporary databases. At the user's later request, the completed changes are being recorded as Conventional Commits with separately verified RED test commits and GREEN implementation commits. Existing history is preserved; no deployment is involved.

- Backend RED: new Experience endpoints returned 404; raw category was absent. GREEN: 13 AJAX backend tests pass.
- Browser RED: Experience modals were absent and both list loaders lacked failure toasts. Implemented modal UI, CSRF submission, prefill, safe rendering, and failure notifications.
- Ruling: preserve the latest commit's POST-only legacy Award routes; update stale GET-form tests to reflect that behavior. The new Experience AJAX routes coexist with its existing routes.
- Browser test correction: toast text must be checked after its entrance animation becomes visible; immediate Selenium `.text` can be empty during the CSS transition.
- Final review: no critical/important findings. Added coverage for successful writes followed by failed refresh and retry while preserving the current search.
- Additional RED: immediate initial fetch failure raised `showToast is not defined` before the footer script loaded. Fixed by starting both initial list loads on DOMContentLoaded.
- Final GREEN: full Django suite 82/82; browser suite 9/9, including all four roles, initial loading failures, write/refresh failure/retry behavior, and permitted deletion from both edit modals. `manage.py check` and `git diff --check` pass.
- Runserver verification: `/award/`, `/experience/`, `/api/awards/`, and `/api/experiences/` returned HTTP 200 for anonymous requests; Award JSON includes star count and false current-user star status. Local server stopped after verification.
