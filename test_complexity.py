import pytest
from services import analyze_time_complexity

@pytest.mark.parametrize("code_snippet, expected_complexity", [
    # --- Basic Structure ---
    ("let a = 1; let b = 2; return a + b;", "O(1)"),
    
    # --- Constant Loops (The "Sudoku" Case) ---
    ("for (let i = 0; i < 9; i++) { console.log(i); }", "O(1)"),
    
    # --- Variable Loops ---
    ("for (let i = 0; i < n; i++) { console.log(i); }", "O(N)"),
    
    # --- Nested Loops (Quadratic) ---
    ("""
        for (let i = 0; i < nums.length; i++) {
            for (let j = i + 1; j < nums.length; j++) {
                if (nums[i] === nums[j]) return true;
            }
        }
    """, "O(N^2)"),
    
    # --- Sorting (N log N) ---
    ("""
      nums.sort((a, b) => a - b);
        for (let i = 1; i < nums.length; i++) {
            if (nums[i] === nums[i - 1]) return true;
        }
    """, "O(N log N)"), 

    # --- Modern Loops (For...of) ---
    ("""
        const seen = new Set();
        for (const num of nums) {
            if (seen.has(num)) return true;
            seen.add(num);
        }
    """, "O(N)"), 
        
    # --- Linear Constructors ---
    ("return new Set(nums).size < nums.length", "O(N)"),

    # --- Method Chaining (The "Top K Frequent" Case) ---
    ("""
        const arr = Object.entries(count).map(([num, freq]) => [freq, num]);
        arr.sort((a, b) => b[0] - a[0]);
    """, "O(N log N)"),

    # --- Heap / Priority Queue ---
    ("""
        const heap = new MinPriorityQueue();
        for (const [num, cnt] of Object.entries(count)) {
            heap.enqueue([num, cnt]);
            if (heap.size() > k) heap.dequeue();
        }
    """, "O(N log N)"),
])
def test_time_complexity_analysis(code_snippet, expected_complexity):
    complexity, reason = analyze_time_complexity(code_snippet)
    print(f"Reason: {reason}")
    assert complexity == expected_complexity