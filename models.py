from pydantic import BaseModel

class CodeSnippet(BaseModel):
    code: str

class AnalysisResponse(BaseModel):
    complexity: str
    time_complexity: str
    time_reason: str
    status: str