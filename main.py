from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import os
import json
import uuid
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Import services
from app.builder import generate_task_page
from services.github_manager import GitHubManager
from services.llm_generator import LLMGenerator
from services.task_manager import TaskManager
from services.evaluation_service import EvaluationService
from services.attachment_handler import AttachmentHandler
from database.db import init_db, SessionLocal
from config import validate_config

load_dotenv()

# Initialize services
github_mgr = GitHubManager()
llm_gen = LLMGenerator()
task_mgr = TaskManager()
eval_svc = EvaluationService()
attachment_handler = AttachmentHandler()

STUDENT_SECRET = os.getenv("STUDENT_SECRET")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")

# ============================================================================
# Pydantic Models
# ============================================================================

class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int = 1
    nonce: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brief: str
    checks: Optional[List[str]] = []
    evaluation_url: str
    attachments: Optional[List[Dict]] = []

class BuildRequest(BaseModel):
    email: Optional[str] = None
    secret: str
    task: str
    description: str
    brief: Optional[str] = None
    checks: Optional[List[str]] = None

class ReviseRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int = 2
    nonce: str
    brief: str
    checks: Optional[List[str]] = []
    evaluation_url: str

class EvaluationResponse(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str

class TaskResponse(BaseModel):
    status: str
    message: str
    task_id: str
    round: int
    repo_url: Optional[str] = None
    pages_url: Optional[str] = None

# ============================================================================
# Lifespan & Middleware
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        validate_config()
        init_db()
        print("✅ Configuration validated")
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise
    yield
    # Shutdown
    print("🛑 Shutting down")

app = FastAPI(
    title="LLM Code Deployment Engine",
    description="Build, deploy, and evaluate LLM-generated applications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (optional)
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "LLM Code Deployment"
    }

@app.get("/")
async def home():
    """Serve home page"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return JSONResponse(
        {"message": "Welcome to LLM Code Deployment API. Visit /docs for API documentation."},
        status_code=200
    )

@app.get("/templates/{task_name}.html")
async def serve_task_page(task_name: str):
    """Serve generated task HTML pages"""
    file_path = f"app/templates/{task_name}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Task page not found")

# ============================================================================
# Build Endpoints (Round 1)
# ============================================================================

@app.post("/api/build", response_model=TaskResponse)
async def build_task(req: TaskRequest, background_tasks: BackgroundTasks):
    """
    Build phase: Generate and deploy an app based on the brief
    
    1. Verify secret
    2. Generate app using LLM
    3. Create GitHub repo
    4. Deploy to GitHub Pages
    5. POST to evaluation_url
    """
    # Verify secret
    if req.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    try:
        # Process attachments
        processed_attachments = attachment_handler.process_attachments(req.attachments)
        
        # Log task request
        db = SessionLocal()
        task_mgr.create_task(
            email=req.email,
            task_name=req.task,
            round=req.round,
            brief=req.brief
        )
        db.close()
        
        # Generate app code using LLM
        app_code = await llm_gen.generate_app(
            brief=req.brief,
            checks=req.checks or [],
            task_id=req.task
        )
        
        # Create GitHub repo and deploy
        repo_info = await github_mgr.create_and_deploy_repo(
            repo_name=req.task,
            code=app_code,
            readme=f"# {req.task}\n\n{req.brief}\n\n## License\n\nMIT"
        )
        
        # Prepare evaluation payload
        eval_payload = eval_svc.create_evaluation_payload(
            email=req.email,
            task=req.task,
            round=req.round,
            nonce=req.nonce,
            repo_url=repo_info["repo_url"],
            commit_sha=repo_info["commit_sha"],
            pages_url=repo_info["pages_url"]
        )
        
        # POST to evaluation URL in background
        background_tasks.add_task(
            eval_svc.post_to_evaluation_url,
            req.evaluation_url,
            eval_payload
        )
        
        return TaskResponse(
            status="success",
            message=f"Task '{req.task}' deployed successfully!",
            task_id=req.task,
            round=req.round,
            repo_url=repo_info["repo_url"],
            pages_url=repo_info["pages_url"]
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Build failed: {str(e)}")

@app.post("/api/submit")
async def submit_task(req: BuildRequest):
    """Legacy endpoint for task submission"""
    if req.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    try:
        page_path = generate_task_page(req.task, req.description)
        return {
            "status": "success",
            "message": f"Task '{req.task}' page generated!",
            "url": page_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Revise Endpoints (Round 2)
# ============================================================================

@app.post("/api/revise", response_model=TaskResponse)
async def revise_task(req: TaskRequest, background_tasks: BackgroundTasks):
    """
    Revise phase (Round 2): Update an existing app based on new requirements
    
    1. Verify secret
    2. Fetch existing code from GitHub
    3. Use LLM to revise code based on new brief
    4. Push updates to GitHub
    5. POST to evaluation_url
    """
    # Verify secret
    if req.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    if req.round != 2:
        raise HTTPException(status_code=400, detail="Revise endpoint is for round 2")
    
    try:
        # Get existing repo
        user = github_mgr.github.get_user()
        repo = user.get_repo(req.task)
        
        # Fetch existing index.html
        try:
            existing_file = repo.get_contents("index.html")
            existing_code = existing_file.decoded_content.decode('utf-8')
        except:
            raise HTTPException(status_code=404, detail=f"Repository {req.task} not found or no index.html")
        
        # Use LLM to revise code
        revised_code = llm_gen.revise_html(
            original_html=existing_code,
            feedback=req.brief,
            checks=req.checks
        )
        
        # Update the file in GitHub
        github_mgr.upload_file(
            repo_name=req.task,
            file_path="index.html",
            content=revised_code,
            commit_message=f"Round 2: {req.brief[:50]}"
        )
        
        # Update README
        readme = f"# {req.task}\n\n## Round 2 Updates\n\n{req.brief}\n\n## License\n\nMIT"
        github_mgr.upload_file(
            repo_name=req.task,
            file_path="README.md",
            content=readme,
            commit_message="Update README for Round 2"
        )
        
        # Wait for Pages to update
        github_mgr.wait_for_pages_deployment(req.task, timeout=60)
        
        # Get updated commit SHA
        commit_sha = github_mgr.get_latest_commit_sha(req.task)
        pages_url = f"https://{github_mgr.username}.github.io/{req.task}/"
        repo_url = f"https://github.com/{github_mgr.username}/{req.task}"
        
        # Prepare evaluation payload
        eval_payload = eval_svc.create_evaluation_payload(
            email=req.email,
            task=req.task,
            round=req.round,
            nonce=req.nonce,
            repo_url=repo_url,
            commit_sha=commit_sha,
            pages_url=pages_url
        )
        
        # POST to evaluation URL in background
        background_tasks.add_task(
            eval_svc.post_to_evaluation_url,
            req.evaluation_url,
            eval_payload
        )
        
        return TaskResponse(
            status="success",
            message=f"Task '{req.task}' revised successfully!",
            task_id=req.task,
            round=2,
            repo_url=repo_url,
            pages_url=pages_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Revision failed: {str(e)}")

# ============================================================================
# Evaluation Webhook Endpoints
# ============================================================================

@app.post("/api/evaluate/webhook")
async def evaluation_webhook(req: EvaluationResponse):
    """
    Receive evaluation results from instructor's evaluation system
    
    Stores results and triggers next round if applicable
    """
    try:
        db = SessionLocal()
        
        # Verify task exists
        task = task_mgr.get_task(db, req.task, req.round)
        if not task:
            db.close()
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Store evaluation results
        task_mgr.log_evaluation_result(db, {
            "email": req.email,
            "task": req.task,
            "round": req.round,
            "nonce": req.nonce,
            "repo_url": req.repo_url,
            "commit_sha": req.commit_sha,
            "pages_url": req.pages_url,
            "timestamp": datetime.utcnow()
        })
        
        db.close()
        
        return {
            "status": "received",
            "message": "Evaluation results logged successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

# ============================================================================
# Evaluation Endpoints
# ============================================================================

@app.get("/api/results/{task_id}")
async def get_results(task_id: str, round: int = 1):
    """Get evaluation results for a specific task"""
    try:
        db = SessionLocal()
        results = task_mgr.get_results(db, task_id, round)
        db.close()
        
        if not results:
            raise HTTPException(status_code=404, detail="No results found")
        
        return {
            "task_id": task_id,
            "round": round,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{email}")
async def get_tasks(email: str):
    """Get all tasks for a student"""
    try:
        db = SessionLocal()
        tasks = task_mgr.get_student_tasks(db, email)
        db.close()
        
        return {
            "email": email,
            "tasks": tasks,
            "count": len(tasks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Background Tasks
# ============================================================================

async def evaluate_deployment(email: str, task_id: str, repo_url: str, pages_url: str):
    """Background task to evaluate deployment after GitHub Pages becomes available"""
    try:
        print(f"📊 Evaluating deployment for {task_id}...")
        # This would be expanded to run actual evaluations
        print(f"✅ Deployment evaluation complete: {pages_url}")
    except Exception as e:
        print(f"❌ Evaluation error: {str(e)}")

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status": "error"},
    )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT
    
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
