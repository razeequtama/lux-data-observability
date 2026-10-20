# Lux Security & Trust Boundaries Specification

## 1. Threat Model & Trust Boundaries

Lux is an observational data tool designed to ingest, process, and inspect datasets provided as local files or uploads. Because users may upload arbitrary CSV and JSON files, the platform assumes that **all dataset contents, column names, filenames, and metadata are untrusted inputs**.

```text
[ UNTRUSTED ZONE ]                   [ APPLICATION BOUNDARY ]                 [ TRUSTED CORE ]
User File Uploads     ───► [ MIME / Size / Schema Validator ] ───► Ingestion Storage (data/uploads/UUID)
Dataset Values & Headers ──► [ Strict HTML Escaping & CSP ]     ───► HTML / JSON Report Artifacts
API Request Payloads  ───► [ Pydantic v2 Schema Validation ]   ───► SQLite Persistent DB (lux.db)
```

---

## 2. File Upload & Ingestion Defenses

### 2.1 File Size & Format Restrictions
- **Strict Size Limit:** File uploads are limited to a maximum of **20 MB** per file. Uploads exceeding this threshold are immediately rejected with HTTP 413 (*Payload Too Large*) before buffering into memory.
- **Extension Whitelist:** Only `.csv` and `.json` extensions are permitted. All executable formats (`.py`, `.sh`, `.exe`, `.bat`, `.html`, `.js`, `.php`) are rejected.
- **MIME Type & Content Sniffing Protection:**
  - Files claiming to be CSV or JSON are parsed with standard header inspections.
  - Multi-part upload content streams are inspected using Python’s standard `csv.Sniffer` and `json.loads` within bounded read buffers.
  - Reject binary streams, compressed archive headers (preventing zip-bomb vectors), or null-byte characters.

### 2.2 Path Traversal & Filename Sanitization
- **No Direct Filesystem Path Exposure:** Client-supplied filenames are never used directly to construct filesystem paths.
- **UUID Directory Isolation:** Every uploaded file is written to an isolated directory generated via `uuid.uuid4()`:
  ```text
  data/uploads/{uuid4()}/dataset.csv
  ```
- **Path Canonicalization:** All storage paths are verified against the absolute resolved base path (`data/`):
  ```python
  resolved_path = (UPLOAD_DIR / upload_id / filename).resolve()
  if not resolved_path.is_relative_to(UPLOAD_DIR.resolve()):
      raise SecurityException("Path traversal attempt detected.")
  ```

---

## 3. Cross-Site Scripting (XSS) & Markup Injection Defenses

### 3.1 Report Artifact Security (HTML Exports)
Exported incident reports can be downloaded and opened directly in a web browser. If an attacker embeds `<script>alert(document.cookie)</script>` or `"><img src=x onerror=...>` in a CSV product name or order ID, this could execute as script.
- **Jinja2 Auto-Escaping:** The template engine is initialized with `select_autoescape(['html', 'xml'])`. Every interpolated string is converted to safe HTML entities (`&lt;`, `&gt;`, `&quot;`, `&#39;`, `&amp;`).
- **Defensive Content Security Policy (CSP):** Every generated HTML report includes a strict CSP `<meta>` tag:
  ```html
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;">
  ```
  - `default-src 'none'`: Disables all outbound network requests, websockets, and external scripts.
  - `style-src 'unsafe-inline'`: Allows only self-contained inline CSS styles embedded in the header.
  - `sandbox`: Enforces a browser sandbox restricting popups, script execution, and forms.

### 3.2 React UI Frontend Rendering
- The React frontend exclusively renders data using JSX `{finding.message}` text interpolation, which treats all values as string primitives, completely immune to HTML injection.
- The use of `dangerouslySetInnerHTML` is strictly prohibited throughout the entire codebase.

---

## 4. Arbitrary Code Execution Prevention

- **Declarative Rules Only:** Validation rules are defined purely as declarative JSON structures (`rules.json`).
- **No Dynamic Code Evaluation:** The backend never calls `eval()`, `exec()`, or `compile()` on user input, rule parameters, or dataset values.
- **No Dynamic Raw SQL Execution:** SQLite interactions are handled exclusively via SQLAlchemy ORM parameterized queries or strictly typed query builders. Raw SQL concatenation is forbidden.
- **No Dynamic Shell Commands:** Lux never invokes system subprocesses or shell commands based on dataset or pipeline parameters.

---

## 5. Resource Limits & Denial of Service (DoS)

- **CPU / Memory Quotas:** Docker Compose service configurations specify memory limits (`1GB` for backend, `512MB` for frontend) and CPU quotas (`1.0` cores) to prevent container starvation.
- **Validation Run Timeouts:** Validation engine execution enforces a 30-second timeout per dataset run.
- **Row Read Limits:** Row previews are strictly paginated with an enforced upper limit of 100 rows per request.

---

## 6. Secrets & Environment Management

- **Zero Hardcoded Credentials:** No API keys, database passwords, or secret tokens are stored in the repository.
- **Configuration via Environment Variables:** All runtime settings (e.g., `LUX_ENV`, `LUX_DATA_DIR`, `LUX_LOG_LEVEL`) are managed via Pydantic `BaseSettings` reading from `.env` files.
- **Production Error Masking:** Production API responses never leak internal Python stack traces, file paths, or system environment variables. All errors return the sanitized `ErrorResponse` schema.

