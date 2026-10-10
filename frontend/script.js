"use strict";

const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.getElementById("certificateForm");
const eventNameInput = document.getElementById("eventName");
const recipientsContainer = document.getElementById("recipientsContainer");
const addRecipientButton = document.getElementById("addRecipient");
const generateButton = document.getElementById("generateButton");
const formMessage = document.getElementById("formMessage");

const jobSection = document.getElementById("jobSection");
const jobIdElement = document.getElementById("jobId");
const jobStatusElement = document.getElementById("jobStatus");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const totalCountElement = document.getElementById("totalCount");
const successCountElement = document.getElementById("successCount");
const failureCountElement = document.getElementById("failureCount");

const certificatesSection = document.getElementById("certificatesSection");
const certificatesList = document.getElementById("certificatesList");
const refreshStatusButton = document.getElementById("refreshStatus");

const FINAL_STATUSES = new Set([
    "COMPLETED",
    "COMPLETED_WITH_ERRORS",
    "FAILED"
]);

let currentJobId = null;
let pollingTimer = null;
let isSubmitting = false;
let isRefreshing = false;

// Display a message to the user.
function showMessage(message, type = "") {
    formMessage.textContent = message;
    formMessage.className = "message";

    if (type) {
        formMessage.classList.add(type);
    }
}

// Send a request to FastAPI.
async function apiRequest(url, options = {}) {
    let response;

    try {
        response = await fetch(url, options);
    } catch {
        throw new Error(
            "Cannot connect to FastAPI. Make sure the backend is running."
        );
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        if (Array.isArray(data.detail)) {
            throw new Error(
                data.detail.map(item => item.msg).join("; ")
            );
        }

        throw new Error(
            data.detail || `Request failed with status ${response.status}`
        );
    }

    return data;
}

// Enable Remove only when there is more than one recipient.
function updateRemoveButtons() {
    const rows = recipientsContainer.querySelectorAll(".recipient-row");

    rows.forEach(row => {
        const button = row.querySelector(".remove-button");

        if (button) {
            button.disabled = rows.length === 1;
        }
    });
}

// Add another recipient row.
function addRecipientRow() {
    const row = document.createElement("div");
    row.className = "recipient-row";

    const nameField = document.createElement("div");
    nameField.className = "field";

    const nameLabel = document.createElement("label");
    nameLabel.textContent = "Recipient Name";

    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.className = "recipient-name";
    nameInput.placeholder = "Full name";
    nameInput.maxLength = 100;
    nameInput.required = true;

    nameField.append(nameLabel, nameInput);

    const emailField = document.createElement("div");
    emailField.className = "field";

    const emailLabel = document.createElement("label");
    emailLabel.textContent = "Email Address";

    const emailInput = document.createElement("input");
    emailInput.type = "email";
    emailInput.className = "recipient-email";
    emailInput.placeholder = "name@example.com";
    emailInput.required = true;

    emailField.append(emailLabel, emailInput);

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-button";
    removeButton.textContent = "Remove";

    removeButton.addEventListener("click", () => {
        row.remove();
        updateRemoveButtons();
    });

    row.append(nameField, emailField, removeButton);
    recipientsContainer.appendChild(row);

    updateRemoveButtons();
}

// Collect all recipient data.
function collectRecipients() {
    return Array.from(
        recipientsContainer.querySelectorAll(".recipient-row")
    ).map(row => ({
        name: row.querySelector(".recipient-name").value.trim(),
        email: row.querySelector(".recipient-email").value.trim()
    }));
}

// Display the job section.
function revealJobSection() {
    jobSection.hidden = false;
}

// Stop checking job progress.
function stopPolling() {
    if (pollingTimer !== null) {
        window.clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

// Retrieve and display certificates.
async function loadCertificates() {
    const certificates = await apiRequest(
        `${API_BASE_URL}/api/jobs/${currentJobId}/certificates`
    );

    certificatesList.replaceChildren();

    certificates.forEach(certificate => {
        const item = document.createElement("div");
        item.className = "certificate-item";

        const info = document.createElement("div");
        info.className = "certificate-info";

        const name = document.createElement("strong");
        name.textContent = certificate.recipient_name;

        const email = document.createElement("p");
        email.textContent = certificate.recipient_email;

        const status = document.createElement("span");
        status.className = "status-label";
        status.textContent = certificate.status;

        if (certificate.status === "GENERATED") {
            status.classList.add("status-generated");
        } else if (certificate.status === "FAILED") {
            status.classList.add("status-failed");
        }

        info.append(name, email, status);

        if (certificate.error_message) {
            const errorMessage = document.createElement("p");
            errorMessage.className = "message error";
            errorMessage.textContent =
                `Error: ${certificate.error_message}`;
            info.appendChild(errorMessage);
        }

        item.appendChild(info);

        if (certificate.status === "GENERATED") {
            const downloadButton = document.createElement("button");
            downloadButton.type = "button";
            downloadButton.className = "secondary-button";
            downloadButton.textContent = "Download PDF";

            downloadButton.addEventListener("click", () => {
                const url =
                    `${API_BASE_URL}/api/certificates/${certificate.certificate_id}`;

                window.open(url, "_blank", "noopener");
            });

            item.appendChild(downloadButton);
        }

        certificatesList.appendChild(item);
    });

    certificatesSection.hidden = false;
}

// Get the latest job status and progress.
async function refreshJobStatus() {
    if (currentJobId === null || isRefreshing) {
        return null;
    }

    isRefreshing = true;

    try {
        const job = await apiRequest(
            `${API_BASE_URL}/api/jobs/${currentJobId}`
        );

        revealJobSection();

        jobIdElement.textContent = job.job_id ?? currentJobId;
        jobStatusElement.textContent = job.status;

        totalCountElement.textContent = job.total_count;
        successCountElement.textContent = job.success_count;
        failureCountElement.textContent = job.failure_count;

        const progress = Math.max(
            0,
            Math.min(100, Number(job.progress_percent) || 0)
        );

        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}% completed`;

        if (FINAL_STATUSES.has(job.status)) {
            stopPolling();
            await loadCertificates();

            if (job.status === "COMPLETED") {
                showMessage(
                    "Success! All certificates have been generated.",
                    "success"
                );
            } else if (job.status === "FAILED") {
                showMessage(
                    "The job failed. Review the certificate results.",
                    "error"
                );
            } else {
                showMessage(
                    "Generation finished with some failures. Review the results.",
                    "error"
                );
            }
        }

        return job.status;
    } finally {
        isRefreshing = false;
    }
}

// Refresh job status every two seconds.
function startPolling() {
    if (pollingTimer !== null) {
        return;
    }

    pollingTimer = window.setInterval(async () => {
        try {
            const status = await refreshJobStatus();

            if (status && FINAL_STATUSES.has(status)) {
                stopPolling();
            }
        } catch (error) {
            stopPolling();
            showMessage(error.message, "error");
        }
    }, 2000);
}

// Handle form submission and prevent browser navigation.
form.addEventListener("submit", async event => {
    event.preventDefault();

    if (isSubmitting) {
        return;
    }

    if (!form.reportValidity()) {
        return;
    }

    const eventName = eventNameInput.value.trim();
    const recipients = collectRecipients();

    if (!eventName) {
        showMessage("Please enter an event name.", "error");
        eventNameInput.focus();
        return;
    }

    if (
        recipients.length === 0 ||
        recipients.some(recipient => !recipient.name || !recipient.email)
    ) {
        showMessage(
            "Enter a name and valid email address for every recipient.",
            "error"
        );
        return;
    }

    isSubmitting = true;
    generateButton.disabled = true;
    stopPolling();

    try {
        showMessage("Submitting your request...");
        revealJobSection();

        certificatesSection.hidden = true;
        certificatesList.replaceChildren();

        currentJobId = null;

        jobIdElement.textContent = "Creating job...";
        jobStatusElement.textContent = "SUBMITTING";

        totalCountElement.textContent = recipients.length;
        successCountElement.textContent = "0";
        failureCountElement.textContent = "0";

        progressBar.style.width = "0%";
        progressText.textContent = "0% completed";

        // Send one bulk request to the backend.
        const job = await apiRequest(`${API_BASE_URL}/api/jobs`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                event_name: eventName,
                recipients: recipients
            })
        });

        currentJobId = job.job_id;
        jobIdElement.textContent = currentJobId;
        jobStatusElement.textContent = job.status;

        showMessage(
            `Job #${currentJobId} created. Checking status...`,
            "success"
        );

        const status = await refreshJobStatus();

        if (status && !FINAL_STATUSES.has(status)) {
            startPolling();
        }
    } catch (error) {
        revealJobSection();
        showMessage(
            error.message || "An unexpected error occurred.",
            "error"
        );
    } finally {
        isSubmitting = false;
        generateButton.disabled = false;
    }
});

// Register the remaining button handlers.
addRecipientButton.addEventListener("click", addRecipientRow);

refreshStatusButton.addEventListener("click", async () => {
    try {
        await refreshJobStatus();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

// Initialize recipient controls.
updateRemoveButtons();