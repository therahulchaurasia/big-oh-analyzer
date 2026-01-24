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
        
        # --- CONFIGURATION ---
        self.iterators = [
            b".map", b".filter", b".forEach", b".reduce", 
            b".includes", b".indexOf", b".find", b".some", b".every"
        ]
        self.mutators = [
            b".slice", b".splice", b".concat", b".shift", 
            b".unshift", b".split", b".join", b".flat", b".reverse"
        ]
        self.statics = [
            b"Array.from", b"Object.keys", b"Object.values", b"Object.entries"
        ]
        self.constructors = [
            b"Set", b"Map", b"List", b"Dict"
        ]
        # NEW: Heap/Tree operations that imply O(log N)
        self.log_ops = [
            b".sort", b"MinPriorityQueue", b"MaxPriorityQueue", 
            b".enqueue", b".dequeue", b"heapq", b"PriorityQueue"
        ]
        
        self.linear_ops = self.iterators + self.mutators

    def analyze(self, code: str, language: str = 'javascript'):
        parser = Parser()
        if language == 'python':
            parser.language = self.py_lang
        else:
            parser.language = self.js_lang
            
        tree = parser.parse(bytes(code, "utf8"))
        
        self.code_bytes = bytes(code, "utf8")
        self.max_depth = 0
        self.found_log_op = False # Track if we found sorting/heap ops
        
        self._traverse(tree.root_node, current_depth=0, is_chain=False)
        
        # --- RESULT REASONING ---
        
        # Case 1: Log Linear (Sorting or Heap in a loop)
        # If we have depth 1 (Loop) AND a Log Op (Heap/Sort), it's N log N
        if self.max_depth == 1 and self.found_log_op:
             return "O(N log N)", "Heap operations or Sorting detected in linear flow"

        # Case 2: Standard Depths
        if self.max_depth == 0:
            return "O(1)", "Constant time operations"
        elif self.max_depth == 1:
            return "O(N)", "Single loop or linear operation detected"
        else:
            return f"O(N^{self.max_depth})", f"Nested loops/operations detected (Depth {self.max_depth})"

    def _traverse(self, node, current_depth, is_chain=False):
        node_type = node.type
        cost = 0
        is_linear = False
        
        # --- 1. IDENTIFY NODE COST ---
        
        # Loops
        if node_type in ["for_statement", "while_statement", "do_statement", "for_of_statement", "for_in_statement"]:
            if self._is_constant_loop(node):
                cost = 0
            else:
                cost = 1
                
        # Methods
        elif node_type == "call_expression":
            if self._is_log_op(node):
                self.found_log_op = True
                # Log ops don't add "Integer Depth" (N^2), they add a "Log Factor"
                # We track them separately.
            elif self._is_linear_method(node) or self._is_static_linear(node):
                is_linear = True
                if is_chain: cost = 0
                else: cost = 1

        # New Expressions (Constructors)
        elif node_type == "new_expression":
            if self._is_log_op(node): # new MinPriorityQueue
                self.found_log_op = True
            elif self._is_linear_constructor(node):
                cost = 1

        # --- 2. UPDATE DEPTH ---
        next_depth = current_depth + cost
        self.max_depth = max(self.max_depth, next_depth)
        
        # --- 3. RECURSE (THE SMART PART) ---
        
        # SPECIAL HANDLING: LOOPS
        # We must split the "Header" (Outer Scope) from the "Body" (Inner Scope)
        if node_type in ["for_statement", "for_of_statement", "for_in_statement", "while_statement"]:
            body_node = node.child_by_field_name("body")
            
            # 1. Traverse everything EXCEPT body at CURRENT_DEPTH
            # This ensures Object.entries() in the header is NOT multiplied by the loop
            for child in node.children:
                if child != body_node:
                    self._traverse(child, current_depth, is_chain=False)
            
            # 2. Traverse Body at NEXT_DEPTH
            if body_node:
                self._traverse(body_node, next_depth, is_chain=False)
                
            return # Done with this node
            
        # SPECIAL HANDLING: CALLS (Chaining)
        if node_type == "call_expression":
            function_node = node.child_by_field_name("function")
            arguments_node = node.child_by_field_name("arguments")
            
            if function_node:
                self._traverse(function_node, next_depth, is_chain=(is_linear or is_chain))
            
            if arguments_node:
                self._traverse(arguments_node, next_depth, is_chain=False)
                
            for child in node.children:
                if child != function_node and child != arguments_node:
                    self._traverse(child, next_depth, is_chain=False)
            return

        # SPECIAL HANDLING: MEMBERS (Chaining)
        if node_type == "member_expression":
            object_node = node.child_by_field_name("object")
            property_node = node.child_by_field_name("property")
            if object_node: self._traverse(object_node, next_depth, is_chain=is_chain)
            if property_node: self._traverse(property_node, next_depth, is_chain=False)
            return

        # Default Recursion
        for child in node.children:
            self._traverse(child, next_depth, is_chain=False)

    # --- HELPER FUNCTIONS ---

    def _is_constant_loop(self, node):
        condition_node = node.child_by_field_name("condition")
        collection_node = node.child_by_field_name("right") 
        target_text = ""
        if condition_node:
            target_text = self.code_bytes[condition_node.start_byte:condition_node.end_byte].decode('utf8', errors='ignore')
        else:
            header_end = min(node.end_byte, node.start_byte + 150) 
            target_text = self.code_bytes[node.start_byte:header_end].decode('utf8', errors='ignore')
        is_numeric_comparison = re.search(r'([<>]=?|[!=]=)\s*\d+', target_text)
        is_python_range = re.search(r'range\s*\(\s*\d+\s*\)', target_text)
        return bool(is_numeric_comparison or is_python_range)

    def _get_node_text(self, node):
        end = min(node.end_byte, node.start_byte + 50)
        return self.code_bytes[node.start_byte:end]

    def _is_log_op(self, node):
        text = self._get_node_text(node)
        for op in self.log_ops:
            if op in text: return True
        return False

    def _is_linear_method(self, node):
        text = self._get_node_text(node)
        for op in self.linear_ops:
            if op in text: return True
        return False

    def _is_static_linear(self, node):
        text = self._get_node_text(node)
        for op in self.statics:
            if op in text: return True
        return False

    def _is_linear_constructor(self, node):
        constructor_name = ""
        constructor_node = node.child_by_field_name("constructor")
        if constructor_node:
            constructor_name = self.code_bytes[constructor_node.start_byte:constructor_node.end_byte].decode('utf8')
        
        if constructor_name not in ["Set", "Map", "Array", "List", "Dict"]:
            return False

        arguments_node = node.child_by_field_name("arguments")
        if not arguments_node:
            return False
        args = [c for c in arguments_node.children if c.type not in ["(", ")", ",", "comment"]]
        
        if not args:
            return False # new Set() -> O(1)

        first_arg = args[0]
        if first_arg.type in ["array", "object", "array_literal", "object_literal"]:
            content = [c for c in first_arg.children if c.type not in ["[", "]", "{", "}", ","]]
            if not content:
                return False 
        return True

analyzer = ComplexityAnalyzer()