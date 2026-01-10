import re

def analyze_time_complexity(code: str):
    stream = code.replace('\n', ' ')
    
    # --- 1. Heavy Hitters ---
    has_sort = bool(re.search(r'\.sort\(', stream))
    
    # --- 2. O(N) Patterns ---
    
    # A. Iterators
    iterators = r'\.(map|filter|forEach|reduce|includes|indexOf|find|some|every)\('

    # B. Mutators/Copies (shift, splice, split, etc.)
    mutators = r'\.(slice|splice|concat|shift|unshift|split|join|flat|reverse)\('
    
    # C. Static Methods (Array.from, Object.keys)
    statics = r'\b(Array\.from|Object\.keys|Object\.values|Object\.entries)\('
    
    # D. Constructors (new Set, new Map) - checking for arguments
    constructors = r'(?<!\.)\b(set|new Set|list|dict|new Map)\s*\(\s*[^)\s]'
    
    linear_pattern = f'{iterators}|{mutators}|{statics}|{constructors}'
    
    # --- 3. Tokenization ---
    tokens = re.finditer(r'(\bfor\b|\bwhile\b)|(\{)|(\})|(' + linear_pattern + ')', stream)
    
    max_depth = 0
    current_depth = 0
    stack = [] 
    is_loop_pending = False
    
    # We track the "Cause" of the max depth
    primary_cause = "Constant time operations"
    
    for match in tokens:
        token_str = match.group(0)
        
        # --- Case A: Loop Keyword ---
        if match.group(1): 
            is_loop_pending = True
            
        # --- Case B: Hidden O(N) Operation ---
        elif match.group(4):
            cost = 1
            temp_depth = current_depth + cost
            if temp_depth > max_depth:
                max_depth = temp_depth
                # Capture the specific method name for the "Why"
                clean_name = token_str.split('(')[0].strip()
                if current_depth > 0:
                     primary_cause = f"Linear operation '{clean_name}' inside a loop"
                else:
                     primary_cause = f"Linear operation '{clean_name}'"
        
        # --- Case C: Opening Bracket '{' ---
        elif match.group(2):
            if is_loop_pending:
                stack.append(1)
                current_depth += 1
                is_loop_pending = False
                
                # Update Reason
                if current_depth > max_depth:
                    max_depth = current_depth
                    if max_depth == 1:
                        primary_cause = "Single Loop detected"
                    elif max_depth == 2:
                        primary_cause = "Nested Loop detected"
                    else:
                        primary_cause = f"Deeply Nested Loops (Depth {max_depth})"
            else:
                stack.append(0) # It's an IF/ELSE, no depth increase
            
            if current_depth > max_depth:
                max_depth = current_depth
                
        # --- Case D: Closing Bracket '}' ---
        elif match.group(3):
            if stack:
                val = stack.pop()
                current_depth -= val

    # --- Final Logic ---
    
    # 1. Sort dominates linear loops
    if has_sort and max_depth <= 1:
        return "O(N log N)", "Sorting (.sort) dominates linear operations"
        
    # 2. Loop Logic
    if max_depth == 0:
        return "O(1)", "No loops or linear methods found"
    elif max_depth == 1:
        return "O(N)", primary_cause
    else:
        return f"O(N^{max_depth})", primary_cause