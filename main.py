import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeSnippet(BaseModel):
    code: str

def analyze_js_complexity(code: str):
    """
    Analyzes JS/TS code by tracking nested loops using a Stack.
    """
    # 1. Simple cleaning: Remove newlines to treat it as one long stream
    # This handles one-liners like: for(...) { for(...) {} }
    stream = code.replace('\n', ' ')
    
    # 2. Extract key tokens (for, while, {, }) using Regex
    # We look for whole words 'for', 'while' OR the characters '{', '}'
    tokens = re.findall(r'\bfor\b|\bwhile\b|\{|\}', stream)
    print(tokens)
    max_complexity = 0
    current_complexity = 0
    stack = [] 
    
    # 'recent_keyword' tracks if the last word we saw was 'for' or 'while'
    # This helps us decide if the next '{' belongs to a loop.
    is_loop_pending = False
    
    for token in tokens:
        if token == 'for' or token == 'while':
            is_loop_pending = True
            
        elif token == '{':
            # We are entering a block. 
            if is_loop_pending:
                # It IS a loop block. 
                # Push 1 to stack (this layer adds to O(N))
                stack.append(1)
                current_complexity += 1
                is_loop_pending = False # Reset flag
            else:
                # It is just an IF or FUNCTION block.
                # Push 0 (this layer adds nothing)
                stack.append(0)
            
            # Update our record if this is the deepest we've gone
            if current_complexity > max_complexity:
                max_complexity = current_complexity
                
        elif token == '}':
            # We are leaving a block. Pop the last value.
            if stack:
                val = stack.pop()
                current_complexity -= val  # If it was a loop (1), decrease depth.
                
    # 3. Formulate Result
    if max_complexity == 0:
        return "O(1)"
    elif max_complexity == 1:
        return "O(N)"
    else:
        return f"O(N^{max_complexity})"
    

@app.post("/api/analyze")
def analyze_code_endpoint(request: CodeSnippet):
    if len(request.code) > 5000:
         raise HTTPException(status_code=400, detail="Code too long.")

    # Call the new JS analyzer
    complexity = analyze_js_complexity(request.code)
    
    return {
        "complexity": complexity,
        "status": "success"
    }

@app.get("/")
def health_check():
    return {"status": "Backend is running"}