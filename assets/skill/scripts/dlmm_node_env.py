"""Bounded V8 heap for every node child a Python helper spawns.

On 2026-11-08 one node child of the monitor reached ~4 GB RSS on a ~4 GB host
and the kernel's global OOM killer took the monitor down mid-close. A child
that hits this cap aborts inside its own process instead. Every state-changing
executor path persists its pending marker before it signs (close, deploy,
settlement swap), so an abort is the same recoverable outcome as the SIGKILL a
command timeout already sends. An operator NODE_OPTIONS that sets its own heap
size wins.

Spawners call cap_node_heap(os.environ) at import; children inherit it.
"""

EXECUTOR_HEAP_MB = 768


def cap_node_heap(env, heap_mb=None):
    options = env.get("NODE_OPTIONS", "")
    if "--max-old-space-size" not in options:
        env["NODE_OPTIONS"] = f"{options} --max-old-space-size={heap_mb or EXECUTOR_HEAP_MB}".strip()
    return env
