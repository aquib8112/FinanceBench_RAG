# FinanceBench_RAG

Explore the system through the [live demo](https://aquib8112.github.io/FinanceBench_RAG/).

## Overview

FinanceBench_RAG answers financial questions using evidence from company filings, including annual reports, quarterly reports, and earnings releases. It combines document search with language models to find relevant pages, check the evidence, and produce answers with supporting calculations and citations.

The system achieves **87.3% end-to-end answer accuracy (131/150)** on the public [FinanceBench](https://github.com/patronus-ai/financebench) evaluation questions. It retrieves relevant pages rather than sending entire filings to the answering model.

This is a research and engineering project, with a web interface for exploring answers and their sources.

## How It Works

1. **Identify the company and years** to narrow the search.
2. **Plan the evidence searches.** A language model breaks the question into focused queries, usually one or two, covering the facts needed to answer it.
3. **Retrieve candidate pages** using keyword and semantic search over page summaries, then merge results and remove duplicate pages.
4. **Review the evidence.** A language model checks each page's usefulness, whether the pages collectively support an answer, and what information is missing.
5. **Generate an answer from the original pages**, with calculations and citations to the sources used. When essential evidence is missing, the model is instructed to explain the limitation and abstain.

LangSmith traces the pipeline for debugging and evaluation. The web interface shows search progress, evidence assessments, and cited sources.

## Design Choices

- **Pages as evidence units:** The corpus contains 11,954 page chunks from 84 documents. Tables stay with their surrounding text, headings, units, and footnotes so the answering model can interpret them together.
- **Summaries for search, original content for answers:** Search uses concise page summaries; evidence review and answer generation use the original structured page content.
- **Hybrid retrieval:** Qdrant combines BM25 keyword search with Gemini Embedding 2 semantic search. Company and year filters narrow the search before ranking.
- **Evidence review before generation:** The judge retains useful pages even when the full answer is not yet supported. Those pages still reach the answering model; the pipeline does not automatically search again for missing evidence.

## Results and Limitations

The saved [evaluation results](results/final_run.json) record **87.3% end-to-end answer accuracy (131/150)** on the [public question set](results/page_eval.csv), with 19 uncredited answers. [Detailed outputs](results/detailed_final_run.json) include search queries, retrieved pages, evidence assessments, and citations.

Used agents to find **question-compliant alternative evidence for 78 FinanceBench questions**, identifying **218 additional page references** beyond FinanceBench's [gold evidence](results/gold_page_id_eval.json). The [expanded evidence catalogue](results/compliant_evidence_eval.json) also records combinations of pages assessed as sufficient to answer a question. This audit supports retrieval evaluation and is separate from the live answering pipeline.

A separate manual review, informed by the [FinanceBench paper's evaluation guidelines](https://arxiv.org/abs/2311.11944), accepts seven additional, source-supported answers that differ from the reference answers, bringing the reviewed score to **138/150 (92.0%)**. These involve differences in financial definitions, reporting periods, or source restrictions. This is a manual reassessment of the same saved answers, not a new run or official benchmark adjudication; **87.3% remains the primary reported result**.

Remaining challenges include unnecessary abstentions, fiscal-year interpretation, incomplete evidence, and reasoning errors despite relevant sources. Three questions omit the company name and remain uncredited in the full 150-question denominator. Results cover this public subset; broader generalization has not been established.

## Running the Project

See the [data preparation guide](data_processing/README.md) for extraction, page construction, summaries, and downloadable data and indexes. Raw filings and vector indexes are not bundled with the repository.

Extract the Gemini Embedding 2 index into `backend/data/qdrant_db/`, with `meta.json` directly inside it. Copy `backend/.env.example` to `backend/.env` and configure Google, OpenRouter, and LangSmith keys. Query embeddings require `gemini-embedding-2` with 3,072 dimensions; the older Embedding 001 index is incompatible. From `backend`, start the API with `python -m uvicorn server:app --reload` using your project environment.
