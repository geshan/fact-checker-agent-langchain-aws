data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

# -----------------------------------------------------------------------------
# 1. ECR Repository for AgentCore Runtime ARM64 Container
# -----------------------------------------------------------------------------
resource "aws_ecr_repository" "agent" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# -----------------------------------------------------------------------------
# 1b. Amazon Bedrock Model Access Use-Case Submission
# -----------------------------------------------------------------------------
resource "aws_bedrock_use_case_for_model_access" "this" {
  form_data = jsonencode({
    companyName         = "FactCheckerDev"
    companyWebsite      = "https://example.com"
    intendedUsers       = "0"
    industryOption      = "Technology"
    otherIndustryOption = ""
    useCases            = "Fact-checking claims against live public web search results."
  })
}


# -----------------------------------------------------------------------------
# 2. AgentCore Gateway Outbound IAM Role + Web Search Target
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "gateway_trust" {
  statement {
    sid     = "AllowBedrockAgentCoreGatewayAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock-agentcore:${var.aws_region}:${local.account_id}:gateway/*"]
    }
  }
}

resource "aws_iam_role" "gateway" {
  name               = "${var.project_name}-gateway-role"
  assume_role_policy = data.aws_iam_policy_document.gateway_trust.json
}

data "aws_iam_policy_document" "gateway_outbound" {
  statement {
    sid       = "InvokeGateway"
    effect    = "Allow"
    actions   = ["bedrock-agentcore:InvokeGateway"]
    resources = ["arn:aws:bedrock-agentcore:${var.aws_region}:${local.account_id}:gateway/*"]
  }

  statement {
    sid       = "InvokeWebSearch"
    effect    = "Allow"
    actions   = ["bedrock-agentcore:InvokeWebSearch"]
    resources = ["arn:aws:bedrock-agentcore:${var.aws_region}:aws:tool/web-search.v1"]
  }
}

resource "aws_iam_role_policy" "gateway_outbound" {
  name   = "${var.project_name}-gateway-web-search-policy"
  role   = aws_iam_role.gateway.id
  policy = data.aws_iam_policy_document.gateway_outbound.json
}

resource "aws_bedrockagentcore_gateway" "this" {
  name            = "${var.project_name}-gw"
  description     = "AgentCore Gateway exposing managed Web Search tool over MCP for LangChain Fact Checker"
  authorizer_type = "AWS_IAM"
  protocol_type   = "MCP"
  role_arn        = aws_iam_role.gateway.arn

  depends_on = [aws_iam_role_policy.gateway_outbound]
}

resource "aws_bedrockagentcore_gateway_target" "web_search" {
  gateway_identifier = aws_bedrockagentcore_gateway.this.gateway_id
  name               = "web-search-tool"
  description        = "Managed Amazon Bedrock AgentCore Web Search Tool target"

  target_configuration {
    mcp {
      connector {
        source {
          connector_id = "web-search"
        }
        configuration {
          name             = "WebSearch"
          parameter_values = jsonencode({})
        }
      }
    }
  }

  credential_provider_configuration {
    gateway_iam_role {}
  }
}

# -----------------------------------------------------------------------------
# 3. AgentCore Runtime Execution IAM Role + Runtime & Endpoint
# -----------------------------------------------------------------------------
data "aws_iam_policy_document" "runtime_trust" {
  statement {
    sid     = "AllowBedrockAgentCoreRuntimeAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock-agentcore:${var.aws_region}:${local.account_id}:runtime/*"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name               = "${var.project_name}-runtime-role"
  assume_role_policy = data.aws_iam_policy_document.runtime_trust.json
}

data "aws_iam_policy_document" "runtime_permissions" {
  statement {
    sid    = "BedrockInvokeModel"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = [
      "arn:aws:bedrock:${var.aws_region}:${local.account_id}:inference-profile/${var.bedrock_model_id}",
      "arn:aws:bedrock:*::foundation-model/${var.foundation_model_name}"
    ]
  }

  statement {
    sid       = "InvokeAgentCoreGateway"
    effect    = "Allow"
    actions   = ["bedrock-agentcore:InvokeGateway"]
    resources = [aws_bedrockagentcore_gateway.this.gateway_arn]
  }

  statement {
    sid       = "ECRGetAuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "ECRPullAgentImage"
    effect = "Allow"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchCheckLayerAvailability"
    ]
    resources = [aws_ecr_repository.agent.arn]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
    ]
  }
}

resource "aws_iam_role_policy" "runtime_permissions" {
  name   = "${var.project_name}-runtime-policy"
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.runtime_permissions.json
}

resource "aws_bedrockagentcore_agent_runtime" "agent" {
  count              = var.deploy_runtime ? 1 : 0
  agent_runtime_name = var.runtime_name
  description        = "LangChain Fact Checker Agent running on Amazon Bedrock AgentCore Runtime"
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agent.repository_url}:${var.image_tag}"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  protocol_configuration {
    server_protocol = "HTTP"
  }

  environment_variables = {
    AGENTCORE_GATEWAY_URL = aws_bedrockagentcore_gateway.this.gateway_url
    BEDROCK_MODEL_ID      = var.bedrock_model_id
    AWS_REGION            = var.aws_region
  }

  depends_on = [
    aws_iam_role_policy.runtime_permissions,
    aws_bedrockagentcore_gateway_target.web_search
  ]
}

resource "aws_bedrockagentcore_agent_runtime_endpoint" "agent" {
  count            = var.deploy_runtime ? 1 : 0
  agent_runtime_id = aws_bedrockagentcore_agent_runtime.agent[0].agent_runtime_id
  name             = "${var.runtime_name}_endpoint"
  description      = "HTTP endpoint for LangChain Fact Checker AgentCore Runtime"
}
