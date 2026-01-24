import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

class BoundaryResolver:
    def __init__(self):
        self.js_lang = Language(tsjs.language())
        self.parser = Parser(self.js_lang)
        self.comparison_ops = {"<", ">", "<=", ">=", "==", "===", "!=", "!=="}
        self.literal_types = {
            "number", "string", "boolean", "true", "false", 
            "null", "undefined", "regex"
        }
        self.pure_globals = {"Math", "Number", "Object", "Array"}

    def get_truthiness(self, node):
        """Returns True (always truthy), False (always falsy), or None (unknown)."""
        if not node: return None
        
        # Unwrap parentheses for truthiness check
        if node.type == "parenthesized_expression":
            return self.get_truthiness(node.named_child(0))

        if node.type in ["true", "regex", "array", "object"]:
            return True
        if node.type in ["false", "null", "undefined"]:
            return False
        
        if node.type == "number":
            return node.text.decode('utf8') not in ["0", "0n"]
        
        if node.type == "string":
            return node.text.decode('utf8') not in ["''", '""']

        if node.type == "unary_expression":
            op = node.child_by_field_name("operator")
            arg = node.child_by_field_name("argument")
            if op and op.text.decode('utf8') == "!" and arg:
                val = self.get_truthiness(arg)
                return not val if val is not None else None
        
        return None

    def is_bounded_condition(self, node):
        if not node: return False

        # 1. Structural Unwrapping
        if node.type == "parenthesized_expression":
            return self.is_bounded_condition(node.named_child(0))
        
        if node.type == "unary_expression":
            return self.is_bounded_condition(node.child_by_field_name("argument"))

        # 2. Base Cases
        if node.type in self.literal_types:
            return True
            
        # Whitelist globals (Math.PI)
        if node.type == "member_expression":
            obj = node.child_by_field_name("object")
            if not obj or obj.text.decode('utf8') not in self.pure_globals:
                return False
            
            prop = node.child_by_field_name("property")
            if prop:
                prop_text = prop.text.decode('utf8')
                known_constants = {
                    "Math": {"PI", "E", "LN10", "LN2", "LOG10E", "LOG2E", "SQRT1_2", "SQRT2"},
                    "Number": {"MAX_SAFE_INTEGER", "MIN_SAFE_INTEGER", "MAX_VALUE", "MIN_VALUE"},
                }
                obj_name = obj.text.decode('utf8')
                if obj_name in known_constants and prop_text in known_constants[obj_name]:
                    return True
            
            return False

        # 3. Recursive Binary Logic
        if node.type == "binary_expression":
            named = [c for c in node.children if c.is_named]
            op_node = next((c for c in node.children if not c.is_named), None)
            op = op_node.type if op_node else ""
            
            if len(named) >= 2:
                left, right = named[0], named[1]
                
                # Logical Short-Circuiting
                if op in ["&&", "||"]:
                    l_truth = self.get_truthiness(left)
                    r_truth = self.get_truthiness(right)

                    if op == "&&":
                        # If either is false, loop is O(1) [0 iterations]
                        if l_truth is False or r_truth is False: return True
                        # If left is true, complexity depends on right
                        if l_truth is True: return self.is_bounded_condition(right)
                        return self.is_bounded_condition(left) and self.is_bounded_condition(right)

                    if op == "||":
                        # If either is true, loop is O(inf) [Non-constant]
                        if l_truth is True or r_truth is True: return False
                        return self.is_bounded_condition(left) and self.is_bounded_condition(right)

                # Call Guard: Soundness first
                if left.type == "call_expression" or right.type == "call_expression":
                    return False

                # Math and Comparison
                if op in ["+", "-", "*", "/"]:
                    return self.is_bounded_condition(left) and self.is_bounded_condition(right)
                if op in self.comparison_ops:
                    return self.is_bounded_condition(left) or self.	condition(right)

         # 4. Ternary (IMPROVED: short-circuit on condition)
        if node.type == "conditional_expression":
            condition = node.child_by_field_name("condition")
            consequence = node.child_by_field_name("consequence")
            alternative = node.child_by_field_name("alternative")
            
            cond_truth = self.get_truthiness(condition)
            if cond_truth is True:
                return self.is_bounded_condition(consequence)
            if cond_truth is False:
                return self.is_bounded_condition(alternative)
            
            return self.is_bounded_condition(consequence) and self.is_bounded_condition(alternative)
        
				# Assignment expressions: check RHS
        if node.type == "assignment_expression":
            value = node.child_by_field_name("right")
            return self.is_bounded_condition(value) if value else False
        
				        # Guard: optional chaining and nullish coalescing are non-constant
        if node.type in ["optional_chain", "nullish_coalescing_expression"]:
            return False

        return False

# --- TEST DRIVE ---
# Initialize the resolver correctly
boundary_resolver = BoundaryResolver()

test_cases = [
    "i < 10",                      # True
    "i === 5",                     # True
    "i !== 0",                     # True
    "i < n",                       # False
    "i < 10 && i < n",             # False
    "i < 10 || i < n",             # False
    "i === 'stop'",                # True
    "i < n && j < m",              # False
    "(i < 10 && i < n) || j < k",  # False
    "i < 10 && (j < 5 || k < 3)",  # False
    "i < 10 + 2",                  # True
    "i < n + 1",                   # False
    "i < -5",                      # True
    "!flag",                       # False
    "!!true",                      # True
    "true",                        # True
    "false",                       # True
    "0",                           # True
    "'x'",                         # True
    "i",                           # False
    "arr.length < 10",             # True
    "i < getN()",                  # False
    "getN() < 10",                 # False
    "value === null",              # True
    "value === undefined",         # True
    "5 < 10",                      # True
    "true || false",               # False  # always-true ⇒ non-constant
    "true && false",               # True   # always-false ⇒ bounded
    "((i < 10)) && (i < n)",       # False

    # Additional edges:
    "Math.PI < 4",                 # True   # pure_global whitelist
    "Math[foo] < 10",              # False  # non-constant property access
    "0 && 1",                      # True   # always false ⇒ bounded
    "0 || 1",                      # False  # always true ⇒ unbounded
    "'' || 'a'",                   # False  # always true ⇒ unbounded
    "'' && 'a'",                   # True   # always false ⇒ bounded
    "((true))",                    # True   # parenthesis unwrap
    "(flag ? 1 : 2) < 10",         # True   # both branches literal
    "(flag ? getN() : 2) < 10",    # False  # call in a branch
    "(true ? 1 : getN()) < 10",    # True   # condition always true ⇒ consequence checked
    "(false ? getN() : 2) < 10",   # True   # condition always false ⇒ alternative checked
]

print(f"{'Code':<30} | {'Constant'}")
print("-" * 45)

for src in test_cases:
    tree = boundary_resolver.parser.parse(bytes(f"while({src});", "utf8"))
    # JS tree-sitter: while_statement -> condition is a named field
    while_node = tree.root_node.children[0]
    cond = while_node.child_by_field_name("condition")
    
    # Structural fallback for unwrapping
    if cond and cond.type == "parenthesized_expression":
        cond = cond.named_child(0)

    result = boundary_resolver.is_bounded_condition(cond)
    print(f"{src:<25} | {result}")