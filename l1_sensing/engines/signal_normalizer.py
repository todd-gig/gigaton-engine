"""SignalNormalizer for ingesting and validating raw signals."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from l1_sensing.models.signal import SignalRecord, SignalClass


class SignalNormalizer:
    """Normalizes raw signal data into SignalRecord objects.

    Validates signal classes, assigns object IDs, and ensures data consistency.
    """

    def __init__(self):
        """Initialize signal normalizer with counter tracking."""
        self._signal_counters: Dict[str, Dict[str, int]] = {}

    def normalize_signals(
        self, prospect_id: str, raw_signals: List[Dict[str, Any]]
    ) -> List[SignalRecord]:
        """Convert raw signal dicts to SignalRecord objects.

        Args:
            prospect_id: The prospect these signals relate to
            raw_signals: List of raw signal dictionaries

        Returns:
            List of validated SignalRecord objects
        """
        signals = []

        # Initialize counter for this prospect if needed
        if prospect_id not in self._signal_counters:
            self._signal_counters[prospect_id] = {}

        for raw_signal in raw_signals:
            try:
                signal = self._normalize_single_signal(prospect_id, raw_signal)
                if signal:
                    signals.append(signal)
            except ValueError:
                # Skip invalid signals
                continue

        return signals

    def _normalize_single_signal(
        self, prospect_id: str, raw_signal: Dict[str, Any]
    ) -> Optional[SignalRecord]:
        """Normalize a single raw signal to SignalRecord.

        Args:
            prospect_id: Prospect ID for this signal
            raw_signal: Raw signal dictionary

        Returns:
            SignalRecord if valid, None if invalid
        """
        # Validate required fields
        required_fields = [
            "signal_class",
            "signal_subtype",
            "raw_value",
            "source_url",
        ]
        if not all(field in raw_signal for field in required_fields):
            raise ValueError("Missing required signal fields")

        # Validate signal_class
        signal_class_str = raw_signal["signal_class"]
        if not SignalRecord.validate_signal_class(signal_class_str):
            raise ValueError(f"Invalid signal_class: {signal_class_str}")

        # Validate confidence
        confidence = raw_signal.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            raise ValueError(f"Confidence must be 0-1, got {confidence}")

        # Get or create counter for this signal class
        signal_class = signal_class_str
        if signal_class not in self._signal_counters[prospect_id]:
            self._signal_counters[prospect_id][signal_class] = 0
        else:
            self._signal_counters[prospect_id][signal_class] += 1

        counter = self._signal_counters[prospect_id][signal_class]

        # Generate object_id
        object_id = f"sig_{prospect_id}_{signal_class}_{counter}"

        # Set captured_at to now if not provided
        captured_at = raw_signal.get(
            "captured_at", datetime.now().isoformat()
        )

        # Normalize value (default to raw_value if not provided)
        normalized_value = raw_signal.get("normalized_value", raw_signal["raw_value"])

        # Build signal record
        signal = SignalRecord(
            object_id=object_id,
            prospect_id=prospect_id,
            signal_class=SignalClass(signal_class),
            signal_subtype=raw_signal["signal_subtype"],
            raw_value=raw_signal["raw_value"],
            normalized_value=normalized_value,
            source_url=raw_signal["source_url"],
            captured_at=captured_at,
            confidence=confidence,
            evidence_ids=raw_signal.get("evidence_ids", []),
        )

        return signal
