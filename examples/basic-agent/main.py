import asyncio

from kaiwen_agent import Agent, AgentContext, tool
from kaiwen_agent.models.fake import FakeModelProvider
from kaiwen_agent.types import AgentInput, ModelResponse, ToolCall
from pydantic import BaseModel


class ProjectQuery(BaseModel):
    category: str | None = None


@tool(
    name="projects.read",
    description="List example projects",
    input_model=ProjectQuery,
    permissions={"projects.read"},
)
async def read_projects(context: AgentContext, query: ProjectQuery) -> list[dict[str, str]]:
    del context
    projects = [{"name": "Cube Rivals", "category": "game"}]
    if query.category:
        return [item for item in projects if item["category"] == query.category]
    return projects


async def main() -> None:
    provider = FakeModelProvider(
        [
            ModelResponse(
                tool_calls=[
                    ToolCall(id="call_1", name="projects.read", arguments={"category": "game"})
                ]
            ),
            ModelResponse(text="Bir oyun bulundu: Cube Rivals."),
        ]
    )
    agent = Agent(
        name="basic-example",
        model=provider,
        tools=[read_projects],
        permissions={"projects.read"},
    )
    result = await agent.run(
        AgentInput(text="Oyunları göster"),
        context=AgentContext(
            session_id="example-session",
            permissions=frozenset({"projects.read"}),
        ),
    )
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
