# ADR-006: Separation of Pipeline Execution Health and Data Quality Health

## Status
Accepted

## Context
A fundamental problem in modern data engineering is the conflation of **pipeline execution status** (did the job exit with return code 0?) with **data quality health** (are the output records accurate, complete, and reliable?).

In the signature scenario (*Monday Revenue Mystery*), the daily revenue aggregation pipeline ran to completion with exit status `SUCCESS`. However, upstream source files contained duplicate order records and missing order-item rows. Because the pipeline succeeded mechanically, traditional infrastructure alerts remained green while executive dashboards displayed corrupted revenue figures.

If Lux treats a green pipeline run as proof of healthy data, or flags a pipeline as "crashed" when it actually completed with dirty data, it fails its core observability mission.

## Decision
We established a strict **Dual-Dimension Status Model** across all database entities, API contracts, and user interface components:

1. **Pipeline Execution Dimension (`execution_status`):**
   - Measures compute job execution:
     - `COMPLETED_SUCCESS`: Process terminated with zero exit code.
     - `COMPLETED_WITH_WARNINGS`: Process terminated successfully with non-fatal operational warnings.
     - `FAILED`: Process crashed, threw unhandled exceptions, or timed out.
     - `RUNNING`: Job currently executing.
     - `CANCELLED`: Manually or system aborted.

2. **Data Quality Dimension (`quality_health`):**
   - Measures data integrity based on executed validations:
     - `HEALTHY`: All executed checks passed.
     - `WARNING`: Low/Medium severity non-critical anomalies detected.
     - `DEGRADED`: High severity anomalies observed; some downstream data may be unreliable.
     - `CORRUPTED`: Critical severity failures observed (e.g., duplicate primary keys, broken referential integrity, record count collapse).
     - `UNVALIDATED`: Data has not been evaluated against quality rules.

3. **Asset Lineage Impact Classification (`impact_status`):**
   - Distinct classification for assets in the lineage tree:
     - `CONFIRMED_FAILED`: The asset itself was directly validated and produced validation failures.
     - `DIRECTLY_AFFECTED`: The asset is an immediate downstream consumer of a `CONFIRMED_FAILED` asset.
     - `POTENTIALLY_AFFECTED`: The asset is a transitive downstream consumer in the dependency path.
     - `HEALTHY`: The asset has passing validations or no failing upstream dependencies.

4. **UI Visual Distinction:**
   - Execution status is represented by distinct operational indicators (e.g., terminal/run icons with duration).
   - Quality health is represented by distinct structural badges and severity pills (with icon + text, never relying on color alone).

## Consequences

### Positive
- **Accurate Truth Representation:** Explicitly clarifies scenarios where "The pipeline succeeded, but the data is corrupted."
- **Prevents Misleading Root Causes:** Analysts can clearly see whether a metric discrepancy stems from a pipeline crash vs dirty source data.
- **Precise Recovery Verification:** Verification can confirm that while a pipeline re-executed successfully, quality validations also independently confirmed the fix.

### Negative & Mitigations
- **Cognitive Load:** Users must interpret two distinct status badges per pipeline node.
  - *Mitigation:* The UI groups these under clear headings: "Compute Run Status" and "Data Quality Health" with explanatory tooltips and accessible text.

