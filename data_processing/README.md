# FinanceBench data pipeline

**PDFs → Docling JSON → page chunks → retrieval summaries → hybrid index.**

Start at any stage using the Kaggle downloads below. Use Python 3.10+ and keep
dependencies in your project environment. Keep downloaded data outside the code
folder; all input and output paths are supplied by you.

## 1. Extract PDFs

[Download the 84 source documents](https://www.kaggle.com/datasets/aquibahmad7/financebench-clean/data?select=docneeded)
used for the 150 FinanceBench questions.

In [docling_processing.py](docling_processing.py), fill in `PDF_PATHS` and
`OUTPUT_DIR`, then run the script or paste it into a notebook cell. It requires
Docling and defaults to CPU with four threads; select CUDA for a supported GPU.

Save the resulting JSON files in a folder of your choice. Use that folder as
`--docling-dir` in the next step.

## 2. Build page chunks

[Download the processed Docling documents](https://www.kaggle.com/datasets/aquibahmad7/financebench-clean/data?select=docling_processed_documnets)
to skip extraction. Save the JSON files in a folder of your choice.

From the `FinanceBench_RAG` repository root:

```powershell
# Replace the quoted placeholders with your actual paths.
python -B -m data_processing --all-documents --docling-dir "YOUR_DOCLING_JSON_FOLDER" --output "YOUR_OUTPUT_FOLDER/chunks.json"
```

Paths can be absolute or relative to the directory you run the command from.
`--docling-dir` and `--output` are required. The audit is saved alongside the
output as `chunks.audit.json`; use `--audit-output` to choose another location.
For a subset, replace `--all-documents` with
`--documents WALMART_2020_10K NETFLIX_2017_10K`; those two are also the default
without a selection flag. Builds replace their outputs, so choose different
paths to preserve a summarized corpus.

The builder needs only the Python standard library. Document names encode
company, year, quarter and type, such as `3M_2023Q2_10Q`. Each document needs
an entry in [fiscal_date_catalog.json](fiscal_date_catalog.json). Fiscal dates
represent reporting periods, not event dates; the six dated 8-Ks have null
fiscal dates and quarters.

Important chunking decisions:

- **Physical pages:** one chunk per substantive page, preserving original
  numbering. Construction rules apply uniformly across the corpus.
- **Identity:** `page_id` identifies the document and page; `uid` also includes
  the first 16 hexadecimal characters of SHA-256 over exact `plain_text`.
  Identical text on different pages stays distinct.
- **Evidence stays together:** tables remain with surrounding text, units,
  captions and footnotes. Merged-cell spans are preserved; overlaps are audited.
- **Text and structure:** `plain_text` is readable text; `xml_text` preserves
  headings, lists and tables. Invalid XML characters, footers and exact
  `Table of Contents` labels are removed; index entries and list markers remain.
- **Limits:** generic chart/picture OCR is excluded, but captions, footnotes
  and headings remain. Footer removal can discard useful text.
- **Navigation:** `doc_sections` uses visible SEC indexes and body headings.
  Continuation links need source evidence across adjacent pages. Section/index
  labels can be imperfect; retain a filing-wide fallback.

Chunks also contain document metadata, table IDs/headers/terms, presence flags
and `summary: ""`. Index tables remain inline, outside the ordinary table
catalog. Validation checks page coverage, identifiers, XML, tables and links;
the audit records construction details.

Verified coverage: **84 documents, 11,990 physical pages, 11,954 chunks**.
The 36 omitted pages were 33 empty, two page-number-only and one filing-label-only.

## 3. Add retrieval summaries

[Download the completed corpus with summaries](https://www.kaggle.com/datasets/aquibahmad7/financebench-clean/data?select=final_chunks_v2.json)
to skip rebuilding and summary-generation calls.

Otherwise, set `CHUNKS_FILE` in [chunk_summarizer.py](chunk_summarizer.py) and
implement `llm_call(xml_text, prompt)`, returning `{"summary": "..."}` matching
the included schema. This script requires Pydantic 2.

Summaries inventory page topics for retrieval; original page content supplies
answer evidence. The loop skips existing summaries and saves each success into
the same JSON file through a temporary-file replacement. Failed calls remain
unfinished for another run; saving errors stop processing.

The downloaded corpus retains five older fields (`section`,
`secondary_sections`, `keywords`, `entities`, `financial_metrics`) omitted
by fresh builds, plus older quarter labels for the six dated 8-Ks.

## 4. Build the hybrid index

[Download the prebuilt Gemini Embedding 2 hybrid index](https://www.kaggle.com/datasets/aquibahmad7/financebench-clean/data?select=GEMINI_EMBEDDING_2_3072_HYBRID)
to skip embedding calls.

In [embedder.py](embedder.py), set `CHUNKS_FILE` to a fully summarized corpus,
choose a new `QDRANT_PATH` and set the `OPENROUTER_API_KEY` environment variable.
Dependencies: `requests`, `fastembed`, `qdrant-client`. No GPU is required.

It combines `google/gemini-embedding-2` at **3,072 dimensions** through
OpenRouter's `google-ai-studio` provider with `Qdrant/bm25` over the original
summaries. Dense document inputs use `title: none | text: {summary}`.
Retrieval queries must use `task: search result | query: {question}` with
the same dense model and dimensions.

Batches of 99 are saved to collection `sec_filings`, with vectors `dense` and
`sparse`. Payloads hold the summary as `page_content` and other chunk fields
as `metadata`. Existing output folders are refused; interrupted builds do
not resume automatically. Set `ARCHIVE_PATH` without `.zip` for optional ZIP
export after the database closes.
