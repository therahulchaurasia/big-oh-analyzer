import re
from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspy

class ComplexityAnalyzer:
    def __init__(self):
        try:
            self.js_lang = Language(tsjs.language())
            self.py_lang = Language(tspy.language())
        except Exception as e:
            print(f"Error loading languages: {e}")
            raise e

    def analyze(self, code: str, language: str = 'javascript'):
        parser = Parser()
        if language == 'python':
            parser.language = self.py_lang
        else:
            parser.language = self.js_lang
            
        tree = parser.parse(bytes(code, "utf8"))
        cursor = tree.walk()
        code_bytes = bytes(code, "utf8")
        
        max_depth = 0
        depth_stack = [] 
        visited_children = False
        
        # --- FEATURE PARITY LISTS ---
        
        # 1. Iterators (O(N))
        iterators = [
            b".map", b".filter", b".forEach", b".reduce", 
            b".includes", b".indexOf", b".find", b".some", b".every"
        ]
        
        # 2. Mutators (O(N) - especially shift/unshift/splice)
        mutators = [
            b".slice", b".splice", b".concat", b".shift", 
            b".unshift", b".split", b".join", b".flat", b".reverse"
        ]
        
        # 3. Static Methods (O(N))
        statics = [
            b"Array.from", b"Object.keys", b"Object.values", b"Object.entries"
        ]
        
        # 4. Constructors (O(N) if they take arguments)
        constructors = [
            b"Set", b"Map", b"List", b"Dict" 
            # Note: In AST, we look for 'new Set', so we just track the class name
        ]

        # Combine linear operations for easier checking
        linear_ops = iterators + mutators
        
        # Track if we found a sort operation (dominates O(N))
        has_sort = False
        
        try:
            while True:
                node = cursor.node
                if node is None: break
                
                node_type = node.type
                
                if not visited_children:
                    # --- A. LOOP DETECTION ---
                    is_loop = node_type in ["for_statement", "while_statement", "do_statement"]
                    is_constant_loop = False
                    
                    if is_loop:
                        # Grab header text to check for constant bounds (e.g. i < 9)
                        header_end = min(node.end_byte, node.start_byte + 150) 
                        header_text = code_bytes[node.start_byte:header_end].decode('utf8', errors='ignore')
                        if re.search(r'[<>=!]\s*\d+\s*[;)]', header_text) or re.search(r'range\s*\(\s*\d+\s*\)', header_text):
                            is_constant_loop = True

                    # --- B. METHOD CALLS (.map, .sort, Object.keys) ---
                    is_linear_method = False
                    
                    if node_type == "call_expression":
                        # Get the text of the entire call, e.g., "arr.map(x => x)"
                        # Limiting length to avoid huge strings, but enough to catch method name
                        snippet_end = min(node.end_byte, node.start_byte + 50)
                        node_text = code_bytes[node.start_byte:snippet_end]
                        
                        # Check 1: .sort()
                        if b".sort" in node_text:
                            has_sort = True
                        
                        # Check 2: Linear Methods (.map, .shift, etc.)
                        for op in linear_ops:
                            if op in node_text:
                                is_linear_method = True
                                break
                                
                        # Check 3: Static Methods (Object.keys)
                        if not is_linear_method:
                            for static_method in statics:
                                if static_method in node_text:
                                    is_linear_method = True
                                    break
                                    
                    # --- C. CONSTRUCTORS (new Set(...)) ---
                    # In JS AST, this is 'new_expression'
                    elif node_type == "new_expression":
                        # We need to check if it has arguments. 
                        # "new Set()" is O(1), "new Set(arr)" is O(N).
                        # We look at the node text for the class name AND parens with content
                        node_text = code_bytes[node.start_byte:node.end_byte]
                        
                        # Check if it's one of our target constructors
                        is_target_constructor = False
                        for constr in constructors:
                            # regex to ensure word boundary, e.g. "new Set"
                            if re.search(rb'\bnew\s+' + constr, node_text):
                                is_target_constructor = True
                                break
                        
                        # Check if it has arguments (simple heuristic: look for non-whitespace inside parens)
                        if is_target_constructor:
                            # Look for contents between ( and )
                            match = re.search(rb'\(\s*[^)\s]+\s*\)', node_text)
                            if match:
                                is_linear_method = True

                    # --- D. BLOCK CONTAINERS ---
                    is_block = node_type in [
                        "function_definition", "arrow_function", "method_definition",
                        "if_statement", "else_clause", "try_statement", "catch_clause",
                        "class_definition"
                    ]

                    # --- DEPTH CALCULATION ---
                    if is_loop:
                        if is_constant_loop:
                            depth_stack.append(0)
                        else:
                            depth_stack.append(1)
                    
                    elif is_linear_method:
                        depth_stack.append(1)
                        
                    elif is_block:
                        depth_stack.append(0)

                    # Update Max Depth
                    current_depth = sum(depth_stack)
                    max_depth = max(max_depth, current_depth)

                # --- NAVIGATION ---
                if not visited_children and cursor.goto_first_child():
                    visited_children = False
                elif cursor.goto_next_sibling():
                    visited_children = False
                    # POP Logic
                    if node_type in ["for_statement", "while_statement", "do_statement", "call_expression", "new_expression"] or \
                       node_type in ["function_definition", "arrow_function", "if_statement", "class_definition"]:
                         if depth_stack: depth_stack.pop()
                
                elif cursor.goto_parent():
                    visited_children = True
                    # POP Logic
                    parent_type = cursor.node.type
                    if parent_type in ["for_statement", "while_statement", "do_statement", "call_expression", "new_expression"] or \
                       parent_type in ["function_definition", "arrow_function", "if_statement", "class_definition"]:
                         if depth_stack: depth_stack.pop()
                else:
                    break
                    
        except Exception as e:
            print(f"Traversal Error: {e}")
            return "O(1)", "Error analyzing complexity"

        # --- FINAL RESULT LOGIC ---
        
        # 1. Sort Dominance
        # If we have a sort, and the max nesting is just that sort (depth 1) or simple loops,
        # Sort (N log N) dominates O(N).
        # Note: If sort is INSIDE a loop (depth 2), it becomes N^2 log N, which our simple N^depth logic approximates to N^2.
        if has_sort and max_depth <= 1:
            return "O(N log N)", "Sorting (.sort) dominates linear operations"

        # 2. Standard Depth
        if max_depth == 0:
            return "O(1)", "Constant time operations"
        elif max_depth == 1:
            return "O(N)", "Single loop or linear operation detected"
        else:
            return f"O(N^{max_depth})", f"Nested loops/operations detected (Depth {max_depth})"

analyzer = ComplexityAnalyzer()