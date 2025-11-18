from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime
from submitter import submit_application
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for running sync code
executor = ThreadPoolExecutor(max_workers=2)

app = FastAPI(
    title="AI Resume Auto-Submission (Simplified)",
    description="Automate job application form filling and submission",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/submit")
async def submit(
    job_url: str = Form(...),
    name: str = Form(default=""),
    email: str = Form(default=""),
    phone: str = Form(default=""),
    linkedin: str = Form(default=""),
    website: str = Form(default=""),
    resume: UploadFile = File(...),
):
    """
    Submit a job application with resume to real ATS platforms.
    
    Args:
        job_url: URL of the job posting (Greenhouse, Lever, Ashby, etc.)
        name: Applicant name (optional)
        email: Applicant email (optional)
        phone: Applicant phone (optional)
        linkedin: LinkedIn profile URL (optional)
        website: Personal website/portfolio URL (optional)
        resume: Resume PDF file
    
    Returns:
        JSON response with submission status and details
    """
    tmpdir = None
    resume_path = None
    
    try:
        # Validate inputs
        if not job_url or not job_url.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "job_url is required"}
            )
        
        if not resume.filename.lower().endswith(".pdf"):
            return JSONResponse(
                status_code=400,
                content={"error": "Resume must be a PDF file"}
            )
        
        # Save resume to temporary file
        tmpdir = tempfile.mkdtemp(prefix="ai_submit_")
        resume_path = os.path.join(tmpdir, resume.filename)
        
        with open(resume_path, "wb") as out:
            shutil.copyfileobj(resume.file, out)
        
        logger.info(f"Processing submission for {job_url}")
        logger.info(f"Resume saved to {resume_path}")
        
        # Prepare fields
        fields = {
            "name": (name or "").strip(),
            "email": (email or "").strip(),
            "phone": (phone or "").strip(),
            "linkedin": (linkedin or "").strip(),
            "website": (website or "").strip()
        }
        
        # Run submission in thread pool (Playwright sync API needs to be in a thread)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            lambda: submit_application(
                job_url=job_url,
                resume_path=resume_path,
                fields=fields,
                headless=True
            )
        )
        
        logger.info(f"Submission result: {result['status']}")
        
        return JSONResponse(status_code=200, content=result)
        
    except Exception as e:
        logger.error(f"Error in submission: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "job_url": job_url,
                "status": "error",
                "submitted_at": None,
                "notes": [f"Server error: {str(e)[:100]}"]
            }
        )
    
    finally:
        # Cleanup temporary files
        if resume_path and os.path.exists(resume_path):
            try:
                os.unlink(resume_path)
                logger.info(f"Cleaned up {resume_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {resume_path}: {e}")
        
        if tmpdir and os.path.exists(tmpdir):
            try:
                os.rmdir(tmpdir)
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

