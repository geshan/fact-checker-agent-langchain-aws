# Provision AWS Bedrock AgentCore Infrastructure with Terraform

We will manage all AWS resources—including the AgentCore Gateway, the Web Search Gateway Target (`connectorId: "web-search"`), ECR repository, AgentCore Runtime, Runtime Endpoint, and least-privilege IAM roles—using Terraform (`infra/`). This ensures reproducible, auditable infrastructure lifecycle management (`terraform apply` / `terraform destroy`) rather than imperative CLI scripts or manual console clicks, which is critical since AgentCore Gateways and Runtime endpoints incur billable resource usage.
