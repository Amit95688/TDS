# LLM Code Deployment - Interactive Task Generator

A FastAPI application that generates, deploys, and evaluates LLM-powered applications. Students submit task briefs, the system generates code using OpenAI's API, deploys to GitHub Pages, and provides real-time evaluation.

## 🚀 Features

- **LLM-Powered Code Generation** - Uses OpenAI GPT to generate applications from natural language descriptions
- **Automatic GitHub Integration** - Creates repos, handles deployments, and manages GitHub Pages
- **Interactive Task Generator** - Beautiful web UI for task submission
- **Multi-Round Evaluation** - Support for iterative improvements (Round 1 Build → Round 2 Revise)
- **Real-time Feedback** - Instant success/error responses with generated task URLs
- **Multiple Task Templates** - Counter, Calculator, Todo, Markdown, CAPTCHA, Sales, GitHub Lookup
- **RESTful API** - Full API documentation at `/docs`

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key (from https://platform.openai.com/api-keys)
- GitHub Account with Personal Access Token
- Git installed locally

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <https://github.com/Amit95688/tds>
cd llm-code-deployment
```

### 2. Create Virtual Environment
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Playwright Browsers
```bash
playwright install
```

### 5. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
OPENAI_API_KEY=sk-proj-your-key-here
GITHUB_TOKEN=ghp_your-token-here
GITHUB_USERNAME=your-username
STUDENT_SECRET=your-secret-key
```

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for code generation | `sk-proj-...` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_...` |
| `GITHUB_USERNAME` | Your GitHub username | `Amit95688` |
| `STUDENT_SECRET` | Secret key for API verification | `st_secret_...` |
| `API_PORT` | Server port (optional) | `8000` |
| `API_HOST` | Server host (optional) | `0.0.0.0` |
| `WEBHOOK_BASE_URL` | Base URL for webhooks (optional) | `http://localhost:8000` |
| `DATABASE_URL` | Database connection string (optional) | `sqlite:///./llm_deployment.db` |

## 🚀 Running the Application

### Development Mode
```bash
python main.py
```

The server will start at `http://localhost:8000`

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📱 API Endpoints

### Home Page
```
GET /
```
Returns the interactive task generator dashboard.

### Health Check
```
GET /health
```
Returns server status.

### Submit Task (Legacy)
```
POST /submit
Content-Type: application/json

{
  "email": "student@example.com",
  "secret": "st_secret_Xw28g7mc45Qp91Yf",
  "task": "counter",
  "description": "Create a simple counter that increments and decrements"
}
```

### Build Task (Round 1)
```
POST /api/build
Content-Type: application/json

{
  "email": "student@example.com",
  "secret": "st_secret_Xw28g7mc45Qp91Yf",
  "task": "calculator",
  "brief": "Create a calculator with +, -, *, / operations",
  "checks": ["Can add numbers", "Can multiply numbers"]
}
```

### Revise Task (Round 2)
```
POST /api/revise
Content-Type: application/json

{
  "email": "student@example.com",
  "secret": "st_secret_Xw28g7mc45Qp91Yf",
  "task": "calculator-abc123",
  "round": 2,
  "nonce": "unique-id-here",
  "brief": "Add square root function to calculator",
  "checks": ["Has sqrt button", "Calculates square roots correctly"]
}
```

### Get Results
```
GET /api/results/{task_id}?round=1
```

### Get Student Tasks
```
GET /api/tasks/{email}
```

## 🌐 Using the Web Interface

1. Visit `http://localhost:8000`
2. Fill in the form:
   - **Email** (optional): Your email address
   - **Secret Key**: Your STUDENT_SECRET from `.env`
   - **Task Name**: Select from dropdown (counter, calculator, todo, etc.)
   - **Description**: Describe what the task should do
3. Click "Generate Task"
4. View the generated application in a new tab

## 📚 Available Task Types

- **counter** - Increment/decrement counter with reset
- **calculator** - Full arithmetic calculator
- **todo** - Task list with add/remove/complete
- **markdown** - Markdown to HTML converter
- **captcha** - CAPTCHA solver
- **sales** - Sales summary with CSV processing
- **github-user** - GitHub user profile lookup

## 🔐 Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` to version control
- Always use `.env.example` as template
- Keep your `STUDENT_SECRET` confidential
- GitHub token should have only `repo` and `workflow` scopes
- Rotate secrets periodically

## 🛠️ GitHub Configuration

### Creating a Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (update GitHub Action workflows)
4. Copy and paste into `.env` as `GITHUB_TOKEN`

### Repository Structure

Generated repositories will have:
```
task-name-abc123/
├── index.html          (Main application)
├── README.md           (Documentation)
├── LICENSE             (MIT License)
└── .github/
    └── workflows/
        └── pages.yml   (GitHub Pages deployment)
```

## 📊 Project Structure

```
llm-code-deployment/
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── README.md                    # This file
│
├── app/
│   ├── builder.py              # Task page generator
│   └── templates/
│       ├── index.html          # Web dashboard
│       ├── counter.html        # Generated tasks
│       └── ...
│
├── services/
│   ├── llm_generator.py        # OpenAI integration
│   ├── github_manager.py       # GitHub API wrapper
│   ├── task_manager.py         # Task tracking
│   └── evaluator.py            # Evaluation logic
│
├── database/
│   ├── db.py                   # Database setup
│   └── models.py               # SQLAlchemy models
│
├── api/
│   ├── build.py                # Build endpoints
│   ├── revise.py               # Revise endpoints
│   └── evaluate_webhook.py     # Webhook handler
│
└── scripts/
    ├── round1.py               # Evaluation scripts
    ├── round2.py
    └── evaluate.py
```

## 🧪 Testing

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

### Test Task Submission
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "secret": "st_secret_Xw28g7mc45Qp91Yf",
    "task": "counter",
    "description": "Simple counter app"
  }'
```

### View API Documentation
```
http://localhost:8000/docs    # Swagger UI
http://localhost:8000/redoc   # ReDoc documentation
```

## 🐛 Troubleshooting

### "Invalid secret" Error
- Check that `STUDENT_SECRET` in `.env` matches the one you're using
- Ensure `.env` file is in the project root

### GitHub Token Issues
- Verify token has `repo` and `workflow` scopes
- Check token hasn't expired
- Ensure `GITHUB_USERNAME` matches token owner

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is correct
- Check API key has sufficient credits
- Ensure API key hasn't been revoked

### Port Already in Use
```bash
# Change port in .env
API_PORT=8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### Database Errors
```bash
# Reset database
rm llm_deployment.db
python -c "from database.db import init_db; init_db()"
```

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide interactive API documentation and testing.

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💡 Examples

### Example 1: Create a Counter
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "st_secret_Xw28g7mc45Qp91Yf",
    "task": "counter",
    "description": "A simple counter that can go up and down"
  }'
```

### Example 2: Create a Calculator
```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "st_secret_Xw28g7mc45Qp91Yf",
    "task": "calculator",
    "description": "Scientific calculator with basic operations"
  }'
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check GitHub issues
4. Contact the development team

## 🔄 Workflow

```
1. Student fills form → 2. Submit → 3. OpenAI generates code → 
4. Create GitHub repo → 5. Deploy to Pages → 6. Return URLs → 
7. Student views result → 8. Request revisions (Round 2) → 9. Deploy again
```

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-17
**Status**: ✅ Stable
