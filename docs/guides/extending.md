# Extending RunBook-AI

## Adding New Document Types

1. Add the document type to `_infer_doc_needs()` in `analyzer.py`
2. Add a template method to `docgen.py`
3. Add a document-specific prompt to `DOC_PROMPTS` in `llm.py`

## Adding New Compliance Patterns

Add entries to the appropriate dictionary in `compliance_scanner.py`:

```python
CRITICAL_PATTERNS = {
    "my_api_key": (
        r"my_service_key\s*=\s*['\"][A-Za-z0-9]{32,}['\"]",
        "My Service API key",
        "api_key",
        "Rotate the key and store it in a secrets manager."
    ),
    ...
}
```

Available severity levels: `CRITICAL_PATTERNS`, `HIGH_PATTERNS`, `MEDIUM_PATTERNS`, `LOW_PATTERNS`.

## Creating a Custom GPT

You can use RunBook-AI's output to build a Custom GPT that answers questions about any repository.

### Steps

1. **Generate documentation** for your target repository:

    ```bash
    repo-intel /path/to/repo --output-docs ./docs --use-ai --json > repo-profile.json
    ```

2. **Go to ChatGPT** → Explore GPTs → Create

3. **Configure the GPT**:
    - **Name**: `RepoName Expert Assistant`
    - **Description**: Expert assistant for the RepoName codebase
    - **Instructions**: Reference the documentation as your knowledge base

4. **Upload Knowledge Files**: all generated `.md` files and `repo-profile.json`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request
