from app.services.pipeline import PipelineService
from fastapi.testclient import TestClient

from app.main import app


def test_bid_b_reuses_memory_when_running_both() -> None:
    service = PipelineService()

    response = service.run_demo("both")

    assert len(response.runs) == 2
    bid_a, bid_b = response.runs

    assert bid_a.bid_id == "BID-A-001"
    assert bid_a.metrics.memory_reused_items == 0
    assert bid_a.metrics.fresh_matches == 18

    assert bid_b.bid_id == "BID-B-002"
    assert bid_b.memory_hit.found is True
    assert bid_b.metrics.memory_reused_items > 0
    assert bid_b.metrics.simulated_steps_saved > 0


def test_unknown_bid_raises_value_error() -> None:
    service = PipelineService()

    try:
        service.run_demo("missing")
    except ValueError as exc:
        assert "Unknown demo bid" in str(exc)
    else:
        raise AssertionError("Expected unknown bid to raise ValueError")


def test_run_demo_endpoint_supports_both() -> None:
    client = TestClient(app)

    response = client.post("/pipeline/run-demo/both")

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_bid_id"] == "both"
    assert [run["bid_id"] for run in payload["runs"]] == ["BID-A-001", "BID-B-002"]
    assert payload["runs"][1]["metrics"]["memory_reused_items"] > 0
