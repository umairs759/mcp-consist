# MCP-Consist Datasheet

## Motivation

MCP-Consist was developed to address the need for automated consistency checking in multi-context scenarios, such as RAG systems, multi-document verification, and LLM output validation.

## Composition

### Training Data

- Ablation study: 1,500 paired text examples with consistency labels (ALLOW/WARN/BLOCK/ERROR)
- Adaptive holdout: 2,000 additional examples with varied topics and styles

### Input Format

- Two text strings (input1, input2) along with a similarity threshold (0.0 - 1.0)
- Output: Consistency badge (ALLOW/WARN/BLOCK/ERROR) with colored pill styling

### Intended Use

- Research assistants can quickly verify consistency between document pairs
- LLM developers can evaluate output reliability against a similarity threshold
- Content moderators can flag potentially conflicting information

### Training Procedure

The consistency check uses a simple overlap-based metric between the two input texts,
complemented by a configurable threshold to control the strictness of consistency evaluation.

### Evaluation Protocols

- **Ablation**: In-domain evaluation with 1,500 examples
- **Adaptive Holdout**: Out-of-domain evaluation with 2,000 examples

### Ethical Considerations

- The tool should not be used as the sole decision mechanism for high-stakes evaluations
- Results should be interpreted with awareness of the limitations of text overlap metrics
- Bias can be introduced if the threshold is not appropriately calibrated for the use case

### Limitations

- Overlap-based metrics may not capture semantic equivalence in all cases
- Very short or very long texts may produce less reliable consistency scores
- The tool does not account for context, tone, or intent beyond surface-level text comparison