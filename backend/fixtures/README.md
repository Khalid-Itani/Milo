Representative synthetic JSON for the existing Swift decoders and additive scan/proposal APIs.
These examples were authored for contract review; they are not claimed as captured live responses.
All database IDs remain integers. UUIDs are only request, conversation, scan-client and proposal
correlation identifiers. The token in visualize-session.json is a placeholder.
The independent files are examples, not a single consistent database snapshot.
The complete set is checked against actual runtime OpenAPI and Pydantic response models
by tests/test_contract.py; legacy card data fields are checked against the Swift models.
