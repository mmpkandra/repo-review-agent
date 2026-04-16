# Cost Estimation

Costs depend on which AI provider you use and the size of the repository being analyzed.

## OpenAI (GPT-4.1-mini)

| Repo Size | Approx. Files | Estimated Cost |
|-----------|---------------|----------------|
| Small | ~100 | ~$0.02 |
| Medium | ~500 | ~$0.05 |
| Large | ~1,000 | ~$0.08 |
| Very Large | ~5,000 | ~$0.15 |

## AWS Bedrock (Claude Sonnet)

Bedrock pricing varies by model. With **Claude Sonnet**:

- Input: ~$0.003 per 1K tokens
- Output: ~$0.015 per 1K tokens
- Typical repo (~500 files): ~$0.10–0.20

!!! tip
    Use `--all-docs` sparingly on very large repos — it generates all 9 document types and increases token consumption. Without `--all-docs`, only relevant documents are generated based on detected content.
