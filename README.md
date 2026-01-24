COMMAND TO RUN THE CODE

TO INSTALL THE PACKAGES:

```bash
pip install -r requirements.txt
```

TO RUN THE CODE:

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

```bash
Windows: venv\Scripts\activate
Linux/Mac: source venv/bin/activate
```

We are using uvicorn to run the application:

```bash
uvicorn main:app --reload
```

# 🚀 Big-O Static Analyzer Roadmap

### 📊 Project Status

| Phase       | Focus                      | Status             |
| :---------- | :------------------------- | :----------------- |
| **Phase 1** | Boundary & Truthiness      | ✅ **Complete**    |
| **Phase 2** | Structural Constructors    | 🚧 **In Progress** |
| **Phase 3** | Complexity Accumulator     | 📅 Planned         |
| **Phase 4** | Scope & Reference Tracking | 📅 Planned         |
| **Phase 5** | Space & Recursion          | 📅 Planned         |

---

## 🟢 Phase 1: Boundary & Truthiness Resolver

_Goal: Prove if a condition is mathematically bounded by a constant or if it is infinite/variable._

- [x] **Basic Literal Detection** (`number`, `string`, `boolean`, `null`, `undefined`).
- [x] **Structural Unwrapping** (Parentheses, Unary `!`, `-`, `+`).
- [x] **Binary Operator Logic** (Comparison, Math, Nullish Coalescing `??`).
- [x] **Semantic Truthiness Evaluator** (Handling `0`, `""`, `[]`, `{}` correctly).
- [x] **Logical Short-Circuiting** (e.g., `false && X` is $O(1)$).
- [x] **Dead Code Elimination** (Ternary folding: `true ? 1 : getN()`).
- [x] **Pure Global Whitelist** (`Math.PI`, `Number.MAX_SAFE_INTEGER`).
- [x] **Black-box Guard** (Treat unknown `call_expression` as non-constant).

---

## 🔵 Phase 2: Structural Constructor Analysis

_Goal: Distinguish between constant-time allocations and linear-time data copying._

- [ ] **Constructor Identification** (Detect `new Set`, `new Map`, `new Array`).
- [ ] **Argument Complexity Mapping** (Reuse Phase 1 logic on constructor args).
- [ ] **Empty/Fixed Literal Detection** (`new Set([])` vs `new Set(data)`).
- [ ] **Array-Length Logic** (`new Array(10)` is $O(1)$ vs `new Array(n)` is $O(N)$).
- [ ] **Nested Structure Analysis** (Handle `new Set([1, 2, 3])` as $O(1)$).

---

## 🟡 Phase 3: Complexity Accumulator (The Walker)

_Goal: Traverse the AST and calculate the final Big-O degree._

- [ ] **Nesting Depth Tracker** (Identifying $O(N^2)$ vs $O(N)$).
- [ ] **Sibling Logic** (Additive complexity: $O(N + M)$).
- [ ] **The "N Log N" Rule** (Detecting heap/sort methods + depth multiplication).
- [ ] **Sequential Method Chains** (Treating `.map().filter()` as sequential $O(N)$).
- [ ] **Dominance Comparison** (Simplifying $O(N^2 + N)$ to $O(N^2)$).

---

## 🟠 Phase 4: Reference & Scope Tracking

_Goal: Handle variables that act as constant aliases._

- [ ] **Local Constant Resolver** (Recognizing `const LIMIT = 10;` as a constant bound).
- [ ] **State Mutation Guard** (Flagging "Volatile" variables reassigned in loops).
- [ ] **Shadowing Protection** (Ensuring local names don't collide with inputs).

---

## 🔴 Phase 5: Space Complexity & Recursion

_Goal: Expand analysis to memory usage and functional patterns._

- [ ] **Auxiliary Space Tracker** (Measuring `Set`/`Map` memory growth).
- [ ] **Recursion Detection** (Identifying self-calls and exit conditions).
- [ ] **Depth-Limited Analysis** (Recursive calls with constant depth).

---

## 🧪 Definition of Done

- [ ] Passes the **Worst-Case Stress Test** (30+ complex edge cases).
- [ ] Zero "False Positives" for $O(1)$ on variable-bound loops.
- [ ] **Rice's Theorem Compliance:** Defaults to $O(Unknown)$ rather than guessing.
