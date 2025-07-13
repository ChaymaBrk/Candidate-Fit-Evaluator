from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
from src.services.candidate_evaluator import CandidateEvaluator
from src.models.response_models import FitEvaluationResponse
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Candidate Fit Evaluator",
    description="An AI assistant that evaluates how well a candidate's resume matches a job description",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Candidate Fit Evaluator API", "status": "running"}

@app.post("/evaluate-fit", response_model=FitEvaluationResponse)
async def evaluate_candidate_fit(
    resume_file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description_file: UploadFile = File(..., description="Job description file (PDF, DOCX, or TXT)"),
    candidate_name: Optional[str] = Form(None, description="Candidate name (optional)")
):
    """
    Evaluate how well a candidate's resume matches a job description.
    
    Args:
        resume_file: The candidate's resume (PDF or DOCX)
        job_description_file: The job description (PDF, DOCX, or TXT)
        candidate_name: Optional candidate name for reference
    
    Returns:
        FitEvaluationResponse: Structured evaluation results
    """
    try:
        logger.info(f"Starting evaluation for candidate: {candidate_name or 'Unknown'}")
        
        # Validate file types
        if not resume_file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Resume must be PDF or DOCX")
        
        if not job_description_file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(status_code=400, detail="Job description must be PDF, DOCX, or TXT")
        
        # Initialize evaluator
        evaluator = CandidateEvaluator()
        
        # Perform evaluation
        result = await evaluator.evaluate_fit(
            resume_file=resume_file,
            job_description_file=job_description_file,
            candidate_name=candidate_name
        )
        
        logger.info(f"Evaluation completed for candidate: {candidate_name or 'Unknown'}")
        return result
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Candidate Fit Evaluator"}

@app.get("/ui")
async def get_ui():
    return FileResponse("index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 