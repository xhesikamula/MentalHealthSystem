# ClarityWave 🌊

**ClarityWave** is a mental health web system designed to empower users to manage their emotional well-being through personalized tools, mood tracking, journaling, event recommendations, and much more.

---

## 📖 Overview

In today's fast-paced world, managing mental health is more important than ever. ClarityWave provides users with real-time support, personalized insights, and resources to help them navigate daily challenges and improve their emotional resilience — all through an intuitive, accessible web platform.

---

## ✨ Features

- **Secure Authentication**  
  User registration and login with encrypted data storage (MySQL).

- **Mood Surveys**  
  Daily mood tracking with visual trend analysis.

- **Journaling + Sentiment Analysis**  
  Journal entries analyzed using AI tools (TextBlob, VADER) to detect emotions.

- **Personalized Recommendations**  
  Suggestions for mindfulness exercises, breathing techniques, and motivational content based on user mood.

- **Event Recommendations**  
  Nearby mental health-related events fetched via third-party APIs, based on user location (manual or geolocation).

- **Visual Dashboards**  
  Charts and graphs showing mood trends over time (Chart.js).

- **Guided Meditation & Resources**  
  Access to articles, podcasts, videos, hotlines, and breathing exercises.

- **Notifications**  
  Email reminders for surveys, journaling, mindfulness activities, and event updates.

- **Progress Tracking**  
  Personalized feedback and emotional growth insights.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML5, CSS3 (Bootstrap 5.3), JavaScript
- **Database**: MySQL
- **Visualization**: Chart.js
- **AI Tools**: TextBlob, VADER (sentiment analysis)
- **APIs**: Event discovery APIs
- **Authentication**: Flask-Login, secure password hashing

---

## 🗂️ Database Schema

- `user`
- `moodsurvey`
- `journalentry`
- `sentimentanalysis`
- `events`
- `userevents`
- `notifications`
- `recommendations`

Each table is structured to support relationships for tracking user behavior, mood history, journal analysis, event participation, and reminders.

---

## 📈 Project Goals

Create a comprehensive, user-friendly mental health platform that offers personalized, real-time support to users — making emotional health management more accessible than ever.

---

## 👥 Team

- Xhesika Mula
- Elma Ejupi

---

## 🚀 Get Started

```bash
# 1. Clone the repository
git clone https://github.com/your-username/claritywave.git

# 2. Install dependencies (Flask, MySQL connector, etc.)
pip install -r requirements.txt

# 3. Set up environment variables (.env file for secrets)

# 4. Run the app
flask run
