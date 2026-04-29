# Election Compass

Election Compass is an interactive civic education platform designed to help users understand the election process in a clear, structured, and guided manner.

The system transforms complex procedural information into an intuitive learning experience by combining assistant-driven interaction with organized explanations of stages, timelines, and outcomes.

---

## Live Application

https://election-compass-1067381608763.asia-south1.run.app

---

## Problem

While many individuals participate in elections, a significant number lack clarity on how the process operates in practice. Key aspects such as pre-election preparation, voter eligibility, voting procedures, and result declaration are often fragmented or difficult to interpret.

This gap leads to limited understanding of the full electoral process.

---

## Solution

Election Compass addresses this by providing a structured, assistant-based interface that allows users to explore the election process through guided interaction rather than passive reading.

The platform enables users to:
- understand each stage of the election process  
- explore timelines and sequencing  
- ask context-specific questions  
- receive explanations in different levels of detail  

---

## Core Features

- Assistant-first interaction model  
- Context-aware response generation  
- Multiple explanation styles (simple, detailed, step-by-step)  
- Structured breakdown of election stages  
- Timeline-based process visualization  
- Guided learning flow with next-step suggestions  
- Common question shortcuts for quick access  

---

## System Design

The application is designed with a focus on clarity, usability, and minimalism:

- Reduces reliance on long-form textual content  
- Encourages exploration through guided interaction  
- Maintains a neutral and educational tone  
- Prioritizes user comprehension over feature complexity  

---

## Technology Stack

- Backend: Python (Flask)  
- Frontend: HTML, CSS, JavaScript  
- Deployment: Google Cloud Run  

---

## Project Structure

```
election-compass/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── assistant.html
│   ├── paths.html
│   ├── stages.html
│   ├── timeline.html
│   └── faq.html
│
└── static/
    ├── style.css
    └── script.js
```

---

## Deployment

The application is deployed using Google Cloud Run. Updates to the codebase require redeployment to reflect changes in the live application.

---

## Disclaimer

Election timelines, procedures, and rules may vary depending on the governing authority and region. This platform is intended for educational purposes and provides a generalized understanding of the election process.

---

## Author

Developed as part of a practical challenge focused on building user-centric, real-world applications with an emphasis on clarity, usability, and structured information delivery.
