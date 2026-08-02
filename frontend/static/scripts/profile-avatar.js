"use strict";
(() => {
    const btn = document.getElementById("upload-avatar-btn");
    const input = document.getElementById("avatar-file-input");
    if (!btn || !input) return;

    btn.addEventListener("click", () => input.click());

    input.addEventListener("change", async () => {
        const file = input.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/api/profile/photo", {
                method: "POST",
                body: formData,
            });
            if (response.ok) {
                location.reload();
            } else {
                const data = await response.json();
                alert(data.error || "Upload failed.");
            }
        } catch {
            alert("Network error during upload.");
        }
    });
})();
