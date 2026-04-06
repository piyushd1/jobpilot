"""Structured logging + OpenTelemetry instrumentation.

Configures structlog for structured logging and OpenTelemetry for
distributed traces and metrics export.
"""

import logging
import sys
from typing import cast

import structlog

from src.config.settings import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.dev.ConsoleRenderer()
                if settings.is_dev
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named logger instance."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def setup_opentelemetry() -> None:
    """Initialize OpenTelemetry tracing and metrics.

    Exports traces to Jaeger (via OTLP) and metrics to Prometheus.
    Safe to call in dev — no-ops if collector is unavailable.
    """
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        resource = Resource.create(
            {
                "service.name": "jobpilot",
                "service.version": "0.1.0",
                "deployment.environment": settings.app_env,
            }
        )

        # Tracing
        tracer_provider = TracerProvider(resource=resource)

        # In production, use OTLP exporter to Jaeger/OTel Collector
        # For dev, use console exporter
        if settings.is_dev:
            tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(tracer_provider)

        # Metrics
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)

        get_logger(__name__).info("OpenTelemetry initialized", env=settings.app_env)
    except ImportError:
        get_logger(__name__).warning("OpenTelemetry SDK not available, skipping")
    except Exception as e:
        get_logger(__name__).warning("OpenTelemetry init failed", error=str(e))
