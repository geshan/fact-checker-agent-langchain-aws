# Use AWS IAM (SigV4) for AgentCore Gateway and Runtime Authentication

Both the AgentCore Gateway (`authorizerType: AWS_IAM`) and the AgentCore Runtime will use AWS IAM (SigV4) authentication rather than OAuth/JWT (Cognito). Since the Fact Checker agent runs inside AgentCore Runtime with an execution IAM role and has no per-user downstream token-exchange requirements, SigV4 eliminates the operational overhead and attack surface of managing a Cognito User Pool, OAuth clients, and bearer tokens.
