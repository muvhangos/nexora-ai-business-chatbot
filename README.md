# Nexora AI Business Chatbot

A responsive AI-powered business assistant built with **Python, Flask, OpenAI, HTML, CSS, and JavaScript**.

**Live demo:** https://nexora-ai-business-chatbot.onrender.com  
**GitHub repository:** https://github.com/muvhangos/nexora-ai-business-chatbot

Nexora helps customers learn about business services, ask questions, and submit quotation enquiries through a public chatbot. The application also includes a password-protected administration area for reviewing enquiries and updating their status.

## Features

- Responsive chatbot interface designed for desktop and mobile.
- OpenAI-powered answers using business-specific context.
- Demo/fallback responses when the AI service is unavailable or not configured.
- Suggested questions and chat controls.
- Customer enquiry and quotation-request form.
- Enquiry records with status management, including **Pending**, **Quoted**, and **Approved**.
- Admin login and protected dashboard for reviewing enquiries.
- Support for enquiry attachment information where enabled by the application.
- Email and WhatsApp contact links where configured.
- Environment-variable configuration for private settings.

> **Important:** AI responses depend on a valid OpenAI API key, available API quota, and correct service configuration. A fallback/demo response does not necessarily mean the live AI API is available.

## Technology stack

- **Backend:** Python, Flask
- **AI integration:** OpenAI API
- **Frontend:** HTML, CSS, JavaScript
- **Enquiry storage:** CSV-based storage in the current implementation
- **Production server:** Gunicorn
- **Hosting:** Render

## Try the live application

1. Open the [Nexora chatbot](https://nexora-ai-business-chatbot.onrender.com).
2. Ask a question or submit a test quotation enquiry.
3. Sign in to the admin area using the administrator credentials configured for the deployment.
4. Review the enquiry and test its status-update workflow.

The admin route is:

`https://nexora-ai-business-chatbot.onrender.com/admin`

Keep the admin route and credentials private. Never publish administrator passwords or API keys in this README.

## Run locally on Windows

Open PowerShell and navigate to your project folder:

```powershell
cd "$HOME\Downloads\ai-business-chatbot\ai-business-chatbot"
```

Create and activate a virtual environment if you do not already have one:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

If `.env` does not already exist, create it from the example file:

```powershell
Copy-Item .env.example .env
```

**If you already have a working `.env`, do not overwrite it.**

Open the project in VS Code:

```powershell
code .
```

## Environment configuration

Configure the following variables in your private `.env` file, using values appropriate for your environment:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
SECRET_KEY=your_long_random_secret
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD_HASH=your_generated_password_hash
```

The administrator password hash should be generated with Werkzeug's `generate_password_hash()` function. Use a strong, unique `SECRET_KEY`.

Never commit `.env`, API keys, passwords, secret keys, password hashes, or real customer enquiry records to GitHub.

## Start the local application

With the virtual environment activated, run:

```powershell
python app.py
```

Open the customer interface:

`http://127.0.0.1:5000`

Open the admin dashboard:

`http://127.0.0.1:5000/admin`

The dashboard should require administrator authentication before showing customer enquiries.

## Deploy to Render

This repository is configured for deployment through Render's service settings.

Typical commands:

**Build command**

```bash
pip install -r requirements.txt
```

**Start command**

```bash
gunicorn app:app
```

Set the required environment variables in the Render service's **Environment** settings:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `OPENAI_API_KEY` (needed for OpenAI-powered replies)
- `OPENAI_MODEL` (for example, `gpt-4.1-mini`)

After deployment, test the public chatbot, enquiry submission, admin login, status updates, and logout. The Render service may be configured for manual deployment, so a GitHub commit does not necessarily deploy automatically; check the service's Auto-Deploy setting and deployment status.

## Important production and data-storage notes

- The current application uses CSV-based enquiry storage. A CSV file stored on a hosting service's temporary filesystem may be lost or replaced during restarts, redeployments, or instance replacement.
- **Do not assume that CSV storage is durable or shared across instances.** For reliable production lead management, migrate enquiry records to a persistent database such as PostgreSQL, or configure and verify an appropriate persistent disk.
- Test with a clearly identified test enquiry before relying on the dashboard for real customer leads.
- Protect customer contact details and attachments. Limit administrator access and establish suitable privacy, retention, and deletion practices.
- Keep Flask debug mode disabled in production.
- Monitor OpenAI API usage, quota, errors, and rate limits.

## Project structure

```text
ai-business-chatbot/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    ├── index.html
    ├── admin.html
    └── admin_login.html
```

## Security checklist

- Keep `.env` out of version control.
- Keep real customer records and uploaded files out of GitHub.
- Store administrator passwords as hashes, not plaintext.
- Use HTTPS and secure environment variables in production.
- Restrict the admin dashboard to authorized users.
- Verify storage persistence before using the application for business-critical leads.

## Author

**Samuel Muvhango**  
Full-Stack Web Developer | IT & Systems Engineer

---

Built as a practical full-stack project combining a customer-facing AI assistant with business enquiry management.
