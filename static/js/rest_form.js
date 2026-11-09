document.querySelectorAll("form[data-api-method]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        let deleted = false;
        try {
            const payload = Object.fromEntries(new FormData(form));
            const csrfToken = payload.csrfmiddlewaretoken;
            delete payload.csrfmiddlewaretoken;
            if (form.hasAttribute("data-experience")) {
                try {
                    payload.keyfeatures = payload.keyfeatures.trim() ? JSON.parse(payload.keyfeatures) : [];
                } catch (error) {
                    throw new Error("Key features must be a JSON array of text values.");
                }
                payload.start_at ||= null;
                payload.ended_at ||= null;
            }
            const response = await fetch(form.action, {
                method: form.dataset.apiMethod,
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: form.dataset.apiMethod === "DELETE" ? undefined : JSON.stringify(payload),
            });
            const result = response.status === 204 ? {} : await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(Object.values(result).flat().map(String).join(" ") || `Request failed (HTTP ${response.status}).`);
            }
            if (form.dataset.apiMethod === "POST") form.reset();
            if (form.dataset.apiMethod === "DELETE") {
                deleted = true;
                form.closest("[popover]")?.hidePopover();
                document.querySelectorAll("form[data-api-method] button, [popovertarget^=delete-experience]")
                    .forEach((control) => { control.disabled = true; });
            }
            showToast("Success", "Changes saved successfully.", "success");
        } catch (error) {
            showToast("Request failed", error.message, "error");
        } finally {
            if (!deleted) button.disabled = false;
        }
    });
});
