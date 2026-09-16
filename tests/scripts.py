from app.agent_factory import get_agent

agent = get_agent()

extraction_llm = agent.nodes.extraction_llm

result = extraction_llm.invoke(
    "I need a double room."
)

print(result)
print(result.model_dump())