"""Unit tests for FieldMapper."""

import pytest
from datetime import datetime, timezone
from antigravity.models import RawEvent
from antigravity.field_mapper.mapper import FieldMapper


def test_field_mapper_ranking_and_drag():
    mapper = FieldMapper()
    events = [
        RawEvent(
            source="test",
            stage="ci.integration-tests",
            status="failure",
            queue_seconds=120.0,
            duration_seconds=2400.0,
            repo="your-org/service-a",
        ),
        RawEvent(
            source="test",
            stage="ci.integration-tests",
            status="success",
            queue_seconds=120.0,
            duration_seconds=2400.0,
            repo="your-org/service-a",
        ),
        RawEvent(
            source="test",
            stage="ci.docker-build",
            status="success",
            queue_seconds=60.0,
            duration_seconds=600.0,
            repo="your-org/service-a",
        ),
    ]

    field = mapper.process_events(events, scope="repo", target="your-org/service-a")

    assert len(field.wells) == 2
    # Integration tests have higher drag than docker build
    assert field.wells[0].stage == "ci.integration-tests"
    assert field.wells[0].drag_coefficient == 1.0
    assert field.wells[1].stage == "ci.docker-build"
    assert field.wells[1].drag_coefficient < 1.0
    assert field.wells[0].p_fail == 0.5


def test_field_mapper_drag_vectors():
    mapper = FieldMapper()
    events = [
        RawEvent(
            source="test",
            stage="review.approval-queue",
            status="success",
            queue_seconds=1800.0,
            duration_seconds=300.0,
            repo="your-org/service-a",
        ),
    ]
    field = mapper.process_events(events)
    vectors = mapper.extract_drag_vectors(field)
    assert len(vectors) == 1
    assert vectors[0].well_id == "review.approval-queue"
    assert vectors[0].magnitude > 0
