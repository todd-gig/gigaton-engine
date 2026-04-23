"""Unit tests for segment library definitions."""

import unittest
from segmentation.segment_library import SEGMENT_LIBRARY


class TestSegmentLibrary(unittest.TestCase):
    """Test suite for predefined segment library."""

    def test_all_segments_have_unique_ids(self):
        """Test all segments have unique segment IDs."""
        segment_ids = [s.segment_id for s in SEGMENT_LIBRARY.values()]
        self.assertEqual(len(segment_ids), len(set(segment_ids)))

    def test_all_segments_have_non_empty_service_package(self):
        """Test all segments have at least one service in service_package_fit."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertTrue(
                len(segment.service_package_fit) > 0,
                f"{segment_key} has empty service_package_fit",
            )

    def test_all_segments_have_valid_priority_tier(self):
        """Test all segments have valid priority_tier (1-3)."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertIn(
                segment.priority_tier,
                [1, 2, 3],
                f"{segment_key} has invalid priority_tier: {segment.priority_tier}",
            )

    def test_all_segments_have_apollo_targeting(self):
        """Test all segments have apollo_targeting with at least titles and industries."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertIsNotNone(
                segment.apollo_targeting,
                f"{segment_key} has no apollo_targeting",
            )
            self.assertTrue(
                len(segment.apollo_targeting.titles) > 0,
                f"{segment_key} apollo_targeting has no titles",
            )
            self.assertTrue(
                len(segment.apollo_targeting.industries) > 0,
                f"{segment_key} apollo_targeting has no industries",
            )

    def test_all_segment_criteria_have_valid_keys(self):
        """Test all segment criteria have valid dimension keys."""
        valid_keys = {
            "economic_scale",
            "fit_score",
            "need",
            "service_fit",
            "readiness",
            "accessibility",
            "expected_uplift",
            "confidence",
            "marketing_maturity",
            "sales_complexity",
            "measurement_maturity",
            "interaction_management_maturity",
            "gtm_motion",
        }

        for segment_key, segment in SEGMENT_LIBRARY.items():
            for criteria_key in segment.qualifying_criteria.keys():
                self.assertIn(
                    criteria_key,
                    valid_keys,
                    f"{segment_key} has invalid criteria key: {criteria_key}",
                )

    def test_to_apollo_filters_produces_valid_structure(self):
        """Test that to_apollo_filters() produces dict with expected structure."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            filters = segment.apollo_targeting.to_apollo_filters()

            # Should be a dict
            self.assertIsInstance(filters, dict)

            # All values should be lists or dicts
            for key, value in filters.items():
                self.assertIsInstance(
                    value,
                    (list, dict),
                    f"{segment_key} filter {key} has non-list/dict value",
                )

    def test_all_expected_value_ranges_are_valid(self):
        """Test all segments have valid expected_value_range."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            min_val, max_val = segment.expected_value_range

            # Both should be numbers
            self.assertIsInstance(
                min_val,
                (int, float),
                f"{segment_key} min value is not numeric",
            )
            self.assertIsInstance(
                max_val,
                (int, float),
                f"{segment_key} max value is not numeric",
            )

            # Both should be 0-100
            self.assertGreaterEqual(
                min_val,
                0,
                f"{segment_key} min value < 0",
            )
            self.assertLessEqual(
                min_val,
                100,
                f"{segment_key} min value > 100",
            )
            self.assertGreaterEqual(
                max_val,
                0,
                f"{segment_key} max value < 0",
            )
            self.assertLessEqual(
                max_val,
                100,
                f"{segment_key} max value > 100",
            )

            # Min should be <= Max
            self.assertLessEqual(
                min_val,
                max_val,
                f"{segment_key} min value > max value",
            )

    def test_all_segments_have_defined_gap_pattern(self):
        """Test all segments reference one of the 8 defined gap patterns."""
        valid_gap_patterns = {
            "strong traffic / weak conversion architecture",
            "broad service claims / thin proof",
            "clear enterprise motion / poor trust layer",
            "public pricing / weak CTA and form strategy",
            "heavy content / weak analytics instrumentation",
            "complex offerings / poor navigation taxonomy",
            "strong product / weak interaction consistency",
            "strong brand narrative / weak sales enablement",
        }

        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertIn(
                segment.primary_gap_pattern,
                valid_gap_patterns,
                f"{segment_key} has invalid gap pattern: {segment.primary_gap_pattern}",
            )

    def test_all_segments_have_required_fields(self):
        """Test all segments have all required fields."""
        required_fields = {
            "segment_id",
            "segment_name",
            "description",
            "qualifying_criteria",
            "service_package_fit",
            "expected_value_range",
            "priority_tier",
            "primary_gap_pattern",
            "apollo_targeting",
        }

        for segment_key, segment in SEGMENT_LIBRARY.items():
            for field_name in required_fields:
                self.assertTrue(
                    hasattr(segment, field_name),
                    f"{segment_key} missing field: {field_name}",
                )

    def test_segment_library_has_expected_segments(self):
        """Test that the library contains the expected 5 segments."""
        expected_ids = {"SEG_001", "SEG_002", "SEG_003", "SEG_004", "SEG_005"}
        actual_ids = {s.segment_id for s in SEGMENT_LIBRARY.values()}

        self.assertEqual(actual_ids, expected_ids)

    def test_segments_have_non_empty_descriptions(self):
        """Test all segments have non-empty descriptions."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertTrue(
                len(segment.description) > 0,
                f"{segment_key} has empty description",
            )

    def test_segments_have_non_empty_names(self):
        """Test all segments have non-empty names."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertTrue(
                len(segment.segment_name) > 0,
                f"{segment_key} has empty segment_name",
            )

    def test_segment_ids_match_naming_convention(self):
        """Test all segment IDs follow SEG_XXX naming convention."""
        for segment_key, segment in SEGMENT_LIBRARY.items():
            self.assertTrue(
                segment.segment_id.startswith("SEG_"),
                f"{segment_key} ID doesn't follow SEG_XXX pattern: {segment.segment_id}",
            )


if __name__ == "__main__":
    unittest.main()
