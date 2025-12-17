# FinanceBench_RAG

## Overview
FinanceBench_RAG is an experimental retrieval-augmented generation (RAG) system built to answer questions from the public evaluation subset of [**FinanceBench**](https://arxiv.org/pdf/2311.11944), a 2024 benchmark for open-book financial question answering over long regulatory documents.

FinanceBench evaluates whether large language models can answer clear-cut, expert-written financial questions grounded in real filings such as 10-Ks, 10-Qs, 8-Ks, and earnings materials. Prior work shows that even state-of-the-art models with retrieval struggle on this benchmark, and that brute-force long-context prompting is impractical due to latency and scalability constraints.

This project focuses on building a retrieval pipeline capable of identifying the correct supporting pages for FinanceBench questions and measuring how retrieval quality affects downstream answer generation. On the 150 publicly available evaluation questions, the system achieves **~70% exact page retrieval at low retrieval depth (top_k = 5)**. When the gold pages are provided, strong models (e.g., Gemini-2.5-Pro) are able to answer most questions correctly using zero-shot prompting, indicating that retrieval is the primary bottleneck, not reasoning.

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
4. Retrieval is performed over **page-level document summaries**.
5. The **full page contents** of retrieved documents are passed to a generator LLM.
6. The generator produces an answer and explicitly references the pages it used.

---

## Retrieval Design Choices
Key retrieval decisions in this system:

- **Page-level retrieval**: Documents are indexed by page rather than by structural or heading-based chunks. Structural chunking produced ~36K chunks on this corpus, while page-level indexing reduces the search space to ~12K chunks.
- **Summary-based embeddings**: Each page is represented by a cleaned summary for retrieval; summaries are used for both BM25 and dense embedding search but are never passed to the generator.
- **Single rewritten query**: Multi-query expansion was intentionally avoided in favor of a single, normalized query to limit noise and improve precision at low retrieval depth.
- **Hybrid signals**: Sparse (BM25) and dense embedding retrieval are both used, with document-level deduplication applied after retrieval.
- **Metadata filters**: Company and year constraints are applied early to reduce the search space before ranking.

These choices prioritize precision at low retrieval depth. On the 150 public FinanceBench questions, the system retrieves the exact supporting page approximately 70% of the time. This substantially exceeds the effectiveness of shared vector-store RAG setups reported in the FinanceBench paper, which achieved only ~19% answer accuracy on the same public question set, suggesting that retrieval quality is a dominant limiting factor

Given that strong LLMs (e.g., Gemini-2.5-Pro) answer most FinanceBench questions correctly when provided with the gold supporting pages, these results suggest that improving retrieval—rather than model reasoning—is the primary driver of end-to-end performance gains.

---

## Evaluation & Known Limits

Evaluation is performed on the 150 public FinanceBench queries with a focus on retrieval metrics:

- Recall
- Precision
- Exact page retrieval

Two operating regimes highlight the core tradeoff:

- **Low retrieval depth (top_k = 5)**  
  - Exact page retrieval: ~71%  
  - Recall: ~72%  
  - Precision: ~16%  
  - Average retrieved pages: ~9  

  This regime prioritizes precision and yields a compact evidence set suitable for downstream reasoning.

- **High retrieval depth (top_k = 75)**  
  - Exact page retrieval: ~98%  
  - Recall: ~98%  
  - Precision: ~3%  
  - Average retrieved pages: ~108  

  While recall approaches saturation, precision collapses and the resulting context size becomes impractical for generation.

Observed behavior:

- Precision improves substantially at low retrieval depth but declines rapidly as top_k increases.
- Near-perfect recall requires retrieving 100+ pages, introducing excessive noise.
- Cross-encoder and LLM-based rerankers were explored but did not reliably recover precision at large candidate set sizes in this setup.
- Brute-force increases in retrieval depth are not viable for downstream reasoning under realistic latency and context constraints.

These results reinforce retrieval precision - not recall saturation - as the primary bottleneck for effective financial QA on FinanceBench.

---

## Notes

Due to size constraints, raw FinanceBench documents and vector indexes are not included in this repository.  
The system assumes preprocessed page-level documents and a corresponding vector index, as described above.  
This project is intended for research and experimentation, not as a plug-and-play setup.

If you are interested in running the system end-to-end or discussing the data preparation process, feel free to reach out.
