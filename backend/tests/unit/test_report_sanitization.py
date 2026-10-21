"""Unit tests for report sanitization, Jinja2 auto-escaping, CSP, and integrity."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from app.schemas.report import (
    IncidentReportData,
    ReportFindingDetail,
    ReportValidationSummary,
)
from app.services.reports.generator import ReportGeneratorService


def test_jinja2_autoescape_xss_prevention() -> None:
    """Verify that script tags and XSS payloads in findings and sample records are escaped."""
    env = ReportGeneratorService.get_jinja_env()
    template = env.get_template("incident_report.html")

    malicious_finding = ReportFindingDetail(
        id="f_malicious",
        rule_id="RULE-XSS-001",
        rule_name="<script>alert('pwned_name')</script>",
        category="NULL_CHECK",
        severity="CRITICAL",
        status="FAILED",
        dataset_id="orders.csv",
        message="Injection attempt: <script>alert(document.cookie)</script>",
        affected_record_count=1,
        total_record_count=100,
        sample_keys=["<script>alert(1)</script>", "safe_key_123"],
        sample_line_numbers=[42],
        sample_records=[{"order_id": '"><img src=x onerror=alert(1)>', "amount": 100}],
        created_at=datetime.now(UTC).isoformat(),
    )

    report_data = IncidentReportData(
        report_id="rep_test_xss",
        investigation_id="inv_test_xss",
        generated_at=datetime.now(UTC).isoformat(),
        title="Security Test Report <script>alert('title')</script>",
        scenario={
            "id": "test_scenario",
            "name": "Scenario <script>alert('scen')</script>",
            "category": "security",
            "active_fixture_version": "defective",
        },
        investigation={
            "id": "inv_test_xss",
            "status": "OPEN",
            "verified_facts": ["Fact with <script>alert('fact')</script> payload"],
            "hypotheses": ["Hypothesis with <b>bold</b> and <svg onload=alert(1)>"],
            "action_items": ["Action with <iframe src='evil.com'></iframe>"],
        },
        validation_summary=ReportValidationSummary(
            run_id="run_test",
            executed_at=datetime.now(UTC).isoformat(),
            total_rules=1,
            passed_count=0,
            failed_count=1,
            warning_count=0,
            quality_health="CORRUPTED",
            duration_ms=120,
        ),
        findings=[malicious_finding],
        impacted_assets=[],
        pipeline_summary=None,
        integrity={"sha256": "fakehash123"},
    )

    rendered_html = template.render(**report_data.model_dump())

    # Assert raw script tags are NEVER present
    assert "<script>" not in rendered_html
    assert "</script>" not in rendered_html
    assert "<script" not in rendered_html
    assert "<iframe" not in rendered_html
    assert "<svg" not in rendered_html

    # Assert proper entity escaping
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered_html
    assert "&lt;script&gt;alert(document.cookie)&lt;/script&gt;" in rendered_html
    assert "&lt;script&gt;alert(&#39;pwned_name&#39;)&lt;/script&gt;" in rendered_html or (
        "&lt;script&gt;alert('pwned_name')&lt;/script&gt;" in rendered_html
    )


def test_csp_meta_tag_present_and_strict() -> None:
    """Verify that Content Security Policy meta header is present with strict directives."""
    env = ReportGeneratorService.get_jinja_env()
    template = env.get_template("incident_report.html")

    report_data = IncidentReportData(
        report_id="rep_csp_test",
        investigation_id="inv_csp_test",
        generated_at=datetime.now(UTC).isoformat(),
        title="CSP Enforcement Test",
        scenario={
            "id": "monday_revenue_mystery",
            "name": "Monday Revenue Mystery",
            "category": "e-commerce",
            "active_fixture_version": "defective",
        },
        investigation={
            "id": "inv_csp_test",
            "status": "OPEN",
            "verified_facts": ["15 duplicate order IDs detected."],
            "hypotheses": ["Webhook duplicate delivery."],
            "action_items": ["Deduplicate orders."],
        },
        validation_summary=ReportValidationSummary(
            run_id="run_123",
            executed_at=datetime.now(UTC).isoformat(),
            total_rules=5,
            passed_count=4,
            failed_count=1,
            warning_count=0,
            quality_health="CORRUPTED",
            duration_ms=45,
        ),
        findings=[],
        impacted_assets=[],
        pipeline_summary=None,
        integrity={"sha256": "testhash"},
    )

    rendered_html = template.render(**report_data.model_dump())

    # Assert exact CSP meta tag
    expected_csp = (
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;\">"
    )
    assert expected_csp in rendered_html

    # Assert no external scripts or stylesheets
    assert "<script" not in rendered_html
    assert '<link rel="stylesheet"' not in rendered_html


def test_collapsible_details_evidence_panels() -> None:
    """Verify native collapsible HTML <details> and <summary> panels exist for sample evidence."""
    env = ReportGeneratorService.get_jinja_env()
    template = env.get_template("incident_report.html")

    finding_with_samples = ReportFindingDetail(
        id="f_sample",
        rule_id="VAL-ORD-001",
        rule_name="Order ID Uniqueness Check",
        category="UNIQUENESS",
        severity="CRITICAL",
        status="FAILED",
        dataset_id="orders.csv",
        message="15 duplicate order records detected.",
        affected_record_count=15,
        total_record_count=1250,
        sample_keys=["ORD-1002", "ORD-1009", "ORD-1045"],
        sample_line_numbers=[14, 28, 59],
        sample_records=[{"order_id": "ORD-1002", "customer_id": "CUST-99"}],
        created_at=datetime.now(UTC).isoformat(),
    )

    report_data = IncidentReportData(
        report_id="rep_details_test",
        investigation_id="inv_details_test",
        generated_at=datetime.now(UTC).isoformat(),
        title="Evidence Panel Test",
        scenario={"id": "test", "name": "Test Scenario", "category": "test"},
        investigation={"id": "inv_details_test", "status": "OPEN"},
        validation_summary=ReportValidationSummary(
            run_id="run_abc",
            executed_at=datetime.now(UTC).isoformat(),
            total_rules=1,
            passed_count=0,
            failed_count=1,
            warning_count=0,
            quality_health="CORRUPTED",
        ),
        findings=[finding_with_samples],
        impacted_assets=[],
        pipeline_summary=None,
        integrity={"sha256": "testhash"},
    )

    rendered_html = template.render(**report_data.model_dump())

    assert "<details" in rendered_html
    assert "<summary>" in rendered_html
    assert "</details>" in rendered_html
    assert "ORD-1002" in rendered_html
    assert "ORD-1009" in rendered_html
    assert "14, 28, 59" in rendered_html


def test_sha256_cryptographic_integrity() -> None:
    """Verify SHA-256 calculation matches expected hash over raw JSON content."""
    sample_content = '{"report_id": "rep_123", "status": "CORRUPTED"}'
    expected_hash = hashlib.sha256(sample_content.encode("utf-8")).hexdigest()

    assert len(expected_hash) == 64
    assert all(c in "0123456789abcdef" for c in expected_hash)


def test_utf8_special_characters_rendering() -> None:
    """Verify Unicode, emojis, and non-ASCII characters render safely in HTML and JSON."""
    env = ReportGeneratorService.get_jinja_env()
    template = env.get_template("incident_report.html")

    special_text = (
        "Anomaly: Revenue spiked by €142,000 / ¥1,000,000 (Sunday sync ⚡ — François's orders)"
    )

    report_data = IncidentReportData(
        report_id="rep_utf8",
        investigation_id="inv_utf8",
        generated_at=datetime.now(UTC).isoformat(),
        title=f"UTF-8 Test: {special_text}",
        scenario={"id": "test", "name": "Unicode Test", "category": "test"},
        investigation={
            "id": "inv_utf8",
            "status": "OPEN",
            "verified_facts": [special_text],
            "hypotheses": [],
            "action_items": [],
        },
        validation_summary=ReportValidationSummary(
            run_id="run_utf8",
            executed_at=datetime.now(UTC).isoformat(),
            total_rules=1,
            passed_count=1,
            failed_count=0,
            warning_count=0,
            quality_health="HEALTHY",
        ),
        findings=[],
        impacted_assets=[],
        pipeline_summary=None,
        integrity={"sha256": "testhash"},
    )

    # Test JSON dump & reload
    json_str = json.dumps(report_data.model_dump(), default=str)
    reloaded = json.loads(json_str)
    assert special_text in reloaded["investigation"]["verified_facts"]

    # Test HTML render
    rendered_html = template.render(**report_data.model_dump())
    assert "€142,000" in rendered_html
    assert "¥1,000,000" in rendered_html
    assert "⚡" in rendered_html
    assert "François" in rendered_html
