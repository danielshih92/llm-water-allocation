from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

from sandbox_executor import execute_strategy


TEST_CASES = [
    {
        "name": "normal_status",
        "day_context": {"day": 1, "supply": 15.0},
        "my_status": {"hp": 10, "budget": 500.0, "no_water_days": 1},
        "opponents_status": {
            "Bob": {
                "agent_id": "Bob",
                "hp": 10,
                "budget": 500.0,
                "no_water_days": 1,
                "alive": True,
                "last_bid": 15.0,
            },
        },
    },
    {
        "name": "low_hp",
        "day_context": {"day": 2, "supply": 12.0},
        "my_status": {"hp": 2, "budget": 200.0, "no_water_days": 2},
        "opponents_status": {},
    },
    {
        "name": "low_budget",
        "day_context": {"day": 3, "supply": 18.0},
        "my_status": {"hp": 8, "budget": 5.0, "no_water_days": 1},
        "opponents_status": {},
    },
    {
        "name": "empty_opponents",
        "day_context": {"day": 4, "supply": 10.0},
        "my_status": {"hp": 6, "budget": 100.0, "no_water_days": 1},
        "opponents_status": {},
    },
    {
        "name": "missing_last_bid",
        "day_context": {"day": 5, "supply": 20.0},
        "my_status": {"hp": 7, "budget": 150.0, "no_water_days": 1},
        "opponents_status": {
            "Bob": {
                "agent_id": "Bob",
                "hp": 8,
                "budget": 120.0,
                "no_water_days": 1,
                "alive": True,
            },
        },
    },
]


@dataclass
class ValidationResult:
    admitted: bool
    compile_success: bool
    runtime_success: bool
    error_type: Optional[str]
    error_message: Optional[str]
    test_results: List[Dict[str, Any]]


def _error_type_from_message(error: str) -> str:
    if ":" in error:
        return error.split(":", 1)[0].strip()
    return error.strip()


def validate_strategy_code(
    strategy_code: Optional[str],
    timeout_seconds: float = 1.0,
) -> ValidationResult:
    if strategy_code is None or not str(strategy_code).strip():
        return ValidationResult(
            admitted=False,
            compile_success=False,
            runtime_success=False,
            error_type="code_extraction_failed",
            error_message="No executable get_bid strategy code was extracted.",
            test_results=[],
        )

    strategy_code = str(strategy_code)
    test_results: List[Dict[str, Any]] = []

    compile_success = True
    runtime_success = True

    for case in TEST_CASES:
        name = case["name"]
        day_context = case["day_context"]
        my_status = case["my_status"]
        opponents_status = case["opponents_status"]

        bid, error = execute_strategy(
            strategy_code,
            day_context,
            my_status,
            opponents_status,
            timeout_seconds=timeout_seconds,
        )

        case_result: Dict[str, Any] = {
            "name": name,
            "passed": False,
            "bid": bid,
            "error": error,
        }

        if error is not None:
            if error.startswith("compile_error") or error.startswith("static_check_failed") or error == "missing_get_bid":
                compile_success = False
            runtime_success = False
            case_result["validation_error"] = error
            test_results.append(case_result)
            return ValidationResult(
                admitted=False,
                compile_success=compile_success,
                runtime_success=runtime_success,
                error_type=_error_type_from_message(error),
                error_message=f"[{name}] execute_strategy error: {error}",
                test_results=test_results,
            )

        try:
            float_bid = float(bid)
        except (TypeError, ValueError):
            runtime_success = False
            case_result["validation_error"] = "invalid_bid_type"
            test_results.append(case_result)
            return ValidationResult(
                admitted=False,
                compile_success=compile_success,
                runtime_success=runtime_success,
                error_type="invalid_bid_type",
                error_message=f"[{name}] Bid cannot be converted to float: {bid}",
                test_results=test_results,
            )

        if not math.isfinite(float_bid):
            runtime_success = False
            case_result["validation_error"] = "invalid_bid_value"
            test_results.append(case_result)
            return ValidationResult(
                admitted=False,
                compile_success=compile_success,
                runtime_success=runtime_success,
                error_type="invalid_bid_value",
                error_message=f"[{name}] Bid must be finite, got: {float_bid}",
                test_results=test_results,
            )

        if float_bid < 0:
            runtime_success = False
            case_result["validation_error"] = "invalid_bid_range"
            test_results.append(case_result)
            return ValidationResult(
                admitted=False,
                compile_success=compile_success,
                runtime_success=runtime_success,
                error_type="invalid_bid_range",
                error_message=f"[{name}] Bid must be >= 0, got: {float_bid}",
                test_results=test_results,
            )

        budget = float(my_status.get("budget", 0.0))
        if float_bid > budget:
            runtime_success = False
            case_result["validation_error"] = "invalid_bid_budget_exceeded"
            test_results.append(case_result)
            return ValidationResult(
                admitted=False,
                compile_success=compile_success,
                runtime_success=runtime_success,
                error_type="invalid_bid_budget_exceeded",
                error_message=(
                    f"[{name}] Bid {float_bid} exceeds budget {budget}."
                ),
                test_results=test_results,
            )

        case_result["passed"] = True
        case_result["bid"] = float_bid
        test_results.append(case_result)

    return ValidationResult(
        admitted=True,
        compile_success=True,
        runtime_success=True,
        error_type=None,
        error_message=None,
        test_results=test_results,
    )
