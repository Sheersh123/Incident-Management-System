"""Unit tests for RCA validation logic."""
import pytest
from unittest.mock import MagicMock, patch
from schemas.rca_schema import RCACreate
from services.rca_service import RCAService
from models.incident_model import Incident, IncidentStatus, RCA
from datetime import datetime


class TestRCAValidation:
    """Tests for mandatory RCA validation before closing an incident."""

    def test_valid_rca_passes_validation(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="SOFTWARE_BUG",
            fix_applied="Patched the null pointer exception",
            prevention_steps="Added input validation"
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is True
        assert error == ""

    def test_empty_category_fails_validation(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="",
            fix_applied="Some fix",
            prevention_steps="Some steps"
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is False
        assert "category" in error.lower()

    def test_whitespace_only_category_fails_validation(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="   ",
            fix_applied="Some fix",
            prevention_steps="Some steps"
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is False

    def test_empty_fix_applied_fails_validation(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="INFRASTRUCTURE",
            fix_applied="",
            prevention_steps="Monitor regularly"
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is False
        assert "fix" in error.lower()

    def test_empty_prevention_steps_fails_validation(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="NETWORK",
            fix_applied="Restarted the service",
            prevention_steps=""
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is False
        assert "prevention" in error.lower()

    def test_all_fields_empty_fails(self):
        rca = RCACreate(
            incident_id="test-123",
            root_cause_category="",
            fix_applied="",
            prevention_steps=""
        )
        is_valid, error = RCAService.validate_rca(rca)
        assert is_valid is False


class TestRCASubmission:
    """Tests for the full RCA submission flow with mocked DB."""

    @patch("services.rca_service.MTTRService")
    def test_submit_rca_for_nonexistent_incident(self, mock_mttr):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        rca = RCACreate(
            incident_id="nonexistent-id",
            root_cause_category="SOFTWARE_BUG",
            fix_applied="Fixed",
            prevention_steps="Prevented"
        )
        result, error = RCAService.submit_rca(mock_db, rca)
        assert result is None
        assert "not found" in error.lower()

    @patch("services.rca_service.MTTRService")
    def test_submit_rca_for_already_closed_incident(self, mock_mttr):
        mock_db = MagicMock()
        mock_incident = MagicMock()
        mock_incident.status = IncidentStatus.CLOSED

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_incident,  # First call: find incident
            None            # Second call: check existing RCA
        ]

        rca = RCACreate(
            incident_id="closed-id",
            root_cause_category="INFRASTRUCTURE",
            fix_applied="Already fixed",
            prevention_steps="N/A"
        )
        result, error = RCAService.submit_rca(mock_db, rca)
        assert result is None
        assert "already closed" in error.lower()


class TestIncidentStateTransitions:
    """Tests for the State Pattern — valid/invalid transitions."""

    def test_valid_transitions(self):
        from services.incident_service import IncidentStateMachine
        assert IncidentStateMachine.can_transition(IncidentStatus.OPEN, IncidentStatus.INVESTIGATING) is True
        assert IncidentStateMachine.can_transition(IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED) is True
        assert IncidentStateMachine.can_transition(IncidentStatus.RESOLVED, IncidentStatus.CLOSED) is True

    def test_invalid_transitions(self):
        from services.incident_service import IncidentStateMachine
        assert IncidentStateMachine.can_transition(IncidentStatus.OPEN, IncidentStatus.CLOSED) is False
        assert IncidentStateMachine.can_transition(IncidentStatus.OPEN, IncidentStatus.RESOLVED) is False
        assert IncidentStateMachine.can_transition(IncidentStatus.CLOSED, IncidentStatus.OPEN) is False
        assert IncidentStateMachine.can_transition(IncidentStatus.INVESTIGATING, IncidentStatus.OPEN) is False

    def test_closed_is_terminal(self):
        from services.incident_service import IncidentStateMachine
        for status in IncidentStatus:
            assert IncidentStateMachine.can_transition(IncidentStatus.CLOSED, status) is False

    def test_close_without_rca_rejected(self):
        from services.incident_service import IncidentStateMachine
        mock_incident = MagicMock()
        mock_incident.rca = None
        can_close, reason = IncidentStateMachine.validate_close(mock_incident)
        assert can_close is False
        assert "RCA" in reason

    def test_close_with_rca_allowed(self):
        from services.incident_service import IncidentStateMachine
        mock_incident = MagicMock()
        mock_incident.rca = MagicMock()  # RCA exists
        can_close, reason = IncidentStateMachine.validate_close(mock_incident)
        assert can_close is True
