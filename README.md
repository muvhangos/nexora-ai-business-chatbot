# Nexora AI Business Chatbot

A responsive AI-powered business assistant built with Python, Flask, OpenAI, HTML, CSS, and JavaScript.

Nexora helps businesses answer customer questions, provide service information, and manage customer enquiries through a web-based chatbot and a protected administration dashboard.

## Features

* Responsive chatbot interface with a dark, glowing design.
* OpenAI-powered responses using business-specific context.
* Demo responses when an OpenAI API key is not configured.
* Suggested questions and chat controls.
* Customer enquiry submission and CSV storage.
* Protected admin login using password hashing.
* Admin dashboard for viewing enquiries and updating their status.
* Email and WhatsApp contact links.
* Environment-based configuration for sensitive settings.

## Technology Stack

* Python
* Flask
* OpenAI API
* HTML, CSS, and JavaScript
* CSV-based enquiry storage
* Gunicorn for production hosting

## Requirements

* Python 3.10 or newer
* Git
* An OpenAI API key for AI-powered responses (optional if using demo responses)

## Run Locally on Windows

Open PowerShell and navigate to the project directory:

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

Create your local environment file if it does not exist:

```powershell
Copy-Item .env.example .env
```

Do not overwrite an existing `.env` file containing your working configuration.

Open the project in VS Code:

```powershell
code .
```

## Environment Configuration

Configure these variables in your private `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
SECRET_KEY=your_secure_flask_secret
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD_HASH=your_generated_password_hash
```

Replace the example values with your own configuration. The admin password hash must be generated using Werkzeug's `generate_password_hash()` function.

Keep `.env` private. Never commit real API keys, secret keys, passwords, password hashes, or customer records to GitHub.

## Start the Application

Activate the virtual environment and run:

```powershell
python app.py
```

Open the chatbot:

http://127.0.0.1:5000

Open the admin dashboard:

http://127.0.0.1:5000/admin

The admin dashboard should require authentication before allowing access to customer enquiries.

## Customize Business Information

Edit the business information and chatbot instructions in `app.py` to match the actual business, including its services, pricing, opening hours, and policies.

Verify all business details before making the chatbot publicly available.

## Deploy to Render

1. Push the project to GitHub.

2. Create a new Web Service in Render and connect the repository.

3. Set the build command to:

   ```bash
   pip install -r requirements.txt
   ```

4. Set the start command to:

   ```bash
   gunicorn app:app
   ```

5. Configure the required environment variables in Render: `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD_HASH`. Add `OPENAI_API_KEY` if AI responses are required, and set `OPENAI_MODEL` to the desired model.

6. Deploy and test the public chatbot and admin login over HTTPS.

Use a strong, stable `SECRET_KEY` for production. Never enable Flask debug mode in production.

### Important Production Considerations

* The current CSV-based enquiry storage may be lost when a hosting service replaces its temporary filesystem. Use a persistent disk or a production database for reliable customer records.
* Protect customer information and establish appropriate privacy, retention, and access-control policies.
* Consider rate limiting, monitoring, and OpenAI usage limits before public launch.
* Test login, enquiry submission, status updates, and logout after deployment.

## Project Structure

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

## Security

* `.env` is excluded from Git.
* Customer enquiry CSV files are excluded from Git.
* Admin passwords are stored as hashes rather than plaintext.
* Production deployments should use HTTPS and secure environment variables.

## Project

**Nexora AI Business Chatbot** — a Python and Flask business assistant with AI integration and enquiry management.
