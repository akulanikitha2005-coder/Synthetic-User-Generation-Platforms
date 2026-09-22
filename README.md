# Synthetic User Generation Platform

AI-powered synthetic user generation platform for customer research and product validation.

## Project Overview

The Synthetic User Generation Platform generates synthetic customer personas based on a product description, target audience, research objective, and selected number of personas.

The platform is designed to help with customer research and product validation by providing structured synthetic user profiles.

## Features

- Product description input
- Target audience input
- Research objective input
- Synthetic persona generation
- Multiple persona profiles
- Customer demographic information
- Personality and lifestyle information
- Buying behavior
- Interests and pain points
- Preferred platforms
- Research summary

## Persona Information

Each generated persona can contain:

- Name
- Age
- Gender
- Occupation
- Location
- Education
- Annual Income
- Marital Status
- Personality
- Lifestyle
- Interests
- Buying Behavior
- Preferred Platform
- Pain Points
- Email
- Phone
- Customer ID
- Bio
- Goal

## Technology Stack

### Frontend
- React
- Vite
- Axios
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- Pydantic

## Project Structure

```text
Synthetic-User-Generation-Platform/
│
├── Agile/
│   └── Agile_Sheet.xlsx
│
├── backend/
│   ├── main.py
│   ├── persona_generator.py
│   ├── conversation_manager.py
│   ├── groq_agent.py
│   ├── insight_agent.py
│   └── usage_scoring_agent.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── .gitattributes
├── LICENSE
└── README.md
