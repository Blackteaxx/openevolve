# Experience Knowledge Base

## I. Algorithmic & Data Structure Principles

### Rule ID: R001: [Prefer reducing algorithmic complexity over micro-optimizations]
* **Apply**: When a hotspot shows superlinear time | **Cost**: May require significant refactor
* **Why**: Moving from O(n²) to O(n log n)/O(n) dwarfs constant-factor tweaks.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R002: [Use `dict`/`set` for membership and counting instead of linear scans]
* **Apply**: Frequent lookups/uniqueness/counting | **Cost**: Higher memory; keys must be hashable
* **Why**: Average O(1) lookup beats O(n) list scans.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R003: [Use binary search (`bisect`) on sorted sequences]
* **Apply**: Insertion point or existence queries on sorted lists | **Cost**: Must maintain sorted order
* **Why**: O(log n) queries avoid repeated linear passes.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R004: [Use a heap (`heapq`) for streaming Top-K and k-way merge]
* **Apply**: Maintain rolling Top-K or merge multiple sorted streams | **Cost**: Slightly more complex than sort
* **Why**: O(log K) updates enable online processing without full materialization.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R005: [Prefer two-pointer/sliding-window on sorted arrays]
* **Apply**: Pair/window/coverage problems over ordered data | **Cost**: Careful pointer logic required
* **Why**: Collapses nested loops to linear time.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R006: [Use monotonic stack/queue for next-greater/window extrema]
* **Apply**: Span/extent/next-greater and fixed-window extrema | **Cost**: Higher conceptual overhead
* **Why**: Single pass computes repeated extrema efficiently.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R007: [Use prefix sums/differences for range queries and batch updates]
* **Apply**: Frequent range sum or range increment | **Cost**: Extra arrays and preprocessing
* **Why**: Turns per-query work into O(1) after O(n) prep.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R008: [Apply coordinate compression for sparse large keys]
* **Apply**: Only relative order matters; keys are large/sparse | **Cost**: One-time preprocessing
* **Why**: Dense indices improve cache locality and memory use.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R009: [Sort once, then answer queries via binary search / two-pointers]
* **Apply**: Many queries on the same array (counts, thresholds, pair sums, ranges) | **Cost**: O(n log n) presort; dynamic updates break order
* **Why**: Amortizes cost so each query is O(log n) or linear two-pointer instead of repeated scans.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R010: [Convert online queries to offline with sorting/sweep]
* **Apply**: Range queries, “≤ R” constraints, add/remove events | **Cost**: Extra memory and preprocessing
* **Why**: Sorting enables one-pass solutions with Fenwick/DSU, cutting complexity.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R011: [Use prefix-min/max and suffix-min/max for “remove-one” or edge-range extrema]

* **Apply**: “Best after removing one element” or range-edge maxima/minima | **Cost**: Extra O(n) arrays
* **Why**: O(1) answers per query after O(n) preprocessing.
* **Origin**: Global Baseline: Iteration 0

## II. Memory & Locality Optimizations

### Rule ID: R001: [Avoid unnecessary intermediate lists; favor iterators/generators]
* **Apply**: Pipelines that can be streamed | **Cost**: Debugging/visibility can be harder
* **Why**: Reduces peak memory and allocation churn.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R002: [Build large strings with `''.join(parts)`]
* **Apply**: Accumulating many string fragments | **Cost**: Must buffer parts
* **Why**: One allocation avoids quadratic copy behavior.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R003: [Use `collections.deque` for O(1) queue-front operations]
* **Apply**: Frequent `popleft/appendleft` | **Cost**: No random indexing
* **Why**: List head operations are O(n); deque is O(1) at ends.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R004: [Preallocate fixed-size lists and index directly]
* **Apply**: Known-size arrays, DP tables, visited flags | **Cost**: More boilerplate than `append`
* **Why**: Avoids dynamic growth and repeated reallocations in hot loops.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R005: [Represent boolean grids/visited as bitsets or bytes]
* **Apply**: Large grids/bitmaps | **Cost**: Bit operations reduce readability
* **Why**: Up to 8× memory reduction and better cache locality than Python `bool` lists.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R006: [Pack small state into integers (bit masks) for BFS/DP]
* **Apply**: Small alphabets, on/off features, subset DP | **Cost**: Encode/decode overhead
* **Why**: Compact states hash faster and use less memory.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R007: [Prefer iterative DFS with an explicit stack when depth is large]
* **Apply**: Deep trees/graphs (depth > recursion limit) | **Cost**: Slightly more code
* **Why**: Avoids recursion overhead and recursion-limit issues.
* **Origin**: Global Baseline: Iteration 0

## III. Language-Specific Idioms

### Rule ID: R001: [Prefer built-ins/NumPy/itertools over Python loops]
* **Apply**: Aggregation, transformation, search | **Cost**: Requires refactoring mindset
* **Why**: C-accelerated primitives are often orders of magnitude faster.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R002: [Use list comprehensions or `map` with built-ins]
* **Apply**: Simple elementwise transforms/filters | **Cost**: Balance readability
* **Why**: Comprehensions beat manual loops; `map`+built-ins avoid Python call overhead.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R003: [Bind hot attributes/functions to locals]
* **Apply**: Tight loops repeatedly accessing attributes/methods | **Cost**: One-time binding noise
* **Why**: Local variable lookup is faster than repeated dict/attribute resolution.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R004: [Hoist loop invariants]
* **Apply**: Recomputations inside tight loops | **Cost**: Requires invariants analysis
* **Why**: Fewer calls and loads reduce interpreter overhead.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R005: [Avoid exceptions for expected control flow]
* **Apply**: Misses are common or predictable | **Cost**: Extra branches
* **Why**: Raising/catching exceptions is expensive; prefer `in`/`get`.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R006: [Cache pure functions with `functools.lru_cache`]
* **Apply**: Same inputs recur frequently | **Cost**: Additional memory
* **Why**: Eliminates redundant computation via memoization.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R007: [Bind hot methods/functions to locals inside tight loops]
* **Apply**: Frequent `append`, `heappush/pop`, `write` | **Cost**: Minor naming noise
* **Why**: Local lookup is cheaper than repeated attribute resolution.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R008: [Use `math.isqrt` and integer loops for divisor checks]
* **Apply**: Trial division, perfect-square tests | **Cost**: Python ≥3.8
* **Why**: Exact integer sqrt is faster and avoids FP rounding issues.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R009: [Use `pow(base, exp, mod)` for fast modular exponentiation]
* **Apply**: Modular arithmetic (combinatorics/number theory) | **Cost**: Modulus-specific code path
* **Why**: Built-in exponentiation-by-squaring in C is far faster than Python loops.
* **Origin**: Global Baseline: Iteration 0

## IV. I/O & System Call Efficiency (Concerns file reading/writing, network communication, system call optimization, etc.)

### Rule ID: R001: [Bulk-read input via `sys.stdin.buffer.read` and parse once]
* **Apply**: Very large tokenized stdin workloads | **Cost**: Manual parsing required
* **Why**: Fewer syscalls and Python calls improve throughput.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R002: [Use `sys.stdin.buffer.readline` (bound locally) for line-structured input]
* **Apply**: Per-line semantics (grids, per-test lines) | **Cost**: Still line-by-line calls
* **Why**: Faster than `input()` and avoids full-buffer split for line tasks.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R003: [Accumulate outputs and emit once with `'\n'.join(...)` and buffered `write`]
* **Apply**: Many small outputs | **Cost**: Needs memory for the buffer
* **Why**: Fewer locks and flushes; higher throughput.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R004: [Match parser to data: bulk `read`+split for tokens, `readline` for line semantics]
* **Apply**: Known input shape (token stream vs per-line) | **Cost**: Maintain two code paths
* **Why**: Aligning parser with structure minimizes overhead and parsing cost.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R005: [Batch output; avoid per-item `print`]
* **Apply**: High-volume stdout | **Cost**: Manual newline/flush handling
* **Why**: Reduces synchronization and syscall frequency.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R006: [Parse once, reuse many times]
* **Apply**: Tokens/lines reused across steps | **Cost**: Extra variables
* **Why**: Avoids repeated `int()`/`strip()` conversions and extra scans.
* **Origin**: Global Baseline: Iteration 0

### Rule ID: R007: [For interactive problems, flush deliberately and minimize chatter]
* **Apply**: Interactive judges requiring immediate responses | **Cost**: Risk of over-flushing
* **Why**: `print(..., flush=True)` or `sys.stdout.flush()` ensures timely reads; fewer extraneous prints reduce latency.
* **Origin**: Global Baseline: Iteration 0
