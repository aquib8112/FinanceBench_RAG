# FinanceBench_RAG

## Overview
FinanceBench_RAG is an experimental retrieval-augmented generation (RAG) system built to answer questions from the public evaluation subset of [**FinanceBench**](https://arxiv.org/pdf/2311.11944), a 2024 benchmark for open-book financial question answering over long regulatory documents.

FinanceBench evaluates whether large language models can answer clear-cut, expert-written financial questions grounded in real filings such as 10-Ks, 10-Qs, 8-Ks, and earnings materials. Prior work shows that even state-of-the-art models with retrieval struggle on this benchmark, and that brute-force long-context prompting is impractical due to latency and scalability constraints.

On the 150 publicly available FinanceBench evaluation questions, the system achieves ~76% end-to-end answer accuracy. Error analysis shows that missed evidence during retrieval remains the dominant source of failure, while the remaining errors occur primarily on interpretive or multi-step reasoning questions even when relevant pages are retrieved. This confirms that improving retrieval coverage is still the highest-leverage direction for further gains.

This repository represents an ongoing research and engineering effort rather than a production system.

**Relevant resources:**
- FinanceBench paper: https://arxiv.org/pdf/2311.11944
- Original benchmark repository: https://github.com/patronus-ai/financebench

---

## End-to-End Flow
At a high level, the system operates as follows:

1. A user query is received.
2. Company names and a relevant year window are extracted from the query.
3. The query is rewritten into a retrieval-friendly form using an LLM.
4. Hybrid retrieval is performed over **page-level document summaries**.
5. Retrieved pages are passed through an **LLM relevance judge** that removes clearly irrelevant evidence.
6. The **full page contents** of the remaining documents are sent to a generator LLM.
7. The generator produces an answer and explicitly references the pages it used.
8. All stages of the pipeline are traced and logged using : **langsmith** for debugging and evaluation.

---

## Retrieval Design Choices
Key retrieval decisions in this system:

- **Page-level retrieval**: Documents are indexed by page rather than by structural or heading-based chunks. Structural chunking produced ~36K chunks on this corpus, while page-level indexing reduces the search space to ~12K chunks, improving ranking stability, lowering latency, and reducing the chance of retrieving fragmented context.
- **Summary-based embeddings**: Each page is represented by a cleaned semantic summary for retrieval. Raw financial pages contain tables, boilerplate text, and formatting noise that degrade embedding quality; summaries compress the signal into clearer semantic units. Summaries are used for both BM25 and dense search but are never passed to the generator.
- **Single rewritten query**: Multi-query expansion or HYDE was intentionally avoided in favor of a single normalized query to limit noise and improve precision at low retrieval depth.
- **Hybrid signals**: Sparse (BM25) and dense embedding retrieval are both used, with document-level deduplication applied after retrieval.
- **Metadata filters**: Company and year constraints are applied early to reduce the search space before ranking.
- **LLM relevance judge**: Retrieved pages are filtered through an LLM that removes clearly irrelevant evidence before generation, reducing hallucination risk and preventing noisy context from reaching the answer stage.

These design choices prioritize precise evidence retrieval under realistic constraints. On the 150 public FinanceBench evaluation questions, the system achieves ~76% end-to-end answer accuracy, substantially outperforming shared vector-store RAG configurations reported in the FinanceBench paper, which achieve ~19% accuracy on the same subset, and approaching long-context baselines 79% without requiring entire filings in prompt context.

Error analysis indicates that retrieval coverage remains the primary bottleneck in failed cases, while the remaining errors occur mainly on interpretive or multi-step financial questions even when the correct evidence is retrieved. This suggests that improving retrieval quality is the main driver of performance gains, with reasoning limits emerging only after evidence selection succeeds.

---

## Evaluation & Known Limits
Evaluation was conducted on the 150 public FinanceBench questions.

### Overall Outcome
- ~76% answered correctly  
- 36 failures total  

### Failure Breakdown
- **24 / 36 failures** were caused by incorrect evidence retrieval  
- **12 / 36 failures** occurred despite correct evidence being retrieved (reasoning or interpretation errors)  

### Failure Patterns by Question Type
- **Domain-relevant:** 18 failures  
- **Novel generated:** 14 failures  
- **Metrics-generated:** 4 failures  

### Key Takeaway
Most errors stem from missing or noisy retrieval rather than generation quality.  
When the correct evidence is retrieved, the system answers correctly in the majority of cases, with remaining failures concentrated in interpretive or multi-step financial reasoning.

---

## Notes

Due to size constraints, raw FinanceBench documents and vector indexes are not included in this repository.  
The system assumes preprocessed page-level documents and a corresponding vector index, as described above.  
This project is intended for research and experimentation, not as a plug-and-play setup.

If you are interested in running the system end-to-end or discussing the data preparation process, feel free to reach out.
