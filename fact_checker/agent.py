"""LangChain Fact Checker Agent using Amazon Bedrock AgentCore Gateway Web Search (supports Bedrock and Gemini LLMs)."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client

load_dotenv(override=True)

DEFAULT_BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"
DEFAULT_GOOGLE_MODEL_ID = "gemini-3.5-flash"
DEFAULT_REGION = "us-east-1"

FACT_CHECKER_INSTRUCTION = """You are a fact checker.
You will be skeptical about anything that is said to you.
You will search the web and verify the given information.
If it does not match, you will respond with the latest and factual information.
Always cite the source titles and URLs returned by the web search tool."""


def get_system_prompt() -> str:
    """Build the system prompt anchored to today's date."""
    today = date.today().isoformat()
    return f"{FACT_CHECKER_INSTRUCTION}\n\nToday's date is {today}. Always use the available web search tool to verify claims against current information."


def create_chat_model(
    model_id: str | None = None,
    region_name: str | None = None,
    temperature: float = 0.1,
) -> BaseChatModel:
    """Create the LangChain chat model (Google Gemini Flash or Amazon Bedrock Converse)."""
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    resolved_model = model_id or os.getenv("MODEL_ID") or os.getenv("BEDROCK_MODEL_ID")

    if provider in ("google", "gemini", "vertexai") or (
        resolved_model and resolved_model.startswith("gemini")
    ):
        gemini_model = (
            resolved_model
            if (resolved_model and resolved_model.startswith("gemini"))
            else os.getenv("GOOGLE_MODEL_ID", DEFAULT_GOOGLE_MODEL_ID)
        )
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            temperature=temperature,
        )

    bedrock_model = resolved_model or DEFAULT_BEDROCK_MODEL_ID
    resolved_region = region_name or os.getenv("AWS_REGION", DEFAULT_REGION)
    return ChatBedrockConverse(
        model=bedrock_model,
        region_name=resolved_region,
        temperature=temperature,
    )


def _extract_text_from_content(content: Any) -> str:
    """Normalize LangChain message content (string or list of content blocks) to string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
        return "\n".join(parts)
    return str(content)


async def check_fact(
    claim: str,
    gateway_url: str | None = None,
    model_id: str | None = None,
    region_name: str | None = None,
) -> str:
    """Verify a Claim using LangChain + AWS Bedrock AgentCore Gateway Web Search over MCP."""
    resolved_gateway_url = gateway_url or os.getenv("AGENTCORE_GATEWAY_URL")
    if not resolved_gateway_url:
        raise ValueError(
            "AGENTCORE_GATEWAY_URL environment variable is required to connect to the AgentCore Gateway Web Search tool."
        )

    resolved_region = region_name or os.getenv("AWS_REGION", DEFAULT_REGION)
    model = create_chat_model(model_id=model_id, region_name=resolved_region)

    try:
        async with aws_iam_streamablehttp_client(
            endpoint=resolved_gateway_url,
            aws_service="bedrock-agentcore",
            aws_region=resolved_region,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)

                agent = create_agent(
                    model=model,
                    tools=tools,
                    system_prompt=get_system_prompt(),
                    name="Facts",
                )

                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": claim}]}
                )
                messages = result.get("messages", [])
                if not messages:
                    return "No Fact-Check Verdict could be generated."
                last_message = messages[-1]
                return _extract_text_from_content(
                    getattr(last_message, "content", last_message)
                )
    except BaseExceptionGroup as eg:
        leaf: BaseException = eg
        while isinstance(leaf, BaseExceptionGroup) and leaf.exceptions:
            leaf = leaf.exceptions[0]
        if isinstance(leaf, Exception):
            raise leaf from eg
        raise
