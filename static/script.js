const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const chatMessages = document.getElementById("chat-messages");
const sendButton = document.getElementById("send-button");
const clearButton = document.getElementById("clear-chat");
const modeLabel = document.getElementById("mode-label");

// Customer enquiry form elements
const toggleEnquiryButton = document.getElementById("toggle-enquiry");
const enquiryPanel = document.getElementById("enquiry-panel");
const enquiryForm = document.getElementById("enquiry-form");
const enquiryStatus = document.getElementById("enquiry-status");
const submitEnquiryButton = document.getElementById("submit-enquiry");

const conversationHistory = [];

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

async function sendMessage(message) {
    message = message.trim();

    if (!message) return;

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

// Submit a chat message
chatForm.addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(messageInput.value);
});

// Suggested questions
document.querySelectorAll("[data-question]").forEach(function (button) {
    button.addEventListener("click", function () {
        const question = button.dataset.question;

        if (question.toLowerCase().includes("request a quote")) {
            enquiryPanel.hidden = false;
            toggleEnquiryButton.setAttribute("aria-expanded", "true");
            toggleEnquiryButton.textContent = "Close Enquiry Form";

            document.getElementById("service-required").focus();
        }

        sendMessage(question);
    });
});

// Clear the conversation without affecting customer enquiries
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

// Open and close the customer enquiry form
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

// Submit a customer enquiry or quotation request
enquiryForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    enquiryStatus.textContent = "";

    if (!enquiryForm.reportValidity()) {
        return;
    }

    const formData = new FormData(enquiryForm);

    const enquiry = {
        name: String(formData.get("name") || "").trim(),
        email: String(formData.get("email") || "").trim(),
        phone: String(formData.get("phone") || "").trim(),
        service: String(formData.get("service") || "").trim(),
        details: String(formData.get("details") || "").trim()
    };

    if (
        !enquiry.name ||
        !enquiry.email ||
        !enquiry.service ||
        !enquiry.details
    ) {
        enquiryStatus.textContent =
            "Please complete all required fields.";
        return;
    }

    submitEnquiryButton.disabled = true;
    submitEnquiryButton.textContent = "Submitting...";
    enquiryStatus.textContent = "Sending your enquiry...";

    try {
        const response = await fetch("/api/enquiry", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(enquiry)
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