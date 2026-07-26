import json
import unittest

from failure_analysis.aggregation import (
    aggregate_paired_records,
    pair_judge_records,
)
from failure_analysis.parser import FailureJudgeParseError, parse_failure_response
from failure_analysis.pipeline import (
    _is_non_retryable_quota_error,
    _validate_response_against_item,
)
from failure_analysis.prompt import (
    build_failure_prompt,
    derive_context_evidence,
    derive_failure_evidence,
)


def _response(
    primary="fatal_undercommitment",
    status=None,
    contributing=None,
    contextual=None,
):
    contributing = list(contributing or [])
    contextual = list(contextual or [])
    attributed = primary is not None
    if status is None:
        status = "dominant_policy_failure" if attributed else "insufficient_evidence"
    represented = {primary, *contributing}
    boundary_checks = {
        "allocation_rule_error_explicit": "allocation_context_misreasoning"
        in represented,
        "risk_mapping_failure_explicit": "emergency_response_failure" in represented,
        "winner_curse_bridge_supported": "winners_curse_overpayment" in represented,
        "opponent_model_dominant": "competitive_threshold_miscalibration"
        in represented,
        "repeated_or_lethal_affordable_miss": bool(
            represented.intersection(
                {"fatal_undercommitment", "competitive_threshold_miscalibration"}
            )
        ),
    }
    return json.dumps(
        {
            "attribution_status": status,
            "primary_failure_mode": primary,
            "contributing_failure_modes": contributing,
            "contextual_contributors": contextual,
            "contextual_explanation": (
                "Context materially constrained survival." if contextual else ""
            ),
            "code_mechanism": "Reserve cap stays binding." if attributed else "",
            "evidence_days": [3, 4] if attributed else [],
            "failure_chain": ["risk rises", "bid stays capped"] if attributed else [],
            "counterevidence": "One win occurred earlier.",
            "boundary_checks": boundary_checks,
            "reasoning_policy_mismatch": False,
            "policy_trajectory_mismatch": False,
            "confidence": 4,
            "short_diagnosis": "Evidence-grounded diagnosis.",
        }
    )


def _record(item_id, label, judge_index):
    judge = parse_failure_response(_response(label))
    return {
        "item_id": item_id,
        "condition": "OPF",
        "model_name": "model-a",
        "judge_index": judge_index,
        "judge": judge,
    }


class FailureAnalysisTests(unittest.TestCase):
    def test_insufficient_quota_is_non_retryable(self):
        error = RuntimeError(
            "Error code: 429 - {'error': {'code': 'insufficient_quota', "
            "'message': 'You exceeded your current quota'}}"
        )
        self.assertTrue(_is_non_retryable_quota_error(error))
        self.assertFalse(_is_non_retryable_quota_error(RuntimeError("rate limit")))

    def test_parser_accepts_failure_only_schema(self):
        parsed = parse_failure_response(_response("winners_curse_overpayment"))
        self.assertEqual(parsed["primary_failure_mode"], "winners_curse_overpayment")
        self.assertEqual(parsed["confidence"], 4)

    def test_parser_rejects_failure_mode_with_insufficient_evidence(self):
        payload = json.loads(_response(None))
        payload["contributing_failure_modes"] = ["fatal_undercommitment"]
        with self.assertRaises(FailureJudgeParseError):
            parse_failure_response(json.dumps(payload))

    def test_non_dominant_boundary_need_not_be_listed_as_contributing_mode(self):
        payload = json.loads(_response("fatal_undercommitment"))
        payload["boundary_checks"]["winner_curse_bridge_supported"] = True
        parsed = parse_failure_response(json.dumps(payload))
        self.assertEqual(parsed["primary_failure_mode"], "fatal_undercommitment")
        self.assertTrue(
            parsed["boundary_checks"]["winner_curse_bridge_supported"]
        )

        parsed = parse_failure_response(
            _response(
                "fatal_undercommitment",
                contributing=["emergency_response_failure"],
            )
        )
        self.assertIn(
            "emergency_response_failure", parsed["contributing_failure_modes"]
        )

    def test_no_clear_policy_failure_requires_context_and_null_primary(self):
        payload = json.loads(
            _response(
                None,
                status="no_clear_policy_failure",
                contextual=["resource_disadvantaged_role"],
            )
        )
        payload["evidence_days"] = [3, 4]
        payload["failure_chain"] = [
            "A resource-disadvantaged role accumulated budget slowly.",
            "Later critical thresholds were unaffordable despite full-budget bids.",
        ]
        parsed = parse_failure_response(json.dumps(payload))
        self.assertIsNone(parsed["primary_failure_mode"])
        self.assertEqual(parsed["attribution_status"], "no_clear_policy_failure")
        self.assertEqual(len(parsed["failure_chain"]), 2)

    def test_insufficient_evidence_cannot_assert_failure_chain(self):
        payload = json.loads(_response(None))
        payload["failure_chain"] = ["An unsupported causal claim."]
        with self.assertRaises(FailureJudgeParseError):
            parse_failure_response(json.dumps(payload))

    def test_mixed_attribution_keeps_primary_contributing_and_context(self):
        parsed = parse_failure_response(
            _response(
                "fatal_undercommitment",
                status="mixed_policy_and_context",
                contributing=["winners_curse_overpayment"],
                contextual=["resource_disadvantaged_role"],
            )
        )
        self.assertEqual(parsed["primary_failure_mode"], "fatal_undercommitment")
        self.assertEqual(
            parsed["contributing_failure_modes"], ["winners_curse_overpayment"]
        )
        self.assertEqual(parsed["attribution_status"], "mixed_policy_and_context")

    def test_role_context_is_an_indicator_not_a_failure_label(self):
        item = {
            "agent_id": "Alex",
            "environment": {
                "players": [
                    {"agent_id": "Alex", "daily_salary": 70, "water_requirement": 13},
                    {"agent_id": "Bob", "daily_salary": 90, "water_requirement": 9},
                    {"agent_id": "Cindy", "daily_salary": 150, "water_requirement": 13},
                    {"agent_id": "David", "daily_salary": 80, "water_requirement": 7},
                    {"agent_id": "Eric", "daily_salary": 140, "water_requirement": 8},
                ]
            },
            "trajectory": {"daily_evidence": []},
        }
        context = derive_context_evidence(item)
        self.assertTrue(context["resource_disadvantaged_role_candidate"])

    def test_winner_curse_bridge_is_derived_from_prior_premium(self):
        item = {
            "trajectory": {
                "daily_evidence": [
                    {
                        "day": 1,
                        "won_water": True,
                        "actual_payment": 100,
                        "winning_threshold": {
                            "amount": 40,
                            "reachable": True,
                            "affordable": True,
                        },
                        "budget_before_bid": 120,
                        "bid": 100,
                        "hp_before": 10,
                        "no_water_days_before": 1,
                    },
                    {
                        "day": 4,
                        "won_water": False,
                        "actual_payment": 0,
                        "winning_threshold": {
                            "amount": 120,
                            "reachable": True,
                            "affordable": False,
                        },
                        "budget_before_bid": 80,
                        "bid": 80,
                        "hp_before": 3,
                        "no_water_days_before": 2,
                    },
                ]
            }
        }
        derived = derive_failure_evidence(item)
        self.assertEqual(len(derived["winner_curse_bridge_candidates"]), 1)
        bridge = derived["winner_curse_bridge_candidates"][0]
        self.assertEqual(bridge["budget_gap"], 40)
        self.assertEqual(bridge["accumulated_prior_ex_post_premium"], 60)

    def test_pipeline_rejects_winner_curse_without_bridge(self):
        parsed = parse_failure_response(_response("winners_curse_overpayment"))
        item = {"trajectory": {"daily_evidence": []}}
        with self.assertRaises(FailureJudgeParseError):
            _validate_response_against_item(parsed, item)

    def test_critical_affordable_miss_before_next_day_death_is_supported(self):
        item = {
            "trajectory": {
                "daily_evidence": [
                    {
                        "day": 5,
                        "won_water": False,
                        "status": "alive",
                        "hp_before": 6,
                        "no_water_days_before": 3,
                        "budget_before_bid": 347,
                        "bid": 145,
                        "winning_threshold": {
                            "amount": 232,
                            "reachable": True,
                            "affordable": True,
                        },
                    },
                    {
                        "day": 6,
                        "won_water": False,
                        "status": "dead",
                        "hp_before": 3,
                        "no_water_days_before": 4,
                        "budget_before_bid": 427,
                        "bid": 363,
                        "winning_threshold": {
                            "amount": 472,
                            "reachable": True,
                            "affordable": False,
                        },
                    },
                ]
            }
        }
        derived = derive_failure_evidence(item)
        self.assertTrue(derived["repeated_or_lethal_affordable_miss_supported"])
        self.assertEqual(
            derived["critical_affordable_miss_to_next_day_death"][0],
            {
                "affordable_miss_day": 5,
                "death_day": 6,
                "hp_before_miss": 6,
                "no_water_days_before_miss": 3,
                "budget_before_miss": 347,
                "submitted_bid": 145,
                "winning_threshold": 232,
            },
        )

    def test_single_critical_miss_is_allowed_only_for_mixed_attribution(self):
        item = {
            "trajectory": {
                "daily_evidence": [
                    {
                        "day": 3,
                        "won_water": False,
                        "status": "alive",
                        "hp_before": 5,
                        "no_water_days_before": 3,
                        "budget_before_bid": 210,
                        "bid": 100,
                        "winning_threshold": {
                            "amount": 170,
                            "reachable": True,
                            "affordable": True,
                        },
                    },
                    {
                        "day": 4,
                        "won_water": True,
                        "status": "alive",
                        "hp_before": 2,
                        "no_water_days_before": 4,
                        "budget_before_bid": 280,
                        "bid": 250,
                        "actual_payment": 250,
                        "winning_threshold": {
                            "amount": 220,
                            "reachable": True,
                            "affordable": True,
                        },
                    },
                    {
                        "day": 7,
                        "won_water": False,
                        "status": "dead",
                        "hp_before": 2,
                        "no_water_days_before": 2,
                        "budget_before_bid": 150,
                        "bid": 150,
                        "winning_threshold": {
                            "amount": 300,
                            "reachable": True,
                            "affordable": False,
                        },
                    },
                ]
            }
        }
        derived = derive_failure_evidence(item)
        self.assertEqual(len(derived["critical_affordable_threshold_misses"]), 1)
        self.assertFalse(derived["repeated_or_lethal_affordable_miss_supported"])

        mixed_payload = json.loads(
            _response(
                "fatal_undercommitment",
                status="mixed_policy_and_context",
                contextual=["unaffordable_competitive_pressure"],
            )
        )
        mixed_payload["boundary_checks"][
            "repeated_or_lethal_affordable_miss"
        ] = False
        mixed = parse_failure_response(json.dumps(mixed_payload))
        _validate_response_against_item(mixed, item)

        dominant = parse_failure_response(_response("fatal_undercommitment"))
        with self.assertRaises(FailureJudgeParseError):
            _validate_response_against_item(dominant, item)

    def test_two_judge_disagreement_contributes_half_vote_each(self):
        paired = pair_judge_records(
            [_record("item-1", "fatal_undercommitment", 1)],
            [_record("item-1", "winners_curse_overpayment", 2)],
        )
        self.assertEqual(
            paired[0]["averaged_primary_vote"]["fatal_undercommitment"], 0.5
        )
        self.assertEqual(
            paired[0]["averaged_primary_vote"]["winners_curse_overpayment"], 0.5
        )
        summary = aggregate_paired_records(paired)["overall"]
        self.assertEqual(summary["primary_agreement_rate"], 0.0)
        self.assertEqual(
            summary["averaged_primary_counts"]["fatal_undercommitment"], 0.5
        )

    def test_attribution_and_contributing_modes_are_aggregated_separately(self):
        left = _record("item-1", "fatal_undercommitment", 1)
        right = {
            **_record("item-1", "fatal_undercommitment", 2),
            "judge": parse_failure_response(
                _response(
                    "fatal_undercommitment",
                    status="mixed_policy_and_context",
                    contributing=["winners_curse_overpayment"],
                    contextual=["resource_disadvantaged_role"],
                )
            ),
        }
        summary = aggregate_paired_records(pair_judge_records([left], [right]))[
            "overall"
        ]
        self.assertEqual(summary["policy_attribution_coverage_rate"], 1.0)
        self.assertEqual(
            summary["averaged_attribution_status_counts"][
                "dominant_policy_failure"
            ],
            0.5,
        )
        self.assertEqual(
            summary["averaged_attribution_status_counts"][
                "mixed_policy_and_context"
            ],
            0.5,
        )
        self.assertEqual(
            summary["averaged_any_failure_mode_counts"][
                "winners_curse_overpayment"
            ],
            0.5,
        )

    def test_prompt_is_blinded_and_has_no_scalar_quality_scoring(self):
        item = {
            "model_name": "secret-model",
            "environment": {},
            "submission_status": {},
            "policy": {
                "final_reasoning": "reason",
                "final_code": "def get_bid(*args): return 0",
            },
            "trajectory": {
                "evidence_summary": {"final_status": "dead"},
                "daily_evidence": [],
            },
        }
        prompt = build_failure_prompt(item, blind_model_names=True)
        self.assertNotIn("secret-model", prompt)
        self.assertIn("winners_curse_overpayment", prompt)
        self.assertIn("derived_boundary_evidence", prompt)
        self.assertIn("derived_context_evidence", prompt)
        self.assertIn("mixed_policy_and_context", prompt)
        self.assertIn("boundary_checks", prompt)
        self.assertNotIn("strategy_quality_score", prompt)


if __name__ == "__main__":
    unittest.main()
