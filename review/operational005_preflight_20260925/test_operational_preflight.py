import unittest

import operational_preflight as gate


class OperationalPreflightGuardTests(unittest.TestCase):
    def test_all_declared_zero_fit_rejections(self):
        results = gate.guard_fixtures()
        self.assertEqual(len(results), 8)
        self.assertTrue(all(item["passed"] for item in results), results)

    def test_duplicate_alias_is_not_an_independent_evaluation(self):
        with self.assertRaisesRegex(ValueError, "duplicate_alias_counting"):
            gate.validate_alias_rows([
                {"unique_evaluation_id": "same", "is_alias": False},
                {"unique_evaluation_id": "same", "is_alias": False},
            ])

    def test_valid_alias_points_to_one_primary_evaluation(self):
        gate.validate_alias_rows([
            {"unique_evaluation_id": "one", "is_alias": False},
            {"unique_evaluation_id": "one", "is_alias": True},
        ])


if __name__ == "__main__":
    unittest.main()
