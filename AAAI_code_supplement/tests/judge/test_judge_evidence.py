import unittest

from judge_evidence import (
    find_winning_threshold,
    reconstruct_record_evidence,
    replay_winners,
)


def _synthetic_record():
    profiles = [
        {
            "agent_id": "A",
            "daily_salary": 200.0,
            "water_requirement": 6.0,
        },
        {
            "agent_id": "B",
            "daily_salary": 200.0,
            "water_requirement": 4.0,
        },
        {
            "agent_id": "C",
            "daily_salary": 200.0,
            "water_requirement": 7.0,
        },
    ]

    traces = {
        "A": [
            (1, 50.0, 10.0, 150.0, "alive"),
            (2, 100.0, 10.0, 250.0, "alive"),
            (3, 150.0, 10.0, 300.0, "alive"),
            (4, 200.0, 10.0, 300.0, "alive"),
            (5, 250.0, 10.0, 250.0, "alive"),
        ],
        "B": [
            (1, 40.0, 10.0, 160.0, "alive"),
            (2, 80.0, 10.0, 280.0, "alive"),
            (3, 120.0, 10.0, 360.0, "alive"),
            (4, 160.0, 10.0, 400.0, "alive"),
            (5, 200.0, 10.0, 400.0, "alive"),
        ],
        "C": [
            (1, 30.0, 7.0, 200.0, "alive"),
            (2, 60.0, 5.0, 400.0, "alive"),
            (3, 90.0, 2.0, 600.0, "alive"),
            (4, 120.0, -2.0, 0.0, "dead"),
            # The simulator pads dead agents through the end of the episode.
            (5, 0.0, -2.0, 0.0, "dead"),
        ],
    }

    agents = []
    for agent_id, rows in traces.items():
        agents.append(
            {
                "agent_id": agent_id,
                "daily_trace": [
                    {
                        "day": day,
                        "supply": 10.0,
                        "bid": bid,
                        "hp_after": hp_after,
                        "budget_after": budget_after,
                        "status": status,
                        "error": None,
                    }
                    for day, bid, hp_after, budget_after, status in rows
                ],
                "metrics": {
                    "strategy_complexity": 2,
                    "branch_count": 1,
                    "loop_count": 0,
                    "function_call_count": 1,
                    "failure_types": ["SHOULD_NOT_BE_USED_FOR_RECONSTRUCTION"],
                },
            }
        )

    return {
        "environment": {
            "scenario": "synthetic",
            "episode_days": 5,
            "supply_list": [10.0] * 5,
            "players": profiles,
        },
        "agents": agents,
    }


class ReplayAndThresholdTests(unittest.TestCase):
    def test_replay_winners_matches_greedy_packing(self):
        record = _synthetic_record()
        profiles = record["environment"]["players"]

        winners = replay_winners(
            {"A": 50.0, "B": 40.0, "C": 30.0},
            profiles,
            supply=10.0,
            day=1,
        )

        self.assertEqual(winners, ["A", "B"])

    def test_threshold_reports_strict_and_non_strict_breakpoints(self):
        record = _synthetic_record()
        profiles = record["environment"]["players"]
        strict = find_winning_threshold(
            focal_agent_id="C",
            bids={"A": 50.0, "B": 40.0, "C": 30.0},
            profiles=profiles,
            supply=10.0,
            day=1,
            budget_before_bid=200.0,
        )

        self.assertEqual(strict["amount"], 50.0)
        self.assertEqual(strict["comparison"], ">")
        self.assertTrue(strict["affordable"])
        self.assertTrue(strict["reachable"])

        tie_profiles = [
            {"agent_id": "F", "water_requirement": 5.0},
            {"agent_id": "X", "water_requirement": 6.0},
            {"agent_id": "Y", "water_requirement": 4.0},
        ]
        non_strict = find_winning_threshold(
            focal_agent_id="F",
            bids={"F": 0.0, "X": 50.0, "Y": 40.0},
            profiles=tie_profiles,
            supply=10.0,
            day=1,
            budget_before_bid=50.0,
        )

        self.assertEqual(non_strict["amount"], 50.0)
        self.assertEqual(non_strict["comparison"], ">=")
        self.assertTrue(non_strict["affordable"])
        self.assertTrue(non_strict["reachable"])

    def test_same_bid_and_requirement_uses_simulator_tie_seed(self):
        profiles = [
            {
                "agent_id": "Alex",
                "water_requirement": 13,
            },
            {
                "agent_id": "Bob",
                "water_requirement": 9,
            },
            {
                "agent_id": "Cindy",
                "water_requirement": 13,
            },
            {
                "agent_id": "David",
                "water_requirement": 7,
            },
            {
                "agent_id": "Eric",
                "water_requirement": 8,
            },
        ]
        winners = replay_winners(
            {
                "Alex": 300.0,
                "Bob": 252.0,
                "Cindy": 300.0,
                "David": 118.8252,
                "Eric": 254.8,
            },
            profiles,
            supply=19,
            day=4,
        )

        self.assertEqual(winners, ["Alex"])


class ReconstructionTests(unittest.TestCase):
    def test_reconstructs_payments_and_death_reset_without_padding(self):
        evidence = reconstruct_record_evidence(_synthetic_record())

        self.assertTrue(
            evidence["reconstruction_valid"],
            evidence["validation_mismatches"],
        )
        c_evidence = evidence["agents"]["C"]
        self.assertEqual(len(c_evidence["daily_evidence"]), 4)
        self.assertEqual(c_evidence["summary"]["active_decision_days"], 4)

        death_day = c_evidence["daily_evidence"][-1]
        self.assertEqual(death_day["day"], 4)
        self.assertFalse(death_day["won_water"])
        self.assertEqual(death_day["budget_before_bid"], 800.0)
        self.assertEqual(death_day["actual_payment"], 0.0)
        self.assertEqual(death_day["budget_after_payment"], 800.0)
        self.assertEqual(death_day["budget_before_death_reset"], 800.0)
        self.assertEqual(death_day["logged_budget_after"], 0.0)
        self.assertTrue(death_day["death_budget_reset_applied"])

        self.assertEqual(c_evidence["summary"]["total_submitted_bid"], 300.0)
        self.assertEqual(c_evidence["summary"]["total_actual_payment"], 0.0)
        self.assertEqual(c_evidence["summary"]["death_day"], 4)
        self.assertEqual(c_evidence["summary"]["low_hp_days"], [3, 4])

    def test_winners_pay_bid_and_losers_pay_zero(self):
        evidence = reconstruct_record_evidence(_synthetic_record())

        a_day_one = evidence["agents"]["A"]["daily_evidence"][0]
        c_day_one = evidence["agents"]["C"]["daily_evidence"][0]

        self.assertTrue(a_day_one["won_water"])
        self.assertEqual(a_day_one["actual_payment"], 50.0)
        self.assertEqual(a_day_one["budget_after_payment"], 150.0)
        self.assertFalse(c_day_one["won_water"])
        self.assertEqual(c_day_one["actual_payment"], 0.0)
        self.assertEqual(c_day_one["budget_after_payment"], 200.0)

    def test_missing_post_death_padding_is_not_a_validation_error(self):
        record = _synthetic_record()
        c_agent = next(
            agent
            for agent in record["agents"]
            if agent["agent_id"] == "C"
        )
        c_agent["daily_trace"] = c_agent["daily_trace"][:-1]

        evidence = reconstruct_record_evidence(record)

        self.assertTrue(
            evidence["reconstruction_valid"],
            evidence["validation_mismatches"],
        )
        self.assertEqual(
            len(evidence["agents"]["C"]["daily_evidence"]),
            4,
        )


if __name__ == "__main__":
    unittest.main()
