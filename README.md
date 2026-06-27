# 🎓 School AI ERP Assistant

An **Agentic AI-powered School ERP Assistant** built using **FastAPI**, **Google Gemini**, and **SQLite**. The assistant understands natural language queries, automatically plans execution, selects the appropriate ERP tools, maintains conversation memory, and returns intelligent, structured responses.

---

## ✨ Features

- 🤖 AI-powered intent detection using Google Gemini
- 🧠 Agent planning with execution reasoning
- 🔧 Automatic ERP tool selection (no keyword routing)
- 💬 SQLite-based conversation memory
- 📚 Five ERP modules:
  - Attendance
  - Marks
  - Fees
  - Homework
  - Timetable
- ⚡ Multi-step task execution
- 📈 Academic Performance Summary
- 📝 Structured JSON responses
- 📜 Interaction logging
- 📖 Swagger API Documentation
- 🧪 Pytest test suite
- 🐳 Docker support

---

## 🛠 Tech Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.11 |
| Framework | FastAPI |
| AI Model | Google Gemini 2.0 Flash |
| SDK | google-generativeai |
| Database | SQLite |
| Mock Data | JSON |
| Validation | Pydantic v2 |
| Testing | Pytest |
| Deployment | Docker |

---

# 📂 Project Structure

```text
school-ai-assistant/

│
├── app/
│   ├── api/
│   ├── agents/
│   ├── services/
│   ├── tools/
│   ├── memory/
│   ├── models/
│   ├── utils/
│   ├── config.py
│   └── main.py
│
├── mock_data/
├── logs/
├── data/
├── tests/
│
├── requirements.txt
├── Dockerfile
├── README.md
├── architecture.md
└── .env.example
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/your-username/school-ai-assistant.git
cd school-ai-assistant
```

## Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Copy

```bash
cp .env.example .env
```

or on Windows

```powershell
copy .env.example .env
```

Update

```env
GEMINI_API_KEY=YOUR_API_KEY
```

---

# ▶️ Run the Project

```bash
uvicorn app.main:app --reload
```

Application

```
http://localhost:8000
```

Swagger

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# 🔐 Environment Variables

| Variable | Description |
|-----------|-------------|
| GEMINI_API_KEY | Google Gemini API Key |
| GEMINI_MODEL | Gemini model name |
| DB_PATH | SQLite database path |
| LOG_LEVEL | Logging level |
| DEFAULT_STUDENT_ID | Default student |
| MAX_HISTORY_MESSAGES | Conversation history length |

---

# 📡 API Endpoints

| Method | Endpoint | Description |
|----------|-----------|------------|
| POST | `/api/v1/chat` | Chat with AI Assistant |
| GET | `/api/v1/chat/history` | Retrieve conversation history |
| GET | `/health` | Health Check |

---

# 💬 Example Request

```http
POST /api/v1/chat
```

```json
{
    "message":"Show my attendance this month.",
    "student_id":"STU001"
}
```

---

# ✅ Example Response

```json
{
    "intent":"Attendance",
    "tool":"Attendance Tool",
    "response":"Your attendance is 92%.",
    "status":"Good"
}
```

---

# 🧠 Supported ERP Tools

## Attendance

- Attendance Percentage
- Monthly Attendance
- Missed Classes

---

## Marks

- Subject Marks
- Highest Score
- Average Marks

---

## Fees

- Pending Fees
- Payment History
- Fee Status

---

## Homework

- Pending Homework
- Due Assignments
- Today's Homework

---

## Timetable

- Today's Timetable
- Tomorrow's Timetable
- Subject Schedule

---

# ⭐ Bonus Features

### Multi-step Tool Execution

Example

```
Show my attendance, Mathematics marks and pending fees.
```

The AI automatically calls multiple ERP tools and combines the responses.

---

### Academic Performance Summary

Generates

- Overall Performance
- Attendance Summary
- Strong Subjects
- Weak Subjects
- AI Suggestions

---

# 🧪 Testing

Run all tests

```bash
pytest
```

Verbose mode

```bash
pytest -v
```

Run specific tests

```bash
pytest tests/test_chat.py
pytest tests/test_tools.py
```

---

# 🐳 Docker

Build

```bash
docker build -t school-ai-assistant .
```

Run

```bash
docker run -p 8000:8000 --env-file .env school-ai-assistant
```

---

# 📜 Logging

Every interaction stores

- Timestamp
- User Query
- Detected Intent
- Execution Plan
- Selected Tool(s)
- Execution Time
- Response

Logs are stored in

```
logs/agent_logs.json
```

---

# 🔄 AI Workflow

```
User
   │
   ▼
POST /chat
   │
   ▼
Conversation Memory
   │
   ▼
Gemini Planner
   │
   ▼
Execution Plan
   │
   ▼
Tool Selection
   │
   ▼
ERP Tool Execution
   │
   ▼
Gemini Response Generation
   │
   ▼
Save Memory & Logs
   │
   ▼
JSON Response
```

---

# 📖 Documentation

- Swagger UI → `/docs`
- ReDoc → `/redoc`
- Architecture → `architecture.md`

---

# 🔮 Future Improvements

- JWT Authentication
- Role-Based Access Control
- PostgreSQL Integration
- Real ERP APIs
- Voice Assistant Support
- OCR for Documents
- Multi-language Support
- Teacher & Parent Dashboards

---

# 👨‍💻 Author

**Nitin Chauhan**

B.Tech – Artificial Intelligence & Data Science

AI/ML | Generative AI | FastAPI | Python | Agentic AI

GitHub: https://github.com/nitinc264

---
