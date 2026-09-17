import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from kaiwen_agent.events import AgentEvent

FIXTURES = Path(__file__).parents[2] / "packages" / "protocol" / "fixtures"


def read_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_python_accepts_canonical_valid_event_fixture() -> None:
    event = AgentEvent.model_validate(read_fixture("event.valid.json"))
    assert event.schema_version == "1.0"
    assert event.type == "run.started"


def test_python_rejects_canonical_invalid_event_fixture() -> None:
    with pytest.raises(ValidationError):
        AgentEvent.model_validate(read_fixture("event.invalid.json"))

