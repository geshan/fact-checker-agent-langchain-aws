variable "aws_region" {
  description = "AWS region for Bedrock AgentCore Gateway, Web Search target, ECR, and Runtime (Web Search requires us-east-1)."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name for AgentCore Gateway, IAM roles, and ECR repository (hyphens allowed)."
  type        = string
  default     = "fact-checker-langchain"
}

variable "runtime_name" {
  description = "Name for the AgentCore Runtime and Runtime Endpoint (must match [a-zA-Z][a-zA-Z0-9_]{0,47}, underscores only)."
  type        = string
  default     = "fact_checker_langchain"
}

variable "bedrock_model_id" {
  description = "Bedrock inference profile ID used by the LangChain agent."
  type        = string
  default     = "us.amazon.nova-2-lite-v1:0"
}

variable "foundation_model_name" {
  description = "Underlying foundation model identifier for least-privilege wildcard-region IAM policy."
  type        = string
  default     = "amazon.nova-2-lite-v1:0"
}

variable "image_tag" {
  description = "Docker image tag in ECR to deploy to AgentCore Runtime."
  type        = string
  default     = "v1.0.0"
}

variable "deploy_runtime" {
  description = "Set to true after pushing the ARM64 container image to ECR to provision AgentCore Runtime and RuntimeEndpoint."
  type        = bool
  default     = false
}
