# ADR-002: Deterministic Custom Python Validation Engine

## Status
Accepted

## Context
Lux requires a genuine validation engine executing data-quality checks against loaded CSV and JSON datasets. The engine must support rule categories including missing required values, duplicate identifiers, invalid values and data types, referential integrity violations, timestamp/temporal anomalies, schema changes, record-count anomalies, basic distribution/value-range anomalies, and missing expected partitions.

We evaluated two main approaches:
1. **External Validation Framework (e.g., Great Expectations, Soda Core):**
   - *Pros:* Rich pre-built library of expectations.
   - *Cons:* Heavy dependency footprint (>200 transitive packages), slow container startup, complex abstraction layers that obscure core business logic, frequent breaking API changes, and hard-to-customize structured evidence models.
2. **Deterministic Custom Python Validation Engine:**
   - *Pros:* Completely self-contained, zero telemetry, minimal dependencies, lightning-fast execution (<100ms for synthetic datasets), fully customizable structured evidence matching Lux's domain models, and straightforward extensibility.
   - *Cons:* Requires implementing the core rule evaluators manually.

## Decision
We chose to implement a **Deterministic Custom Python Validation Engine**:
- **Protocol-driven Architecture:** Every rule implements a clean `BaseValidationRule` protocol:
  ```python
  class BaseValidationRule(ABC):
      rule_id: str
      rule_category: RuleCategory
      severity: Severity
      
      @abstractmethod
      def evaluate(self, context: ValidationContext) -> list[ValidationFinding]:
          pass
  ```
- **Rule Registry:** A registry pattern dynamically instantiates rules from declarative JSON/YAML definitions.
- **Structured Evidence:** Findings produce rich, structured diagnostic evidence:
  - `rule_id`, `rule_category`, `severity`, `status` (`PASSED`, `FAILED`, `WARNING`, `SKIPPED`, `ERROR`).
  - `affected_dataset`, `affected_fields`, `affected_record_count`.
  - Representative sample rows (row indices, primary keys, observed vs expected values).
  - Validation execution duration and execution timestamp.
- **Streaming & Chunking:** Datasets are read using streaming iterators with bounded memory footprints, avoiding loading arbitrary-sized datasets entirely into memory.

## Consequences

### Positive
- **Complete Reproducibility:** No hidden heuristics, external network calls, or non-deterministic behaviors.
- **Fast Test Execution:** Pytest can run hundreds of validation tests in milliseconds.
- **Precision Evidence:** Diagnostic outputs match Lux's UI and reporting needs exactly without adapting third-party JSON blobs.
- **Low Footprint:** Keeps the backend image small and build times fast.

### Negative & Mitigations
- **Initial Implementation Effort:** Requires implementing the core rules (null checks, uniqueness, regex/type checks, foreign key referential integrity, range checks, and temporal checks).
  - *Mitigation:* The rule set is focused on the defined functional categories and modularized so each rule has dedicated unit tests.

