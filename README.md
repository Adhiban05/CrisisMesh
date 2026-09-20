# CrisisMesh AI 🚨

> **AI-Powered Real-Time Disaster Response & Coordination Platform**
>
> *"From sensor data to lifesaving decisions in seconds."*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🔥 What is CrisisMesh AI?

CrisisMesh AI is a full-stack platform that centralizes disaster response intelligence. During floods, fires, or industrial accidents, it ingests data from IoT sensors, citizen reports, CCTV, and drones — then uses AI to produce structured **Incident Intelligence Cards** with automated dispatch recommendations.

### The Problem It Solves
During a disaster, information is scattered across IoT sensors, citizen messages, government systems, and field teams. CrisisMesh aggregates all sources, applies NLP + ML, and delivers a single, actionable picture to every response team.

---

## 🤖 AI Intelligence Card — The Killer Feature

Instead of a raw alert like `"Flood detected"`, CrisisMesh generates:

```
🚨 INCIDENT #1042

Location: Zone 7          Type: Flood
Severity: ████ CRITICAL

💧 Water level:    1.82 m ↑
🌧️ Rainfall:       86 mm/hr
🚧 Road blocked:   YES
👥 People:         37
🏥 Hospital:       City General (1.8 km)

🤖 AI Assessment:
"High risk of road isolation. Water levels rising at 0.3m/hr.
Intervention required within 20 minutes."

📋 Recommended Actions:
1. Dispatch rescue team to Zone 7
2. Close Road A17
3. Alert 37 residents via SMS
4. Prepare City General Hospital

Status: 🟠 RESPONSE REQUIRED
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ **Live GIS Map** | Real-time incident + team positions on Leaflet.js |
| 🤖 **AI Intelligence Cards** | Full incident analysis with context and recommendations |
| 🧠 **NLP Parser** | Extract location/type/severity from citizen text messages |
| 📈 **Prediction Engine** | Water level forecast 30 min ahead using time-series analysis |
| 🚨 **Alert Engine** | Severity scoring + automated dispatch recommendations |
| 📡 **IoT Simulator** | Simulates ESP8266 sensors (no hardware needed) |
| ⚡ **Real-time Updates** | WebSocket-based live dashboard (2-second refresh) |
| 📝 **Citizen Reports** | Text-to-incident pipeline via NLP |
| 👥 **Team Management** | Response team tracking and deployment |

---

## 🏗️ Architecture

```
Simulated IoT Sensors (Python)
          │ HTTP / WebSocket
          ▼
┌─────────────────────────────────┐
│       FastAPI Backend           │
│  ├── IoT Ingestion Layer        │
│  ├── NLP Parser                 │
│  ├── Prediction Engine (NumPy)  │
│  ├── AI Intelligence Generator  │
│  ├── Alert & Dispatch Engine    │
│  └── REST + WebSocket API       │
└─────────────────────────────────┘
          │
          ▼
    SQLite Database
          │
          ▼
┌─────────────────────────────────┐
│     Next.js 14 Frontend         │
│  ├── Live Map (Leaflet.js)      │
│  ├── Incident Intelligence Cards│
│  ├── Prediction Panel           │
│  ├── Response Team Tracker      │
│  └── Citizen Report Form        │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### 3. IoT Simulator (Optional)

```bash
cd simulator
pip install httpx
python iot_simulator.py --backend http://localhost:8000 --interval 3
```

---

## 📁 Project Structure

```
crisismesh/
├── backend/
│   ├── main.py                  # FastAPI app + WebSocket
│   ├── database.py              # SQLite + SQLAlchemy
│   ├── requirements.txt
│   ├── models/
│   │   └── incident.py          # DB models
│   ├── routers/
│   │   ├── incidents.py
│   │   ├── sensors.py
│   │   ├── teams.py
│   │   └── ai.py
│   └── services/
│       ├── nlp_parser.py        # NLP text extraction
│       ├── prediction.py        # Water level prediction
│       ├── llm_summary.py       # Intelligence card generator
│       ├── alert_engine.py      # Severity + dispatch logic
│       └── simulator.py        # Background IoT simulation
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   └── types/               # TypeScript types
│   └── package.json
├── simulator/
│   └── iot_simulator.py         # Standalone IoT simulator
├── ppt/
│   └── CrisisMesh_Presentation.md  # Slide content guide
└── README.md
```

---

## 🌐 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/incidents` | GET | List all incidents (filter by severity) |
| `/api/incidents/{id}` | GET | Get incident with AI card |
| `/api/incidents/stats` | GET | Count by severity |
| `/api/sensors` | GET | Latest sensor readings |
| `/api/sensors/predictions` | GET | Water level predictions |
| `/api/teams` | GET | All response teams |
| `/api/ai/parse-report` | POST | NLP parse citizen message |
| `/api/ai/citizen-report` | POST | Full report → incident pipeline |
| `/api/ai/intelligence/{id}` | GET | Full AI intelligence card |
| `/ws` | WebSocket | Real-time broadcast (2s interval) |
| `/docs` | GET | Swagger API documentation |

---

## 🤖 AI Components

### NLP Parser
- Keyword + regex extraction (no external NLP library)
- Extracts: location, incident type, severity, people count
- Confidence scoring
- Handles noisy citizen text

### Prediction Engine
- Linear regression on water level time series
- 30-minute forecast per zone
- Risk classification: Low → Medium → High → Critical
- Trend detection: rising / stable / falling

### Intelligence Card Generator
- Template-based dynamic content generation
- Context-aware recommendations per incident type
- Risk scoring 0–100

### Alert Engine
- Multi-factor severity scoring
- Incident-type-specific action templates
- Nearest team assignment logic

---

## 📡 Hardware Integration (Production)

The simulator can be replaced with real ESP8266/ESP32 hardware:

```c
// Arduino sketch concept
#include <ESP8266WiFi.h>
#include <PubSubClient.h>  // MQTT

// Read sensor (HC-SR04 ultrasonic for water level)
float waterLevel = readUltrasonicSensor();

// Publish via MQTT
client.publish("crisismesh/sensors/WL-001",
  String("{\"value\":" + String(waterLevel) + "}").c_str());
```

The backend's MQTT bridge (configurable) routes hardware data to the same pipeline.

---

## 🎯 Evaluation Criteria Mapping

| Criteria | Implementation |
|---|---|
| **Innovation** | AI Intelligence Cards — structured incident intelligence, not just alerts |
| **Problem-Solving** | End-to-end: IoT → AI analysis → dispatch → coordination |
| **Technical Implementation** | FastAPI + Next.js + WebSocket + NLP + ML |
| **Functionality** | 5 live incident scenarios, real-time updates, citizen reports |
| **User Experience** | Dark ops-center aesthetic, intuitive severity hierarchy |
| **Real-World Impact** | Applicable to any city, any disaster, any scale |
| **Scalability** | Modular services, cloud-ready, MySQL-compatible |

---

## 👥 Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite, NumPy
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Leaflet.js, lucide-react
- **AI/ML:** Custom NLP parser, NumPy linear regression, template-driven LLM cards
- **Real-time:** WebSockets (native FastAPI)
- **IoT Simulation:** Python AsyncIO with realistic sensor models

---

## 📜 License

MIT License — feel free to use, modify, and deploy.

---

*Built during [Hackathon Name] — 24 hours of focused engineering.*
