# Fact Checker Agent (LangChain + AWS Bedrock AgentCore)

A skeptical fact-verification agent running on Amazon Bedrock AgentCore Runtime that verifies claims against live public web data via the AgentCore Gateway Web Search capability.

## Language

**AgentCore Gateway**:
A managed MCP (Model Context Protocol) gateway in Amazon Bedrock AgentCore that exposes tools—specifically the AWS-managed `web-search` connector—to the agent over MCP with IAM authentication.
_Avoid_: API Gateway, Search Proxy, Tool Server

**AgentCore Runtime**:
The managed serverless microVM/container execution environment in Amazon Bedrock AgentCore that hosts and runs the LangChain Fact Checker agent.
_Avoid_: Bedrock Agents (Classic), Lambda Runtime, ECS Task

**Inference Profile**:
The cross-region Amazon Bedrock model endpoint (`us.amazon.nova-2-lite-v1:0`) invoked via the Bedrock Converse API (`ChatBedrockConverse`) to reason over claims and decide when to call Web Search.
_Avoid_: Base Model ID, Provisioned Throughput

**Claim**:
A statement, assertion, or question submitted by a caller to be verified against current public web facts.
_Avoid_: Prompt, Query, Input

**Fact-Check Verdict**:
The agent's grounded response that evaluates a Claim with skepticism, verifies it via the AgentCore Gateway Web Search tool, corrects inaccuracies with the latest factual information, and cites sources.
_Avoid_: Completion, Output, Answer


