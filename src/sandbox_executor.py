import math
import re
import inspect
import multiprocessing
from typing import Any, Dict, Optional, Tuple

DENY_PATTERNS = [
    r"\bimport\b",
    r"\bfrom\b",
    r"__",
    r"open\(",
    r"eval\(",
    r"exec\(",
    r"compile\(",
    r"globals\(",
    r"locals\(",
    r"vars\(",
    r"os\.",
    r"sys\.",
    r"subprocess",
    r"socket",
    r"pathlib",
    r"requests",
]

ALLOWED_BUILTINS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "float": float,
    "int": int,
    "len": len,
    "sum": sum,
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "range": range,
    "sorted": sorted,
    "enumerate": enumerate,
}

DEFAULT_TIMEOUT_SECONDS = 1.0


def _static_check(code: str) -> Optional[str]:
    # 1. 為了避免在註釋中誤判關鍵字，我們先移除所有註釋
    # 移除單行註釋 #
    clean_code = re.sub(r'#.*', '', code)
    # 移除多行註釋 """ ... """ 或 ''' ... '''
    clean_code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', clean_code, flags=re.DOTALL)
    
    # 2. 轉為小寫進行檢查
    lowered = clean_code.lower()
    
    for pattern in DENY_PATTERNS:
        if re.search(pattern, lowered):
            return f"static_check_failed: {pattern}"
    return None


def _execute_strategy_no_timeout(
    strategy_code: str,
    day_context: Dict[str, Any],
    my_status: Dict[str, Any],
    opponents_status: Optional[Dict[str, Any]] = None,
) -> Tuple[float, Optional[str]]:
    safe_globals: Dict[str, Any] = {
        "__builtins__": ALLOWED_BUILTINS,
        "math": math,
    }
    safe_locals: Dict[str, Any] = {}

    try:
        exec(strategy_code, safe_globals, safe_locals)
    except Exception as exc:
        return 0.0, f"compile_error: {exc}"

    get_bid = safe_locals.get("get_bid") or safe_globals.get("get_bid")
    if not callable(get_bid):
        return 0.0, "missing_get_bid"

    try:
        signature = inspect.signature(get_bid)
        param_count = len(signature.parameters)

        if param_count >= 3:
            result = get_bid(
                day_context,
                my_status,
                opponents_status or {},
            )
        else:
            result = get_bid(
                day_context,
                my_status,
            )
    except Exception as exc:
        return 0.0, f"runtime_error: {exc}"

    try:
        bid = float(result)
    except (TypeError, ValueError):
        return 0.0, "invalid_bid_type"

    if not math.isfinite(bid):
        return 0.0, "invalid_bid_value"

    return bid, None


def _strategy_worker(
    queue: multiprocessing.Queue,
    strategy_code: str,
    day_context: Dict[str, Any],
    my_status: Dict[str, Any],
    opponents_status: Optional[Dict[str, Any]],
) -> None:
    try:
        queue.put(
            _execute_strategy_no_timeout(
                strategy_code=strategy_code,
                day_context=day_context,
                my_status=my_status,
                opponents_status=opponents_status,
            )
        )
    except Exception as exc:
        queue.put((0.0, f"runtime_error: {exc}"))


def execute_strategy(
    strategy_code: str,
    day_context: Dict[str, Any],
    my_status: Dict[str, Any],
    opponents_status: Optional[Dict[str, Any]] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[float, Optional[str]]:
    error = _static_check(strategy_code)
    if error:
        return 0.0, error

    queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    process = multiprocessing.Process(
        target=_strategy_worker,
        args=(queue, strategy_code, day_context, my_status, opponents_status),
        daemon=True,
    )

    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return 0.0, "runtime_timeout"

    if queue.empty():
        return 0.0, "runtime_error: no_result"

    try:
        result = queue.get_nowait()
    except Exception:
        return 0.0, "runtime_error: no_result"

    if (
        isinstance(result, tuple)
        and len(result) == 2
    ):
        bid, err = result
        return float(bid), err

    return 0.0, "runtime_error: malformed_result"
