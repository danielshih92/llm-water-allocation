import copy
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sandbox_executor import execute_strategy

SCENARIOS = {
    "low": (10, 20),
    "medium": (15, 25),
    "high": (20, 30),
}


@dataclass
class AgentProfile:
    agent_id: str
    water_requirement: int
    daily_salary: float


@dataclass
class AgentRuntimeState:
    hp: int
    budget: float
    no_water_days: int
    alive: bool


@dataclass
class AgentSubmission:
    agent_id: str
    reasoning_cot: str
    strategy_code: str


def default_agent_profiles() -> List[AgentProfile]:
    return [
        AgentProfile("Alex", 13, 70),
        AgentProfile("Bob", 9, 90),
        AgentProfile("Cindy", 13, 150),
        AgentProfile("David", 7, 80),
        AgentProfile("Eric", 8, 140),
    ]


def build_supply_list(scenario: str, days: int, seed: Optional[int]) -> List[int]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    lower, upper = SCENARIOS[scenario]
    rng = random.Random(seed)
    return [rng.randint(lower, upper) for _ in range(days)]


class WACProgrammaticEnv:
    def __init__(
        self,
        episode_days: int = 10,
        start_hp: int = 8,
        max_hp: int = 10,
        start_no_water_days: int = 1,
    ) -> None:
        self.episode_days = episode_days
        self.start_hp = start_hp
        self.max_hp = max_hp
        self.start_no_water_days = start_no_water_days

    def _init_runtime(self, profiles: List[AgentProfile]) -> Dict[str, AgentRuntimeState]:
        runtime: Dict[str, AgentRuntimeState] = {}
        for profile in profiles:
            runtime[profile.agent_id] = AgentRuntimeState(
                hp=self.start_hp,
                budget=0.0,
                no_water_days=self.start_no_water_days,
                alive=True,
            )
        return runtime

    def _sanitize_bid(self, bid: float, budget: float) -> float:
        import math

        try:
            bid = float(bid)
        except Exception:
            return 0.0

        if not math.isfinite(bid):
            return 0.0

        try:
            budget = float(budget)
        except Exception:
            budget = 0.0

        if (not math.isfinite(budget)) or budget < 0:
            budget = 0.0

        if bid < 0:
            bid = 0.0
        if bid > budget:
            bid = budget
        return float(bid)

    def _allocate_winners(
        self,
        bids: Dict[str, float],
        profiles: Dict[str, AgentProfile],
        supply: float,
        day: int,
    ) -> List[str]:
        tie_rng = random.Random(f"wac-tie-break-{day}-{supply}")
        candidates = []
        for agent_id, bid in bids.items():
            requirement = profiles[agent_id].water_requirement
            if bid <= 0:
                continue
            if requirement > supply:
                continue
            tie_break = tie_rng.random()
            candidates.append((agent_id, bid, requirement, tie_break))

        candidates.sort(key=lambda row: (-row[1], row[2], row[3]))

        winners: List[str] = []
        remaining = supply
        for agent_id, bid, requirement, _ in candidates:
            if requirement <= remaining:
                winners.append(agent_id)
                remaining -= requirement
        return winners
    
    def _compact_trace(
        self,
        trace: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not trace:
            return {
                "day": None,
                "bid": 0.0,
                "supply": None,
                "hp_after": None,
                "budget_after": None,
                "status": None,
            }

        bid = trace.get(
            "bid",
            0.0
        )

        if bid is None:
            bid = 0.0

        return {
            "day": trace.get("day"),
            "bid": bid,
            "supply": trace.get("supply"),
            "hp_after": trace.get("hp_after"),
            "budget_after": trace.get("budget_after"),
            "status": trace.get("status"),
        }    
    
    def _build_opponents_status(
        self,
        profiles: List[AgentProfile],
        runtime: Dict[str, AgentRuntimeState],
        traces: Dict[str, List[Dict[str, Any]]],
        current_agent_id: str,
    ) -> Dict[str, Dict[str, Any]]:

        opponents_status: Dict[str, Dict[str, Any]] = {}

        for other_profile in profiles:

            if other_profile.agent_id == current_agent_id:
                continue

            other_state = runtime[other_profile.agent_id]
            other_traces = traces.get(other_profile.agent_id, [])

            trace_history = [
                self._compact_trace(trace)
                for trace in other_traces[-2:]
            ]

            previous_trace = (
                trace_history[-1]
                if trace_history
                else self._compact_trace({})
            )

            last_bid = previous_trace["bid"]

            opponents_status[other_profile.agent_id] = {
                "agent_id": other_profile.agent_id,

                "hp": other_state.hp,
                "budget": other_state.budget,
                "no_water_days": other_state.no_water_days,
                "alive": other_state.alive,
                "water_requirement": other_profile.water_requirement,
                "daily_salary": other_profile.daily_salary,

                "last_bid": last_bid,
                "last_status": previous_trace["status"],
                "last_hp_after": previous_trace["hp_after"],
                "last_budget_after": previous_trace["budget_after"],

                "trace_history": trace_history,
            }

        return opponents_status

    def _compact_opponents_status_for_log(
        self,
        opponents_status: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:

        compact_status: Dict[str, Dict[str, Any]] = {}

        for opponent_id, status in opponents_status.items():
            if not isinstance(status, dict):
                compact_status[opponent_id] = status
                continue

            status_copy = dict(status)

            status_copy.pop("trace_history", None)

            compact_status[opponent_id] = status_copy

        return compact_status

    def run_episode(
        self,
        profiles: List[AgentProfile],
        submissions: List[AgentSubmission],
        supply_list: List[int],
    ) -> Dict[str, Any]:
        if len(supply_list) != self.episode_days:
            raise ValueError("Supply list must match episode_days")

        profile_map = {profile.agent_id: profile for profile in profiles}
        runtime = self._init_runtime(profiles)
        submission_map = {sub.agent_id: sub for sub in submissions}
        traces: Dict[str, List[Dict[str, Any]]] = {p.agent_id: [] for p in profiles}

        for day in range(1, self.episode_days + 1):
            supply = float(supply_list[day - 1])

            for profile in profiles:
                state = runtime[profile.agent_id]
                if state.alive:
                    state.budget += profile.daily_salary

            bids: Dict[str, float] = {}
            errors: Dict[str, Optional[str]] = {}
            opponents_snapshots: Dict[str, Dict[str, Dict[str, Any]]] = {}
            for profile in profiles:
                state = runtime[profile.agent_id]
                if not state.alive:
                    bids[profile.agent_id] = 0.0
                    errors[profile.agent_id] = None
                    continue

                my_status = {
                    "hp": state.hp,
                    "budget": state.budget,
                    "no_water_days": state.no_water_days,
                }
                day_context = {"supply": supply, "day": day}
                
                opponents_status = self._build_opponents_status(
                    profiles=profiles,
                    runtime=runtime,
                    traces=traces,
                    current_agent_id=profile.agent_id,
                )
                opponents_snapshots[profile.agent_id] = self._compact_opponents_status_for_log(
                    opponents_status
                )
                
                submission = submission_map.get(profile.agent_id)
                if submission is None:
                    bids[profile.agent_id] = 0.0
                    errors[profile.agent_id] = "missing_strategy"
                    continue

                raw_bid, error = execute_strategy(
                    submission.strategy_code,
                    day_context,
                    my_status,
                    opponents_status,
                )
                
                if error:
                    bids[profile.agent_id] = 0.0
                    errors[profile.agent_id] = error
                else:
                    bids[profile.agent_id] = self._sanitize_bid(raw_bid, state.budget)
                    errors[profile.agent_id] = None

            winners = self._allocate_winners(bids, profile_map, supply, day)

            for profile in profiles:
                state = runtime[profile.agent_id]
                if not state.alive:
                    traces[profile.agent_id].append(
                        {
                            "day": day,
                            "bid": bids[profile.agent_id],
                            "supply": supply,
                            "hp_after": state.hp,
                            "budget_after": state.budget,
                            "status": "alive" if state.alive else "dead",
                            "error": errors.get(profile.agent_id),
                        }
                    )
                    continue

                if profile.agent_id in winners:
                    state.hp = min(self.max_hp, state.hp + 2)
                    state.budget -= bids[profile.agent_id]
                    state.no_water_days = self.start_no_water_days
                else:
                    state.hp -= state.no_water_days
                    state.no_water_days += 1

                if state.hp <= 0:
                    state.alive = False
                    state.budget = 0.0

                traces[profile.agent_id].append(
                    {
                        "day": day,
                        "bid": bids[profile.agent_id],
                        "supply": supply,
                        "hp_after": state.hp,
                        "budget_after": state.budget,
                        "status": "alive" if state.alive else "dead",
                        "error": errors.get(profile.agent_id),
                    }
                )

        agents_block: List[Dict[str, Any]] = []
        for sub in submissions:
            agent_traces = traces.get(sub.agent_id, [])

            metrics = self._compute_agent_metrics(
                profile=profile_map[sub.agent_id],
                traces=agent_traces,
                strategy_code=sub.strategy_code,
                reasoning_cot=sub.reasoning_cot,
            )

            agents_block.append(
                {
                    "agent_id": sub.agent_id,
                    "reasoning_cot": sub.reasoning_cot,
                    "strategy_code": sub.strategy_code,
                    "daily_trace": agent_traces,
                    "metrics": metrics,
                }
            )
        return {"agents": agents_block}

    def build_meta_round_record(
        self,
        meta_round_id: int,
        profiles: List[AgentProfile],
        submissions: List[AgentSubmission],
        supply_list: List[int],
        scenario: str,
        seed: Optional[int],
    ) -> Dict[str, Any]:
        environment = {
            "scenario": scenario,
            "supply_range": SCENARIOS[scenario],
            "seed": seed,
            "episode_days": self.episode_days,
            "players": [
                {
                    "agent_id": p.agent_id,
                    "water_requirement": p.water_requirement,
                    "daily_salary": p.daily_salary,
                }
                for p in profiles
            ],
            "supply_list": supply_list,
        }
        episode_result = self.run_episode(profiles, submissions, supply_list)
        return {
            "meta_round_id": meta_round_id,
            "environment": environment,
            "agents": episode_result["agents"],
        }

    def save_meta_round_log(
        self,
        meta_round_record: Dict[str, Any],
        output_dir: str,
        experiment_id: str,
    ) -> str:
        exp_dir = os.path.join(output_dir, experiment_id)
        os.makedirs(exp_dir, exist_ok=True)

        meta_round_id = meta_round_record.get("meta_round_id", "unknown")
        filename = f"meta_round_{meta_round_id}.json"
        path = os.path.join(exp_dir, filename)

        record_to_save = copy.deepcopy(meta_round_record)

        with open(path, "w", encoding="utf-8") as handle:
            json.dump([record_to_save], handle, indent=2)

        return path
    
    def _compute_agent_metrics(
        self,
        profile,
        traces,
        strategy_code,
        reasoning_cot,
    ):

        import ast
        import math
        import statistics

        from collections import Counter

        bids = [
            t["bid"]
            for t in traces
        ]

        hp = [
            t["hp_after"]
            for t in traces
        ]

        supplies = [
            t["supply"]
            for t in traces
        ]

        errors = [
            t.get("error")
            for t in traces
        ]

        # ============================================================
        # Survival Metrics
        # ============================================================

        survival_days = 0

        for t in traces:

            if t["status"] == "dead":
                break

            survival_days += 1

        final_hp = hp[-1] if hp else 0

        # ============================================================
        # Compile / Runtime Success
        # ============================================================

        compile_success = not any(
            (
                err is not None
                and "compile_error" in str(err)
            )
            for err in errors
        )

        runtime_success = not any(
            err is not None
            for err in errors
        )

        # ============================================================
        # Bid Statistics
        # ============================================================

        total_bid = sum(bids)

        average_bid = (
            statistics.mean(bids)
            if bids else 0.0
        )

        bid_variance = (
            statistics.pvariance(bids)
            if len(bids) > 1 else 0.0
        )

        # ============================================================
        # Bid-Supply Sensitivity
        # ============================================================

        bid_supply_sensitivity = 0.0

        if len(bids) > 1:

            adaptation_pairs = []

            for i in range(1, len(bids)):

                supply_delta = (
                    supplies[i]
                    - supplies[i - 1]
                )

                bid_delta = (
                    bids[i]
                    - bids[i - 1]
                )

                adaptation_pairs.append(
                    abs(
                        bid_delta
                        * supply_delta
                    )
                )

            if adaptation_pairs:

                bid_supply_sensitivity = (
                    statistics.mean(
                        adaptation_pairs
                    )
                )

        # ============================================================
        # Bid Entropy
        # ============================================================

        bid_entropy = 0.0

        if bids:

            counts = Counter(bids)

            probs = [
                c / len(bids)
                for c in counts.values()
            ]

            bid_entropy = -sum(
                p * math.log2(p)
                for p in probs
                if p > 0
            )

        # ============================================================
        # Static Policy
        # ============================================================

        static_policy = (
            bid_variance < 1e-6
        )

        # ============================================================
        # Hallucinated API Detection
        # ============================================================

        hallucinated_api_count = 0

        invalid_access_patterns = [

            "my_status['water_requirement']",
            'my_status["water_requirement"]',

            "my_status['daily_salary']",
            'my_status["daily_salary"]',

            "day_context['supply_range']",
            'day_context["supply_range"]',

            "day_context['players']",
            'day_context["players"]',

            "day_context['episode_days']",
            'day_context["episode_days"]',
        ]

        for pattern in invalid_access_patterns:

            if pattern in strategy_code:

                hallucinated_api_count += 1

        # ============================================================
        # Strategy Complexity
        # ============================================================

        strategy_complexity = 0

        branch_count = 0

        loop_count = 0

        function_call_count = 0

        try:

            tree = ast.parse(strategy_code)

            nodes = list(ast.walk(tree))

            strategy_complexity = len(nodes)

            branch_count = sum(
                isinstance(node, ast.If)
                for node in nodes
            )

            loop_count = sum(
                isinstance(node, (ast.For, ast.While))
                for node in nodes
            )

            function_call_count = sum(
                isinstance(node, ast.Call)
                for node in nodes
            )

        except Exception:
            pass

        # ============================================================
        # Opponent Awareness
        # ============================================================

        opponent_keywords = [
            "opponent",
            "competition",
            "other agents",
            "aggressive",
            "conservative",
            "strategy",
            "bid",
        ]

        reasoning_lower = (
            reasoning_cot.lower()
        )

        opponent_awareness_score = sum(
            reasoning_lower.count(keyword)
            for keyword in opponent_keywords
        )

        # ============================================================
        # Utility Score
        # ============================================================

        utility_score = (
            survival_days * 100
            + final_hp * 20
            - total_bid * 0.5
        )

        # ============================================================
        # Survival Efficiency
        # ============================================================

        if total_bid > 0:

            survival_efficiency = (
                survival_days / total_bid
            )

        else:

            survival_efficiency = 0.0

        # ============================================================
        # Recovery Score
        # ============================================================

        recovery_score = 0

        for i in range(1, len(hp)):

            if (
                hp[i - 1] <= 3
                and hp[i] > hp[i - 1]
            ):
                recovery_score += 1

        # ============================================================
        # Supply-Bid Correlation
        # ============================================================

        supply_bid_correlation = 0.0

        if len(bids) > 1:

            try:

                bid_mean = (
                    statistics.mean(bids)
                )

                supply_mean = (
                    statistics.mean(supplies)
                )

                numerator = sum(
                    (
                        bids[i] - bid_mean
                    )
                    * (
                        supplies[i] - supply_mean
                    )
                    for i in range(len(bids))
                )

                denominator_left = math.sqrt(
                    sum(
                        (
                            b - bid_mean
                        ) ** 2
                        for b in bids
                    )
                )

                denominator_right = math.sqrt(
                    sum(
                        (
                            s - supply_mean
                        ) ** 2
                        for s in supplies
                    )
                )

                denominator = (
                    denominator_left
                    * denominator_right
                )

                if denominator > 0:

                    supply_bid_correlation = (
                        numerator / denominator
                    )

            except Exception:
                pass

        # ============================================================
        # Failure Classification
        # ============================================================

        failure_types = []

        if not compile_success:

            failure_types.append(
                "syntax_error"
            )

        if not runtime_success:

            failure_types.append(
                "runtime_error"
            )

        if hallucinated_api_count > 0:

            failure_types.append(
                "hallucinated_api"
            )

        if static_policy:

            failure_types.append(
                "static_policy"
            )

        if (
            survival_days < self.episode_days
            and average_bid < 5
        ):

            failure_types.append(
                "strategic_underbidding"
            )

        if (
            total_bid > 0
            and survival_efficiency < 0.02
        ):

            failure_types.append(
                "inefficient_resource_usage"
            )

        if not failure_types:

            failure_types.append("none")

        # ============================================================
        # Final Metrics
        # ============================================================

        return {

            # --------------------------------------------------------
            # Survival
            # --------------------------------------------------------

            "survival_days": survival_days,

            "final_hp": final_hp,

            # --------------------------------------------------------
            # Bidding
            # --------------------------------------------------------

            "total_bid": total_bid,

            "average_bid": average_bid,

            "bid_variance": bid_variance,

            "bid_entropy": bid_entropy,

            # --------------------------------------------------------
            # Strategic Behavior
            # --------------------------------------------------------

            "bid_supply_sensitivity": bid_supply_sensitivity,

            "static_policy": static_policy,

            "opponent_awareness_score":
            opponent_awareness_score,

            "recovery_score": recovery_score,

            "supply_bid_correlation":
            supply_bid_correlation,

            # --------------------------------------------------------
            # Reliability
            # --------------------------------------------------------

            "compile_success": compile_success,

            "runtime_success": runtime_success,

            "hallucinated_api_count":
            hallucinated_api_count,

            # --------------------------------------------------------
            # Complexity
            # --------------------------------------------------------

            "strategy_complexity":
            strategy_complexity,

            "branch_count":
            branch_count,

            "loop_count":
            loop_count,

            "function_call_count":
            function_call_count,

            # --------------------------------------------------------
            # Economics
            # --------------------------------------------------------

            "utility_score":
            utility_score,

            "survival_efficiency":
            survival_efficiency,

            # --------------------------------------------------------
            # Failure Analysis
            # --------------------------------------------------------

            "failure_types":
            failure_types,
        }
