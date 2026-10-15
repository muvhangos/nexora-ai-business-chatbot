
"use strict";

// ==========================================
// Chatbot elements
// ==========================================
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const chatMessages = document.getElementById("chat-messages");
const sendButton = document.getElementById("send-button");
const clearButton = document.getElementById("clear-chat");
const modeLabel = document.getElementById("mode-label");

// ==========================================
// Customer enquiry elements
// ==========================================
const toggleEnquiryButton =
    document.getElementById("toggle-enquiry");

const enquiryPanel = document.getElementById("enquiry-panel");
const enquiryForm = document.getElementById("enquiry-form");
const enquiryStatus = document.getElementById("enquiry-status");

const submitEnquiryButton =
    document.getElementById("submit-enquiry");

const attachmentInput =
    document.getElementById("enquiry-attachments");

const conversationHistory = [];

// ==========================================
// Display a chat message
// ==========================================
function addMessage(text, sender) {
    const article = document.createElement("article");
    article.className = `message ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = sender === "bot" ? "🤖" : "You";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    article.append(avatar, bubble);
    chatMessages.appendChild(article);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    return article;
}

// ==========================================
// Send a message to the chatbot
// ==========================================
async function sendMessage(message) {
    message = message.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";
    sendButton.disabled = true;
    modeLabel.textContent = "Assistant is thinking...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || `Server error: ${response.status}`
            );
        }

        const reply =
            data.reply || "The assistant returned an empty response.";

        conversationHistory.push(
            { role: "user", content: message },
            { role: "assistant", content: reply }
        );

        addMessage(reply, "bot");

        modeLabel.textContent =
            data.mode === "ai"
                ? "AI assistant connected"
                : "Demo assistant — API credits may be unavailable";

    } catch (error) {
        console.error("Chat error:", error);

        addMessage(
            `Sorry, I couldn't get a response. ${error.message}`,
            "bot"
        );

        modeLabel.textContent = "Connection error";

    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// ==========================================
// Chat form submission
// ==========================================
chatForm.addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(messageInput.value);
});

// ==========================================
// Suggested questions
// ==========================================
document.querySelectorAll("[data-question]").forEach(function (button) {
    button.addEventListener("click", function () {
        const question = button.dataset.question;

        if (
            question.toLowerCase().includes("request a quote")
        ) {
            enquiryPanel.hidden = false;

            toggleEnquiryButton.setAttribute(
                "aria-expanded",
                "true"
            );

            toggleEnquiryButton.textContent = "Close Enquiry Form";

            document.getElementById("service-required").focus();
        }

        sendMessage(question);
    });
});

// ==========================================
// Clear the conversation
// ==========================================
clearButton.addEventListener("click", function () {
    conversationHistory.length = 0;
    chatMessages.replaceChildren();

    addMessage(
        "Chat cleared. What can I help you with?",
        "bot"
    );

    modeLabel.textContent = "Business assistant";
    messageInput.focus();
});

// ==========================================
// Open and close the enquiry form
// ==========================================
toggleEnquiryButton.addEventListener("click", function () {
    const isOpening = enquiryPanel.hidden;

    enquiryPanel.hidden = !isOpening;

    toggleEnquiryButton.setAttribute(
        "aria-expanded",
        String(isOpening)
    );

    toggleEnquiryButton.textContent = isOpening
        ? "Close Enquiry Form"
        : "Open Enquiry Form";

    if (isOpening) {
        document.getElementById("customer-name").focus();
    }
});

// ==========================================
// Customer enquiry and file attachments
// ==========================================
enquiryForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    enquiryStatus.textContent = "";
    delete enquiryStatus.dataset.status;

    if (!enquiryForm.reportValidity()) {
        return;
    }

    // Collect customer details and selected files.
    const formData = new FormData(enquiryForm);

    // Normalise text fields without losing the file attachments.
    const textFields = [
        "name",
        "email",
        "phone",
        "service",
        "details"
    ];

    for (const fieldName of textFields) {
        const value = String(formData.get(fieldName) || "").trim();
        formData.set(fieldName, value);
    }

    // Check required fields before sending.
    const requiredFields = [
        "name",
        "email",
        "service",
        "details"
    ];

    const missingField = requiredFields.some(function (fieldName) {
        return !formData.get(fieldName);
    });

    if (missingField) {
        enquiryStatus.textContent =
            "Please complete all required fields.";

        enquiryStatus.dataset.status = "error";
        return;
    }

    // Check the file selection for an early user-friendly warning.
    // The server must still validate every file securely.
    const allowedExtensions = [
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".docx"
    ];

    if (attachmentInput) {
        const files = Array.from(attachmentInput.files || []);

        for (const file of files) {
            const fileName = file.name.toLowerCase();

            const extensionAllowed = allowedExtensions.some(
                function (extension) {
                    return fileName.endsWith(extension);
                }
            );

            if (!extensionAllowed) {
                enquiryStatus.textContent =
                    `File type not allowed: ${file.name}. ` +
                    "Please choose PDF, JPG, PNG or DOCX files.";

                enquiryStatus.dataset.status = "error";
                return;
            }
        }
    }

    submitEnquiryButton.disabled = true;
    submitEnquiryButton.textContent = "Submitting...";
    enquiryStatus.textContent = "Sending your enquiry...";

    try {
        const response = await fetch("/api/enquiry", {
            method: "POST",

            // Do not set Content-Type manually.
            // The browser adds the multipart boundary for FormData.
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to submit your enquiry."
            );
        }

        enquiryStatus.textContent =
            data.message ||
            "Your enquiry has been submitted successfully.";

        enquiryStatus.dataset.status = "success";

        // Clear customer details and selected files after success.
        enquiryForm.reset();

    } catch (error) {
        console.error("Enquiry submission error:", error);

        enquiryStatus.textContent =
            error.message ||
            "We could not submit your enquiry. Please try again.";

        enquiryStatus.dataset.status = "error";

    } finally {
        submitEnquiryButton.disabled = false;

        submitEnquiryButton.textContent =
            "Submit Enquiry / Request Quote";
    }
});
