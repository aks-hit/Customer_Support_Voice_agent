# 🎙️ Customer Support Voice Agent

An **AI-powered voice agent** that automates customer support using **Deepgram (STT + TTS)**, **Twilio (telephony)**, **OpenAI (NLP + reasoning)**, and **SQLite (persistent storage)**.  
It can handle **complaint booking, tracking, escalation, reporting, sentiment analysis**, and supports **bilingual conversations (English + Hindi)**.

---

## 🚀 Features
- Voice-based customer support with real-time telephony  
- Complaint booking, tracking, escalation, and reporting  
- Persistent storage with **SQLite** (customers, complaints, interactions, metrics)  
- Sentiment analysis on customer messages  
- Multi-language support (English & Hindi)  
- Export complaints to CSV reports  
- Web dashboard (Streamlit prototype)  

---

## 🏗️ Architecture

1. **Incoming Call** → Managed via **Twilio**  
2. **STT (Speech-to-Text)** → Deepgram converts voice to text  
3. **NLP & Reasoning** → OpenAI model for intent recognition, entity extraction, and sentiment analysis  
4. **Function Calls** → Complaint operations mapped to SQLite backend  
5. **Database** → Stores customers, complaints, interactions, and metrics  
6. **TTS (Text-to-Speech)** → Deepgram converts text response to natural voice  
7. **Customer** → Hears automated response over call  

---

## 📊 Flowchart

```mermaid
flowchart TB
    A[Incoming Call via Twilio] --> B[Speech to Text - Deepgram]
    B --> C[NLP and Agent Logic - OpenAI]
    C --> D[Function Calls - Complaint Handling]
    D --> E[SQLite Database]
    E --> F[Text to Speech - Deepgram]
    F --> G[Customer Hears Response via Twilio]

---

## 🏗️ Project Structure
Voice-Agent/
│── main.py # Main entrypoint (Twilio + Deepgram event handling)
│── complaints_db.py # Database models, functions, and sentiment analysis
│── config.json # Agent configuration (STT, TTS, OpenAI functions)
│── app.py # Streamlit web interface
│── reports/ # Auto-generated complaint reports (CSV)
│── requirements.txt # Python dependencies
│── .env # API keys (Deepgram, Twilio, OpenAI)











