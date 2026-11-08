"""Progress contract and real HTTP streaming tests; no model or index access."""
import ast
import importlib.util
import json
import socket
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    "Planning the search\u2026", "Searching the filings\u2026",
    "Reviewing 1 candidate page\u2026", "Writing your answer\u2026",
]
RESULT = {"answer": "A test answer.", "documents": [{"page_content": "Overview", "metadata": {"plain_text": "Evidence"}}]}


def load_pipeline():
    # Isolate orchestration from module-level model/index initialization.
    node = next(node for node in ast.parse((ROOT / "backend/rag/search.py").read_text(encoding="utf-8")).body
                if isinstance(node, ast.FunctionDef) and node.name == "pipeline")
    node.decorator_list = []
    page = types.SimpleNamespace(metadata={"company": "adobe", "fiscal_year": 2022, "document_type": "10k", "page_in_pdf": 67}, page_content="Overview")
    namespace = {
        "trace": MagicMock(),
        "get_year_window": MagicMock(return_value=[2022]),
        "resolve_company": MagicMock(return_value="adobe"),
        "query_decomposer": MagicMock(return_value=types.SimpleNamespace(queries=["query"])),
        "retrieve_queries": MagicMock(return_value=[page]),
        "context_judge": MagicMock(return_value=types.SimpleNamespace(pages=[types.SimpleNamespace(page_index=0, is_useful=True, analysis="Supplies the requested revenue comparison.")], required_data_points=["Revenue for both years"], is_context_enough=True, sufficiency_reason="Both years are covered.", missing_information=None)),
        "generator": MagicMock(return_value=types.SimpleNamespace(reasoning="Evidence", answer="Answer", indexes=[0])),
        "LLMFailure": type("LLMFailure", (Exception,), {}),
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), "search.py", "exec"), namespace)
    return namespace


def load_server():
    package = types.ModuleType("rag")
    package.__path__ = []
    stub = types.ModuleType("rag.search")
    stub.pipeline = lambda query: RESULT
    spec = importlib.util.spec_from_file_location("progress_test_server", ROOT / "backend/server.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"rag": package, "rag.search": stub, spec.name: module}):
        spec.loader.exec_module(module)
    return module


def read_events(response):
    for line in response.iter_lines():
        if line.startswith("data: "):
            yield json.loads(line[6:])


class PipelineTests(unittest.TestCase):
    def test_notifications_precede_the_actual_stages(self):
        ns = load_pipeline()
        events = []
        for label, stage in zip(STAGES, ["query_decomposer", "retrieve_queries", "context_judge", "generator"]):
            original = ns[stage].return_value
            ns[stage].side_effect = lambda *args, name=stage, value=original, **kwargs: (events.append(name), value)[1]
        updates = []
        def progress(update):
            updates.append(update)
            events.append(update["message"])
        result = ns["pipeline"]("Question", progress)
        self.assertEqual(events, [item for pair in zip(STAGES, ["query_decomposer", "retrieve_queries", "context_judge", "generator"]) for item in pair])
        self.assertEqual(result["documents"][0]["page_content"], "Overview")
        self.assertEqual(updates[0]["company"], "adobe")
        self.assertEqual(updates[0]["years"], [2022])
        self.assertEqual(updates[1]["query_count"], 1)
        self.assertEqual(updates[3]["selected_count"], 1)

    def test_progress_is_optional_and_failure_stops_later_stages(self):
        ns = load_pipeline()
        self.assertIn("answer", ns["pipeline"]("Question"))
        ns = load_pipeline()
        ns["context_judge"].side_effect = ns["LLMFailure"]("429")
        stages = []
        result = ns["pipeline"]("Question", lambda update: stages.append(update["message"]))
        self.assertEqual(stages, STAGES[:3])
        self.assertIn("request limit", result["answer"])
        ns["generator"].assert_not_called()


    def test_report_contains_selected_analysis_only_and_maps_citations_to_retrieved_pages(self):
        ns = load_pipeline()
        ns["retrieve_queries"].return_value = [
            types.SimpleNamespace(metadata={
                "company": "adobe", "fiscal_year": year, "document_type": "10k",
                "page_in_pdf": 67, "document_name": "PRIVATE_FILENAME",
                "plain_text": "PRIVATE_BODY", "xml_text": "PRIVATE_XML"
            }, page_content="Overview") for year in [2020, 2021, 2022, 2023]
        ]
        audits = [types.SimpleNamespace(page_index=i, is_useful=i != 1,
                  analysis="EXCLUDED_ANALYSIS" if i == 1 else "Selected analysis " + str(i),
                  evidence=["PRIVATE_SNIPPET"]) for i in range(4)]
        ns["context_judge"].return_value.pages = audits
        ns["generator"].return_value.indexes = [2, 0]
        result = ns["pipeline"]("Question")
        report = result["research"]
        self.assertEqual((report["retrieved_count"], report["selected_count"], report["cited_count"]), (4, 3, 2))
        self.assertEqual([page["metadata"]["fiscal_year"] for page in report["pages"]], [2020, 2022, 2023])
        self.assertEqual([page["is_cited"] for page in report["pages"]], [True, False, True])
        self.assertEqual([doc["metadata"]["fiscal_year"] for doc in result["documents"]], [2023, 2020])
        serialized = json.dumps(report)
        for hidden in ["EXCLUDED_ANALYSIS", "PRIVATE_SNIPPET", "PRIVATE_BODY", "PRIVATE_XML", "PRIVATE_FILENAME"]:
            self.assertNotIn(hidden, serialized)

    def test_empty_context_retains_the_missing_information_assessment(self):
        ns = load_pipeline()
        ns["retrieve_queries"].return_value = []
        judgment = ns["context_judge"].return_value
        judgment.pages = []
        judgment.is_context_enough = False
        judgment.sufficiency_reason = "No source pages were retrieved."
        judgment.missing_information = "Revenue figures for both years."
        ns["generator"].return_value.indexes = []
        result = ns["pipeline"]("Question")
        self.assertEqual(result["research"]["pages"], [])
        self.assertEqual(result["research"]["selected_count"], 0)
        self.assertEqual(result["research"]["missing_information"], "Revenue figures for both years.")


class HTTPStreamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_server()
        cls.sock = socket.socket()
        cls.sock.bind(("127.0.0.1", 0))
        cls.url = "http://127.0.0.1:" + str(cls.sock.getsockname()[1])
        cls.server = uvicorn.Server(uvicorn.Config(cls.module.app, log_level="error", lifespan="off"))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={"sockets": [cls.sock]}, daemon=True)
        cls.thread.start()
        deadline = time.monotonic() + 5
        while not cls.server.started and time.monotonic() < deadline:
            time.sleep(.01)
        assert cls.server.started

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(5)
        cls.sock.close()

    def test_status_arrives_before_pipeline_finishes_and_result_is_preserved(self):
        release, finished = threading.Event(), threading.Event()

        def pipeline(query, on_progress=None):
            on_progress(STAGES[0])
            if not release.wait(5):
                raise RuntimeError("Test did not release pipeline")
            for stage in STAGES[1:]:
                on_progress(stage)
            finished.set()
            return RESULT

        self.module.pipeline = pipeline
        try:
            with httpx.stream("POST", self.url + "/ask/stream", json={"question": "Question"}, timeout=6) as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/event-stream", response.headers["content-type"])
                events = read_events(response)
                first = next(events)
                self.assertEqual(first, {"type": "status", "message": STAGES[0]})
                self.assertFalse(finished.is_set(), "Progress was buffered until completion")
                release.set()
                remaining = list(events)
                self.assertEqual([event["message"] for event in remaining[:-1]], STAGES[1:])
                self.assertEqual(remaining[-1], {"type": "result", "data": RESULT})
        finally:
            release.set()


    def test_structured_progress_and_research_report_are_forwarded(self):
        update = {"message": STAGES[0], "company": "adobe", "years": [2021, 2022, 2023]}
        report = {"pages": [], "queries": ["Revenue comparison"], "retrieved_count": 0}
        def pipeline(query, on_progress=None):
            on_progress(update)
            return {**RESULT, "research": report}
        self.module.pipeline = pipeline
        with httpx.stream("POST", self.url + "/ask/stream", json={"question": "Question"}) as response:
            events = list(read_events(response))
        self.assertEqual(events[0], {**update, "type": "status"})
        self.assertEqual(events[-1]["data"]["research"], report)

    def test_existing_json_route_is_compatible(self):
        self.module.pipeline = lambda query: {**RESULT, "error": "not exposed"}
        response = httpx.post(self.url + "/ask", json={"question": "Question"})
        self.assertEqual(response.json(), RESULT)

    def test_friendly_and_unexpected_errors_are_terminal_events(self):
        self.module.pipeline = lambda query, on_progress=None: {"answer": "Provider limit reached.", "documents": [], "error": "private provider detail"}
        with httpx.stream("POST", self.url + "/ask/stream", json={"question": "Question"}) as response:
            self.assertEqual(list(read_events(response)), [{"type": "error", "message": "Provider limit reached."}])
        def fail(*args, **kwargs):
            raise RuntimeError("private provider detail")
        self.module.pipeline = fail
        with patch("logging.exception"):
            with httpx.stream("POST", self.url + "/ask/stream", json={"question": "Question"}) as response:
                events = list(read_events(response))
        self.assertEqual(events, [{"type": "error", "message": "Research failed. Please try again."}])

    def test_disconnect_stops_the_pipeline_at_its_next_progress_boundary(self):
        release, cancelled = threading.Event(), threading.Event()
        def pipeline(query, on_progress=None):
            on_progress(STAGES[0])
            release.wait(5)
            try:
                on_progress(STAGES[1])
            except InterruptedError:
                cancelled.set()
                raise
            return RESULT
        self.module.pipeline = pipeline
        try:
            with httpx.stream("POST", self.url + "/ask/stream", json={"question": "Question"}) as response:
                self.assertEqual(next(read_events(response))["message"], STAGES[0])
            time.sleep(.1)
            release.set()
            self.assertTrue(cancelled.wait(3))
        finally:
            release.set()


if __name__ == "__main__":
    unittest.main(verbosity=2)
