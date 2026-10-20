# ADR-005: Safe Incident Report Generation and XSS Sanitization Strategy

## Status
Accepted

## Context
Functional Requirement FR-07 requires Lux to generate reproducible, downloadable incident reports in both **JSON** and **HTML** formats. These reports must contain:
- Incident and investigation identifiers.
- Dataset schemas and validation run metadata.
- Failed checks, severities, and representative sample records containing raw cell values.
- Lineage dependency paths and potentially affected downstream assets.
- Pipeline execution history and freshness observations.
- Recommended remediation steps.

Because dataset values and column headers come from uploaded files or external inputs, they must be treated as **untrusted data**. Rendering raw strings into HTML templates creates a critical Cross-Site Scripting (XSS) vulnerability if a malicious dataset contains strings like `<script>alert('xss')</script>` or `"><img src=x onerror=...>` in order IDs or product names.

## Decision
We chose **Strictly Autoescaped Jinja2 Templates with Content Security Policy (CSP) and Standalone Inlined CSS**:
1. **Template Engine Configuration:**
   - Reports are rendered using Jinja2 with `autoescape=select_autoescape(['html', 'xml'])` explicitly enforced.
   - All variables interpolated into HTML elements or attributes are automatically escaped using HTML entity encoding (`&lt;`, `&gt;`, `&quot;`, `&#39;`, `&amp;`).
2. **Defensive Content Security Policy (CSP):**
   - Every exported HTML report includes a strict CSP `<meta>` header:
     ```html
     <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;">
     ```
   - This disables all JavaScript execution, prevents network requests, and sandboxes the exported document even when opened locally in a web browser.
3. **Self-Contained Styling:**
   - All styling (using the Lux Purple brand palette) is embedded in a `<style>` block within the report header. No external CDNs, Google Fonts, or remote stylesheets are referenced.
4. **JSON Export Safety:**
   - JSON reports are generated via Pydantic model serialization (`model_dump_json(indent=2)`), ensuring all Unicode characters and string fields are safely escaped without risk of JSON hijacking or syntax breakage.

## Consequences

### Positive
- **Guaranteed XSS Immunity:** Eliminates markup injection from untrusted dataset cells and metadata.
- **Portability:** Exported HTML reports can be emailed, archived, or opened offline in air-gapped environments without broken external styles.
- **Auditability:** Reports provide an immutable snapshot of investigation findings at the moment of generation.

### Negative & Mitigations
- **No Dynamic Scripts in Reports:** Exported HTML reports cannot run client-side JavaScript for interactive accordion toggles.
  - *Mitigation:* The HTML report is designed with semantic HTML elements (`<details>` and `<summary>`) for expandable evidence panels, providing collapsible interactivity without executing JavaScript.

