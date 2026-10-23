output "ecr_repository_url" {
  description = "ECR repository URL for the Fact Checker ARM64 container image."
  value       = aws_ecr_repository.agent.repository_url
}

output "gateway_identifier" {
  description = "ID of the AgentCore Gateway."
  value       = aws_bedrockagentcore_gateway.this.gateway_id
}

output "gateway_url" {
  description = "MCP endpoint URL of the AgentCore Gateway."
  value       = aws_bedrockagentcore_gateway.this.gateway_url
}

output "web_search_target_id" {
  description = "ID of the Web Search tool target attached to the AgentCore Gateway."
  value       = aws_bedrockagentcore_gateway_target.web_search.target_id
}

output "agent_runtime_id" {
  description = "ID of the deployed AgentCore Runtime (when deploy_runtime = true)."
  value       = var.deploy_runtime ? aws_bedrockagentcore_agent_runtime.agent[0].agent_runtime_id : null
}

output "agent_runtime_arn" {
  description = "ARN of the deployed AgentCore Runtime (when deploy_runtime = true)."
  value       = var.deploy_runtime ? aws_bedrockagentcore_agent_runtime.agent[0].agent_runtime_arn : null
}

output "agent_runtime_endpoint_arn" {
  description = "ARN of the deployed AgentCore Runtime Endpoint (when deploy_runtime = true)."
  value       = var.deploy_runtime ? aws_bedrockagentcore_agent_runtime_endpoint.agent[0].agent_runtime_endpoint_arn : null
}
