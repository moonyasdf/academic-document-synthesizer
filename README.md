### Academic Document Synthesizer

An AI-powered system that drafts and iteratively refines structured academic documents. It is optimized for Google’s Gemini models and uses a schema-validated JSON plan to drive safe, deterministic refinements.

### What it does

- Initial drafting: Generates a complete Markdown document using strict, standardized section headers.
- Peer-review refinement loop: Requests a JSON-only “refinement plan” that identifies issues and returns full rewritten sections. The plan is validated with Pydantic before applying edits.
- Intelligent termination: Stops after consecutive “no further improvements” verdicts.
- Checkpointing: Saves progress after each successful step; can resume from interruptions.
- Robust API handling: Concatenates multi-part responses; retries with backoff; structured warnings for blocked prompts.
- Debugging: Optional raw-response logging for fast diagnosis.

### Key improvements in this version

- JSON-only refinement: The first draft remains plain Markdown; refinement requests enforce application/json.
- Stronger prompts: Refiner prompt redesigned to demand a single valid JSON object, exact section headers (English), and content language compliance.
- Stricter replacement: Rewrites are applied by section title to prevent duplication and drift.
- Test suite: Unit tests for schemas, JSON extraction, refinement application; an end-to-end test with a mocked API; optional validators.
- Safety settings documentation: Clear reference and examples to configure Gemini safety filters.

---

## Project structure

```
.
├── README.md
├── config.yaml
├── run_synthesis.py
├── agent.py
├── schemas.py
├── problem_statement.txt
├── prompts/
    ├── system_expert_prompt.txt
    ├── initial_synthesis_prompt.txt
    └── iterative_refinement_prompt.txt
```

---

## Prerequisites

- Python 3.8+
- Google Gemini API key
- Install dependencies:
```bash
pip install -r requirements.txt
```

Set your API key:
- Windows PowerShell:
```powershell
$env:GOOGLE_API_KEY="YOUR_API_KEY"
```
- Linux/macOS:
```bash
export GOOGLE_API_KEY="YOUR_API_KEY"
```

If not set, the program will securely prompt for the key.

---

## Configuration

Edit `config.yaml` to control model, synthesis behavior, and debugging. Example:

```yaml
model_config:
  model_name: "gemini-2.5-pro"
  temperature: 0.1
  api_endpoint: "https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

  # Optional: Safety settings for Gemini (see “Safety settings” below)
  # Remove or adjust per your use case. Defaults here are permissive for academic content.
  safety_settings:
    - category: "HARM_CATEGORY_HARASSMENT"
      threshold: "BLOCK_NONE"
    - category: "HARM_CATEGORY_HATE_SPEECH"
      threshold: "BLOCK_NONE"
    - category: "HARM_CATEGORY_SEXUALLY_EXPLICIT"
      threshold: "BLOCK_NONE"
    - category: "HARM_CATEGORY_DANGEROUS_CONTENT"
      threshold: "BLOCK_NONE"
    - category: "HARM_CATEGORY_CIVIC_INTEGRITY"
      threshold: "BLOCK_NONE"

synthesis_config:
  max_refinements: 5
  confidence_threshold: 2

debugging:
  debug_mode: true
  log_directory: "debug_logs"
```

Notes:
- The agent enforces application/json only for refinement requests. The initial draft is plain Markdown.
- If `debug_mode` is true, raw model responses are saved to `debug_logs/`.

---

## Safety settings (Gemini)

Gemini supports adjustable safety filters by category:

- HARM_CATEGORY_HARASSMENT
- HARM_CATEGORY_HATE_SPEECH
- HARM_CATEGORY_SEXUALLY_EXPLICIT
- HARM_CATEGORY_DANGEROUS_CONTENT
- HARM_CATEGORY_CIVIC_INTEGRITY

Block thresholds (API values):
- BLOCK_NONE: Never block
- BLOCK_ONLY_HIGH: Block only when the probability is HIGH
- BLOCK_MEDIUM_AND_ABOVE: Block when probability is MEDIUM or HIGH
- BLOCK_LOW_AND_ABOVE: Block when probability is LOW, MEDIUM, or HIGH
- HARM_BLOCK_THRESHOLD_UNSPECIFIED: Use model defaults

How this project uses them:
- You can define `safety_settings` in `config.yaml` (as in the example above). They are sent with each request if present.
- You can start permissive (BLOCK_NONE) for academic content and tighten categories as needed.
- If a prompt is blocked, the agent prints the block reason (e.g., `promptFeedback.blockReason`) and skips or retries as configured.

Example: stricter hate speech and harassment, permissive elsewhere:
```yaml
model_config:
  safety_settings:
    - category: "HARM_CATEGORY_HATE_SPEECH"
      threshold: "BLOCK_LOW_AND_ABOVE"
    - category: "HARM_CATEGORY_HARASSMENT"
      threshold: "BLOCK_MEDIUM_AND_ABOVE"
    - category: "HARM_CATEGORY_SEXUALLY_EXPLICIT"
      threshold: "BLOCK_ONLY_HIGH"
    - category: "HARM_CATEGORY_DANGEROUS_CONTENT"
      threshold: "BLOCK_ONLY_HIGH"
    - category: "HARM_CATEGORY_CIVIC_INTEGRITY"
      threshold: "BLOCK_MEDIUM_AND_ABOVE"
```

Troubleshooting blocked content:
- If `finishReason` is SAFETY, the candidate is withheld. The agent logs the finish reason and can retry.
- Review the `debug_logs/` to see the context and tune settings or prompts accordingly.

---

## Usage

Standard run (reads `problem_statement.txt`, asks language, writes to `output/final_document.md`):
```bash
python run_synthesis.py
```

With a custom task and output:
```bash
python run_synthesis.py my_task.txt -o results/paper.md
```

Safeguard: temporarily raise the maximum refinement cycles:
```bash
python run_synthesis.py -r 10
```

Resume an interrupted run:
- Re-run the exact same command; the agent resumes from the checkpoint (a hidden file alongside the output).

---

## Document structure and prompts

- Headers are standardized in English and must appear exactly as:
  - Title
  - Introduction
  - Experimental Methodology
  - Expected Results and Analysis
  - Discussion
  - Conclusion
  - Final Reflection
  - Bibliography

- Content is generated in the user-selected language.
- Refinement JSON schema (enforced by Pydantic):
  - Final Verdict: SIGNIFICANT_IMPROVEMENTS_REQUIRED | MINOR_IMPROVEMENTS_SUGGESTED | NO_FURTHER_IMPROVEMENTS_NEEDED
  - Summary of Findings: list of { location, issue, Issue Classification }, where Issue Classification is Critical Flaw | Justification Gap
  - Refined Document Sections: list of { section_title, content }

---

## How it works (high level)

1) Load config from `config.yaml` and request API key (or use env var).
2) Initial draft:
   - Uses `initial_synthesis_prompt.txt`
   - Returns plain Markdown (no JSON)
   - Saves a checkpoint
3) Refinement cycles:
   - Uses `iterative_refinement_prompt.txt`
   - Requests JSON-only plan; validates with Pydantic
   - Applies full section rewrites by header match
   - Intelligent termination after consecutive final verdicts
4) Finalize:
   - Writes the final Markdown to the output file
   - Removes checkpoint

API robustness:
- Concatenates multi-part responses
- Retries on transient network errors with exponential backoff
- Logs blocked content reasons and empty candidate warnings

---

## Troubleshooting

- Empty or blocked responses:
  - Check console messages for `promptFeedback.blockReason` or `finishReason: SAFETY`
  - Use `debug_mode: true` to inspect raw responses
  - Adjust safety settings or temperature and retry
- JSON parsing errors:
  - The refiner prompt enforces a single JSON object; if issues persist, check `debug_logs/` for stray text
- Section not replaced:
  - Ensure `section_title` matches the exact English header; content can be any supported language

