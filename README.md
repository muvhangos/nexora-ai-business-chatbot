# Nova AI — Business Chatbot

A polished, responsive AI business assistant built with Python, Flask, OpenAI, HTML, CSS, and JavaScript.

## Features

- Responsive dark glassmorphism interface with glowing accents
- OpenAI-powered answers grounded in your business context
- Suggested prompts, typing indicator, and clear-chat control
- Safe DOM rendering for chat messages (uses `textContent`)
- Input validation and friendly API error messages
- API key stays on the server in `.env`

## 1. Requirements

- Python 3.10 or newer
- An OpenAI API key from https://platform.openai.com/api-keys

## 2. Install on Windows PowerShell

```powershell
cd $HOME\Documents
# If you downloaded and extracted this folder, change into its location:
cd .\ai-business-chatbot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
code .
```

Open `.env` and replace `your_openai_api_key_here` with your own API key. Never publish your real `.env` file or paste the key into frontend JavaScript.

If PowerShell blocks virtual-environment activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## 3. Run the app

With the virtual environment active:
```powershell
python app.py
```

Open http://127.0.0.1:5000 in your browser. Keep the terminal open while testing.

## 4. Customize business details

Edit `BUSINESS_CONTEXT` near the top of `app.py`. Update the business name, services, prices, location, and policies to match the real business. Do not claim that a service, price, or guarantee exists unless the business confirms it.

## 5. Deploying

For a production deployment, set `OPENAI_API_KEY` and `OPENAI_MODEL` as environment variables in your hosting provider. Install requirements and use a WSGI server, for example:

```bash
gunicorn app:app
```

Do not use Flask's `debug=True` development server in production. Before public launch, add rate limiting, authentication/admin controls if needed, privacy and retention notices, and usage/cost monitoring. The demo does not save conversations to a database.

## Project structure

```text
ai-business-chatbot/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html
└── static/
    └── style.css
```
