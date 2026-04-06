"""Application metrics instrumented via OpenTelemetry.

Key metrics per Section 15.1:
  - Campaign duration (histogram)
  - Agent duration by type (histogram)
  - Source success rate by platform (gauge)
  - LLM token consumption (counter)
  - LLM cost (counter)
  - Challenge encounter rate (counter)
  - Error rate by service (counter)
"""

from __future__ import annotations

from src.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from opentelemetry import metrics

    meter = metrics.get_meter("jobpilot", "0.1.0")

    # Histograms
    campaign_duration = meter.create_histogram(
        name="jobpilot_campaign_duration_seconds",
        description="End-to-end campaign execution time",
        unit="s",
    )

    agent_duration = meter.create_histogram(
        name="jobpilot_agent_duration_seconds",
        description="Agent execution time by agent type",
        unit="s",
    )

    # Counters
    llm_tokens_total = meter.create_counter(
        name="jobpilot_llm_tokens_total",
        description="Total LLM tokens consumed",
    )

    llm_cost_total = meter.create_counter(
        name="jobpilot_llm_cost_usd_total",
        description="Total LLM cost in USD",
        unit="usd",
    )

    challenge_encounters = meter.create_counter(
        name="jobpilot_challenge_encounter_total",
        description="Challenge/CAPTCHA encounters by platform",
    )

    error_counter = meter.create_counter(
        name="jobpilot_error_total",
        description="Errors by service and type",
    )

    # Gauges (via UpDownCounter for OTel compatibility)
    source_success_rate = meter.create_up_down_counter(
        name="jobpilot_source_success_rate",
        description="Source retrieval success rate by platform",
    )

    parse_completeness = meter.create_up_down_counter(
        name="jobpilot_parse_completeness_score",
        description="Resume parse completeness score",
    )

    dedup_rate = meter.create_up_down_counter(
        name="jobpilot_dedup_rate",
        description="Deduplication rate per campaign",
    )

    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False
    logger.info("OpenTelemetry metrics not available, using no-op metrics")


def record_campaign_duration(seconds: float, campaign_id: str = "") -> None:
    if _METRICS_AVAILABLE:
        campaign_duration.record(seconds, {"campaign_id": campaign_id})


def record_agent_duration(seconds: float, agent_name: str = "") -> None:
    if _METRICS_AVAILABLE:
        agent_duration.record(seconds, {"agent": agent_name})


def record_llm_tokens(tokens: int, model: str = "", agent: str = "") -> None:
    if _METRICS_AVAILABLE:
        llm_tokens_total.add(tokens, {"model": model, "agent": agent})


def record_llm_cost(cost_usd: float, model: str = "", campaign_id: str = "") -> None:
    if _METRICS_AVAILABLE:
        llm_cost_total.add(cost_usd, {"model": model, "campaign_id": campaign_id})


def record_challenge(platform: str = "") -> None:
    if _METRICS_AVAILABLE:
        challenge_encounters.add(1, {"platform": platform})


def record_error(service: str = "", error_type: str = "") -> None:
    if _METRICS_AVAILABLE:
        error_counter.add(1, {"service": service, "error_type": error_type})
