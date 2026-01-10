import pytest
from main import analyze_js_complexity

# We use @pytest.mark.parametrize to run the same test logic on many different inputs
@pytest.mark.parametrize("code_snippet, expected_complexity", [
    
    # --- LEVEL 1: Basic Structure ---
    
    # Simple O(1)
    ("let a = 1; let b = 2; return a + b;", "O(1)"),
    
    # Simple Loop O(N)
    ("for (let i = 0; i < n; i++) { console.log(i); }", "O(N)"),
    
    # Nested Loop O(N^2)
    ("""
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            console.log(i, j);
        }
    }
    """, "O(N^2)"),
    
    # Triple Nested Loop O(N^3)
    ("""
    for (let i=0; i<n; i++) {
        for (let j=0; j<n; j++) {
            for (let k=0; k<n; k++) {
                x++;
            }
        }
    }
    """, "O(N^3)"),

    # --- LEVEL 2: Built-in Functions ---
    
    # Sorting is O(N log N)
    ("nums.sort((a,b) => a - b);", "O(N log N)"),
    
    # .map is O(N)
    ("nums.map(n => n * 2);", "O(N)"),
    
    # .includes is O(N)
    ("if (nums.includes(5)) { return true; }", "O(N)"),
    
    # --- LEVEL 3: The "Hidden Loop" Constructors (Your previous bugs) ---
    
    # Set with arguments -> O(N)
    ("let s = new Set(nums);", "O(N)"),
    
    # Array from another array -> O(N)
    ("let copy = Array.from(list);", "O(N)"), # Note: You might need to add 'Array.from' to your regex if you haven't!
    
    # Python style set -> O(N)
    ("let s = set(nums)", "O(N)"),

    # --- LEVEL 4: The "False Positives" (Stress Testing Precision) ---
    
    # Empty Set -> O(1) (Should NOT be O(N))
    ("let s = new Set();", "O(1)"),
    
    # Map.set() method -> O(1) (Should NOT count as a loop)
    # This was the bug: "prevMap.set(diff, i)"
    ("""
    const prevMap = new Map();
    for (let i = 0; i < n; i++) {
        prevMap.set(key, value); 
    }
    """, "O(N)"), # O(N) total, NOT O(N^2)
    
    # Dictionary/Map set inside a nested loop
    ("""
    for(let i=0; i<n; i++) {
        // This .set should NOT add depth
        myMap.set(i, i);
    }
    """, "O(N)"),

    # --- LEVEL 5: Mixed Complexity ---
    
    # Sort dominating a loop
    # O(N log N) is strictly 'worse' than O(N), but your code currently returns O(N log N) 
    # only if max_depth <= 1. Let's verify that behavior.
    ("""
    nums.sort();
    for(let i=0; i<n; i++) {}
    """, "O(N log N)"),
    
    # Loop dominating Sort?
    # If I have a loop O(N) and a sort O(N log N), strictly it is O(N log N).
    # But if I have a Nested Loop O(N^2) and a sort, O(N^2) dominates.
    ("""
    nums.sort();
    for(let i=0; i<n; i++) {
        for(let j=0; j<n; j++) {}
    }
    """, "O(N^2)"),
    
		("""
    for(let i=0; i<n; i++) {
        arr.shift();
    }
    """, "O(N^2)"),
    
])
def test_time_complexity_analysis(code_snippet, expected_complexity):
    result = analyze_js_complexity(code_snippet)
    assert result == expected_complexity