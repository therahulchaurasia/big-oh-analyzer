from fastapi import APIRouter, HTTPException
from models import CodeSnippet, AnalysisResponse
from services import analyze_time_complexity

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_code_endpoint(request: CodeSnippet):
    if len(request.code) > 5000:
         raise HTTPException(status_code=400, detail="Code too long.")

    # Call the Service
    time_val, time_reason = analyze_time_complexity(request.code)
    
    return {
        "complexity": time_val,        # Legacy field
        "time_complexity": time_val,
        "time_reason": time_reason,
        "status": "success"
    }