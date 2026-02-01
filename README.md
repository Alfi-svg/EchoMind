
# 🚀 EchoMind – Offline AI Assistant & Video Intelligence System

EchoMind is a **fully offline, production-ready AI system** designed for **AI hackathons, research, and real-world deployments**.  
The project combines **video analysis, speech processing, computer vision, and an offline chatbot with voice assistant capabilities** — all running **without cloud APIs**.

---

## ✨ Key Features

### 🎥 Echo-Vision (Video Analysis Mode)
- Upload **video files** or use **offline video sources**
- Extract audio from video
- Speech-to-Text (STT) processing
- Sentiment & contextual analysis
- AI-generated summaries and insights
- Designed for explainable AI outputs

---

### 🤖 Echo-Bot (Offline Chatbot Mode)
- Fully **offline ChatGPT-style chatbot**
- Powered by **Ollama (LLaMA 3.1)** running locally
- Persistent **chat memory per session**
- Multiple chatbot moods:
  - Default
  - Friendly
  - Tutor
  - Analyst

---

### 🎙️ Voice Assistant (Chatbot Extension)
- Record voice directly from the browser
- Offline **Speech-to-Text** using Whisper (whisper.cpp)
- AI response generated from transcribed text
- Offline **Text-to-Speech** using Piper
- Returns both:
  - Text response
  - Audio reply

---

### 🧠 Computer Vision Capabilities
Using **MediaPipe**, EchoMind supports:
- Face landmark detection
- Hand tracking
- Pose estimation
- Real-time vision processing

---

## 🛠️ Technology Stack

**Backend**
- Python
- FastAPI
- Uvicorn
- Jinja2

**AI / ML**
- Ollama (LLaMA 3.1 – offline LLM)
- Whisper.cpp (offline STT)
- Piper (offline TTS)
- MediaPipe (pose, face, hand tracking)
- OpenCV

**Frontend**
- HTML / CSS / JavaScript
- Responsive, modern UI
- Voice recording support

---

## 📂 Project Structure


EchoMind/
│
├── backend/
│   ├── routes/        # API & web routes
│   ├── services/      # STT, TTS, chatbot, vision logic
│   ├── storage/       # Chat memory, audio, results
│   └── main.py
│
├── frontend/
│   ├── templates/     # HTML templates
│   └── static/        # CSS, JS, images
│
├── requirements.txt
├── run.sh
└── README.md





## 🔒 Offline-First Design

- ❌ No cloud APIs
- ❌ No internet dependency at runtime
- ✅ All models run locally
- ✅ Ideal for privacy-sensitive use cases

---

## 🎯 Use Cases
- AI Hackathons
- Offline AI demos
- Research & experimentation
- Smart assistants
- Human-computer interaction projects
- Computer vision & speech AI systems

---

## ⚠️ Notes
- Large models and datasets are **not included** in the repository
- Configure local model paths via environment variables
- Designed for **MacOS & Windows** environments

---

## 👨‍💻 Team EchoMind
Developed with passion by **Team EchoMind**  
Focused on building **practical, offline, and explainable AI systems**.

---

⭐ If you find this project useful, feel free to star the repository!
```

