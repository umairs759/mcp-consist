# MCP-Consist Datasheet

## Motivation

MCP-Consist was developed to address the need for automated consistency checking in multi-context scenarios, such as RAG systems, multi-document verification, and LLM output validation.

## Composition

### Training Data

MCP-CONSIST Stage 1 is a **lexical rule**, not a trained model. There is no training dataset, no training pipeline, and no learned weights. The detector is a deterministic function of the two inputs:

```
overlap = len(set1 & set2) / max(len(set1), len(set2))
```

## Input Format

- Two text strings (input1, input2) along with a consistency threshold (0.0 - 1.0)
- Output: Consistency badge (ALLOW/WARN/BLOCK/ERROR) with colored pill styling

## Intended Use

- Research assistants can quickly verify consistency between document pairs
- LLM developers can evaluate output reliability against a similarity threshold
- Content moderators can flag potentially conflicting information

## Training Procedure

There is no training procedure. Consistency is computed by a simple overlap-based
metric between the two input texts, complemented by a configurable threshold to
control the strictness of the consistency evaluation. The identical-token-set
prototype rule (BLOCK) is applied regardless of threshold (see Limitations).

## Evaluation Protocols

There are no reproducible evaluation protocols, datasets, or claimed performance
figures in Stage 1. The repository previously carried
`results/ablation_results.json` and `results/adaptive_holdout.json` containing
hand-written constants (e.g. accuracy 0.94 / 0.93, F1 0.915 / 0.905). These
could not be reproduced from any code in the repository and are treated as
**unverified, from earlier experiments / placeholder**. They are kept, clearly
labelled, under `results/_unverified/` and are **not** cited as achieved
performance.

## Stage 2 dataset

`data/eval_cases.jsonl`: 101 synthetic cases, dev 54 / holdout 47, 12 attack
families. Each case has case_id, description, schema, policy, task, call,
expected_verdict, attack_family, explanation, split. Provenance: synthetic,
authored by project author. Not MCPTox or any external dataset.

`data/scenarios.json`: 10 UI scenarios with expected_verdict metadata.

## Ethical Considerations

- The tool should not be used as the sole decision mechanism for high-stakes evaluations
- Results should be interpreted with awareness of the limitations of text overlap metrics
- ALLOW is explicitly not proof that content is safe; BLOCK does not intercept a call
- Bias can be introduced if the threshold is not appropriately calibrated for the use case

## Limitations

- Overlap-based metrics may not capture semantic equivalence in all cases
- Very short or very long texts may produce less reliable consistency scores
- The tool does not account for context, tone, or intent beyond surface-level text comparison
- No semantics, negation handling, schema validation, policy enforcement, or ML
- See `docs/LIMITATIONS.md` for the full list
