# AWS Bedrock Integration

RunBook-AI supports AWS Bedrock with multiple authentication methods. **AWS SSO is recommended** for enterprise use.

## Authentication Options

=== "AWS SSO (Recommended)"

    ```bash
    # Step 1: Login via AWS SSO
    aws sso login --profile your-sso-profile

    # Step 2: Run with the SSO profile
    repo-intel /path/to/repo --use-ai --provider bedrock \
      --aws-profile your-sso-profile \
      --aws-region us-east-1 \
      --model claude-3.7-sonnet

    # Or set as environment variables
    export AWS_PROFILE=your-sso-profile
    export AWS_REGION=us-east-1
    repo-intel /path/to/repo --use-ai --provider bedrock --model claude-3.7-sonnet
    ```

=== "AWS CLI Profile"

    ```bash
    repo-intel /path/to/repo --use-ai --provider bedrock \
      --aws-profile my-profile \
      --aws-region us-east-1 \
      --model claude-3.7-sonnet
    ```

=== "IAM Role (CI/CD)"

    ```bash
    repo-intel /path/to/repo --use-ai --provider bedrock \
      --aws-role-arn arn:aws:iam::123456789:role/BedrockAccessRole \
      --aws-region us-east-1 \
      --model claude-3.7-sonnet
    ```

=== "Instance Profile (EC2/ECS)"

    ```bash
    # Automatic — ensure the instance/task role has Bedrock permissions
    repo-intel /path/to/repo --use-ai --provider bedrock --aws-region us-east-1
    ```

=== "Environment Variables"

    ```bash
    export AWS_ACCESS_KEY_ID=AKIA...
    export AWS_SECRET_ACCESS_KEY=...
    export AWS_REGION=us-east-1
    repo-intel /path/to/repo --use-ai --provider bedrock --model claude-3.7-sonnet
    ```

## Supported Models

| Alias | Full Model ID | Notes |
|-------|---------------|-------|
| `claude-3.7-sonnet` | `anthropic.claude-3-7-sonnet-20250219-v1:0` | **Recommended** — best balance of quality/speed |
| `claude-3.5-haiku` | `anthropic.claude-3-5-haiku-20241022-v1:0` | Fast, cost-effective |
| `claude-3-sonnet` | `anthropic.claude-3-sonnet-20240229-v1:0` | Stable, legacy |
| `claude-3-haiku` | `anthropic.claude-3-haiku-20240307-v1:0` | Fastest, legacy |
| `claude-sonnet` | `us.anthropic.claude-sonnet-4-5-*` | Claude 4.5 Sonnet (cross-region) |
| `claude-haiku` | `us.anthropic.claude-haiku-4-5-*` | Claude 4.5 Haiku (cross-region) |
| `claude-opus` | `us.anthropic.claude-opus-4-5-*` | Claude 4.5 Opus (cross-region) |
| `claude-4-sonnet` | `anthropic.claude-sonnet-4-5-*` | Claude 4.5 Sonnet (direct) |
| `claude-4-haiku` | `anthropic.claude-haiku-4-5-*` | Claude 4.5 Haiku (direct) |
| `titan-text` | `amazon.titan-text-premier-v1:0` | Amazon native |
| `llama3-70b` | `meta.llama3-70b-instruct-v1:0` | Open source |
| `mistral-large` | `mistral.mistral-large-2402-v1:0` | European |

!!! tip
    Use `claude-3.7-sonnet` for best results. Claude 4.x models with the `us.` prefix use cross-region inference profiles.

## Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```
