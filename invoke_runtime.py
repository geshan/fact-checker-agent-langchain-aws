"""Invoke the deployed LangChain Fact Checker Agent on Amazon Bedrock AgentCore Runtime."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

import boto3
from dotenv import load_dotenv


def invoke_agent_runtime(
    claim: str,
    agent_runtime_arn: str,
    qualifier: str | None = None,
    region_name: str = "us-east-1",
) -> dict:
    """Invoke the AgentCore Runtime endpoint using boto3 bedrock-agentcore client."""
    client = boto3.client("bedrock-agentcore", region_name=region_name)
    session_id = str(uuid.uuid4()) + "-" + str(uuid.uuid4())  # >= 33 chars

    kwargs: dict = {
        "agentRuntimeArn": agent_runtime_arn,
        "runtimeSessionId": session_id,
        "payload": json.dumps({"claim": claim}).encode("utf-8"),
        "contentType": "application/json",
        "accept": "application/json",
    }
    if qualifier:
        kwargs["qualifier"] = qualifier

    response = client.invoke_agent_runtime(**kwargs)
    body = response.get("response")
    if hasattr(body, "read"):
        raw = body.read().decode("utf-8")
    else:
        raw = str(body)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(
        description="Invoke the deployed Fact Checker Agent on AWS Bedrock AgentCore Runtime"
    )
    parser.add_argument(
        "claim",
        nargs="?",
        default="The Sydney Harbour Bridge was opened in 1955.",
        help="The claim to fact-check on AgentCore Runtime.",
    )
    parser.add_argument(
        "--runtime-arn",
        default=os.getenv("AGENTCORE_RUNTIME_ARN"),
        help="ARN of the AgentCore Runtime (defaults to AGENTCORE_RUNTIME_ARN env var).",
    )
    parser.add_argument(
        "--qualifier",
        default=os.getenv("AGENTCORE_ENDPOINT_NAME", "fact_checker_langchain_endpoint"),
        help="Runtime endpoint name/qualifier.",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION", "us-east-1"),
        help="AWS region (defaults to us-east-1).",
    )
    args = parser.parse_args()

    if not args.runtime_arn:
        print(
            "Error: Provide --runtime-arn or set AGENTCORE_RUNTIME_ARN in .env",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Invoking AgentCore Runtime: {args.runtime_arn}")
    print(f"Qualifier: {args.qualifier}")
    print(f"Claim: {args.claim}\n" + "-" * 60)

    result = invoke_agent_runtime(
        claim=args.claim,
        agent_runtime_arn=args.runtime_arn,
        qualifier=args.qualifier,
        region_name=args.region,
    )
    if "verdict" in result:
        print(result["verdict"])
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
