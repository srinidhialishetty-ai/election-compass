# Election Compass

Election Compass is an interactive civic education platform that helps users understand the election process through clear explanations, guided questions, and structured learning paths.

The application focuses on neutral public-process education. It explains common election stages, timeline order, voting-day context, and post-voting outcomes without providing partisan guidance.

## Live Application

https://election-compass-1067381608763.asia-south1.run.app

## Problem

Many voters and first-time learners find election procedures difficult to follow because preparation, eligibility, voting, counting, and result confirmation are often explained separately.

Election Compass reduces that confusion by presenting the process as a guided learning flow.

## Solution

The platform provides an assistant-led interface where users can ask focused questions and receive explanations in distinct styles:

- Simple Language
- Detailed Explanation
- Step-by-Step Learning
- Timeline Format

It also includes dedicated pages for learning paths, process stages, timeline context, and frequently asked questions.

## Core Features

- Assistant-first interaction model
- Context-aware response generation
- Multiple explanation styles
- Structured breakdown of election stages
- Timeline-based process visualization
- Guided follow-up suggestions
- Neutral civic education tone

## Google Services Used

- Google Gemini API for AI-assisted civic process explanations
- Google Cloud Run for deployment
- Google Analytics support through an optional `GOOGLE_ANALYTICS_ID` environment variable

If Gemini is unavailable or `GEMINI_API_KEY` is not configured, the assistant uses local fallback responses so the app remains usable.

## Technology Stack

- Backend: Python and Flask
- Frontend: HTML, CSS, JavaScript
- AI service: Google Gemini API
- Deployment: Google Cloud Run
- Testing: pytest

## Project Structure

```text
election-compass/
|-- app.py
|-- requirements.txt
|-- Dockerfile
|-- README.md
|-- .gitignore
|-- test_app.py
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- assistant.html
|   |-- paths.html
|   |-- stages.html
|   |-- timeline.html
|   `-- faq.html
`-- static/
    |-- style.css
    `-- script.js
```

## Environment Variables

- `GEMINI_API_KEY`: Required only for live Gemini-generated assistant responses.
- `GEMINI_MODEL`: Optional Gemini model override. Defaults to `gemini-1.5-flash`.
- `FLASK_SECRET_KEY`: Optional Flask session secret for deployed environments.
- `GOOGLE_ANALYTICS_ID`: Optional Google Analytics measurement ID.
- `PORT`: Optional local or deployment port. Defaults to `8080`.
- `FLASK_DEBUG`: Set to `1` only for local debugging.

## Local Setup

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080` after the server starts.

## Testing

Run the test suite with:

```bash
pytest
```

Latest local result: all tests pass with no real Gemini API call required.

The tests verify:

- the home route returns `200`
- the assistant page route returns `200`
- the assistant API route returns `200`
- Gemini can be mocked safely during tests
- missing Gemini configuration falls back gracefully

## Security

API keys must never be hardcoded in the repository. Configure `GEMINI_API_KEY` and any deployment secrets through environment variables or the hosting platform's secret management system.

The `.gitignore` excludes local environment files, Python caches, virtual environments, and dependency folders.

## Deployment

The application is deployed on Google Cloud Run. Code changes require redeployment before they appear in the live application.

## Disclaimer

Election timelines, procedures, and rules may vary by governing authority and region. Election Compass is intended for general educational use and should be supplemented with official election authority guidance when exact rules or dates are needed.
