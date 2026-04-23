"""Unit tests for SignalNormalizer."""

import unittest
from datetime import datetime

from l1_sensing.engines.signal_normalizer import SignalNormalizer
from l1_sensing.models.signal import SignalClass


class TestSignalNormalizer(unittest.TestCase):
    """Test suite for SignalNormalizer."""

    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = SignalNormalizer()
        self.prospect_id = "prospect_123"

    def test_valid_signal_normalizes(self):
        """Valid signal should normalize without error."""
        raw_signal = {
            "signal_class": "identity",
            "signal_subtype": "company_name",
            "raw_value": "Example Corp",
            "normalized_value": "example_corp",
            "source_url": "https://example.com",
            "confidence": 0.95,
            "captured_at": datetime.now().isoformat(),
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )

        self.assertEqual(len(signals), 1)
        signal = signals[0]
        self.assertEqual(signal.raw_value, "Example Corp")
        self.assertEqual(signal.confidence, 0.95)

    def test_invalid_signal_class_rejected(self):
        """Invalid signal_class should be rejected."""
        raw_signal = {
            "signal_class": "invalid_class",
            "signal_subtype": "test",
            "raw_value": "test",
            "source_url": "https://example.com",
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )

        self.assertEqual(len(signals), 0)

    def test_object_id_format(self):
        """Object ID should follow format sig_prospectid_class_counter."""
        raw_signal = {
            "signal_class": "identity",
            "signal_subtype": "company_name",
            "raw_value": "Test",
            "source_url": "https://example.com",
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )

        signal = signals[0]
        expected_prefix = f"sig_{self.prospect_id}_identity_"
        self.assertTrue(signal.object_id.startswith(expected_prefix))

    def test_confidence_bounded_0_to_1(self):
        """Confidence must be 0-1."""
        # Valid confidence
        raw_signal = {
            "signal_class": "product",
            "signal_subtype": "feature",
            "raw_value": "test",
            "source_url": "https://example.com",
            "confidence": 0.75,
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )
        self.assertEqual(len(signals), 1)

        # Invalid confidence (too high)
        raw_signal["confidence"] = 1.5
        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )
        self.assertEqual(len(signals), 0)

        # Invalid confidence (negative)
        raw_signal["confidence"] = -0.1
        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )
        self.assertEqual(len(signals), 0)

    def test_multiple_signals_increment_counter(self):
        """Multiple signals of same class should have incrementing counters."""
        raw_signals = [
            {
                "signal_class": "audience",
                "signal_subtype": "targeting",
                "raw_value": f"signal_{i}",
                "source_url": "https://example.com",
            }
            for i in range(3)
        ]

        signals = self.normalizer.normalize_signals(
            self.prospect_id, raw_signals
        )

        self.assertEqual(len(signals), 3)

        # Check counters increment
        for i, signal in enumerate(signals):
            self.assertTrue(signal.object_id.endswith(f"_{i}"))

    def test_empty_input_returns_empty(self):
        """Empty signal list should return empty result."""
        signals = self.normalizer.normalize_signals(self.prospect_id, [])

        self.assertEqual(len(signals), 0)

    def test_preserves_raw_value(self):
        """Raw value should be preserved exactly."""
        raw_value = {"nested": "data", "count": 42}
        raw_signal = {
            "signal_class": "technical",
            "signal_subtype": "infrastructure",
            "raw_value": raw_value,
            "source_url": "https://example.com",
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )

        signal = signals[0]
        self.assertEqual(signal.raw_value, raw_value)

    def test_sets_captured_at(self):
        """Captured_at should be set to now if not provided."""
        raw_signal = {
            "signal_class": "pricing",
            "signal_subtype": "plan",
            "raw_value": "$99/month",
            "source_url": "https://example.com",
        }

        signals = self.normalizer.normalize_signals(
            self.prospect_id, [raw_signal]
        )

        signal = signals[0]
        # Should be ISO format string
        self.assertIsInstance(signal.captured_at, str)
        self.assertIn("T", signal.captured_at)  # ISO 8601

    def test_all_signal_classes_accepted(self):
        """All valid signal classes should be accepted."""
        valid_classes = [
            "identity",
            "audience",
            "narrative",
            "product",
            "pricing",
            "conversion",
            "trust",
            "team",
            "technical",
            "seo",
            "infrastructure",
            "external",
        ]

        for signal_class in valid_classes:
            raw_signal = {
                "signal_class": signal_class,
                "signal_subtype": "test",
                "raw_value": "test",
                "source_url": "https://example.com",
            }

            signals = self.normalizer.normalize_signals(
                self.prospect_id, [raw_signal]
            )

            self.assertEqual(
                len(signals),
                1,
                f"Signal class '{signal_class}' should be accepted",
            )

    def test_prospect_id_required(self):
        """Prospect ID must be provided and used in object_id."""
        raw_signal = {
            "signal_class": "external",
            "signal_subtype": "news",
            "raw_value": "news_item",
            "source_url": "https://example.com",
        }

        prospect_id = "special_prospect_999"
        signals = self.normalizer.normalize_signals(prospect_id, [raw_signal])

        signal = signals[0]
        self.assertIn(prospect_id, signal.object_id)
        self.assertEqual(signal.prospect_id, prospect_id)


if __name__ == "__main__":
    unittest.main()
