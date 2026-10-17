from __future__ import annotations

from pathlib import Path

from kaiwen_agent.kits.coding import CodingKit
from kaiwen_agent.models import FakeModelProvider
from kaiwen_agent.types import ModelResponse


def main() -> None:
    """Demonstrate that team mode cannot be enabled implicitly.

    A production host supplies CodingTeamFactory + TeamRuntime + JobManager through a
    CodingTeamBinding. See docs/coding-kits/SIMPLE_API.md for that boundary.
    """

    kit = CodingKit.local(
        workspace=Path.cwd(),
        provider="fake",
        model="deterministic",
        provider_factory=lambda _: FakeModelProvider([ModelResponse(text="unused")]),
    )
    report = kit.preflight(mode="team", team=True)
    print(*(f"{issue.code}: {issue.message}" for issue in report.issues), sep="\n")
    assert not report.ok
    assert any(issue.code == "team_not_configured" for issue in report.issues)


if __name__ == "__main__":
    main()
