try:
    from agno.agent import RunOutput as AgentRunResult  # type: ignore
except ImportError:
    from agno.agent import RunResponse as AgentRunResult  # type: ignore
