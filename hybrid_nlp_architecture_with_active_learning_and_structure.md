# Hybrid NLP + LLM Architecture for Network Automation (User -> Cisco CLI -> User) with Active Learning

## Overview

**Goals:**
- Convert user instructions (natural language) into safe, accurate Cisco CLI commands.
- Parse Cisco CLI outputs into concise, human-friendly summaries.
- Minimize LLM usage for cost, latency, and predictability — use LLM as fallback or for prettifying outputs.
- Maintain deterministic, auditable command generation for safety.
- Continuously improve via active learning from real user feedback.

**High-level approach:** Hybrid NLU + deterministic parsing + LLM fallback

---

## System Components

1. **User Query Handler (FastAPI service)**
   - Accepts NL text from UI, chatbot, or API client.
   - Normalizes text (lowercase, remove extra spaces, spell correction if needed).

2. **NLU Layer**
   - **Intent Classifier**: Distinguish between command types (`show`, `config`, `troubleshoot`, etc.).  
     - Model: Lightweight transformer (DistilBERT) or scikit-learn classifier with TF-IDF features.
   - **Entity Extractor (NER)**: Extract device/interface names, VLAN IDs, IP addresses.  
     - Model: spaCy or Hugging Face fine-tuned token classification model.

3. **Command Template Mapper**
   - Uses intent + entities to fill in pre-defined Jinja2/TextFSM templates for Cisco CLI.
   - Example:  
     User: "show me VLAN 10" → Template: `show vlan {vlan_id}` → Output: `show vlan 10`.

4. **Execution Layer**
   - Sends CLI command to Cisco switch via NETCONF/SSH/RESTCONF.
   - Receives raw CLI output.

5. **Output Parsing Layer**
   - Deterministic parser (TextFSM templates or regex) to convert raw CLI text into structured JSON.
   - Example: `show ip interface brief` output → list of interfaces with status.

6. **Natural Language Generator**
   - Deterministic phrasing for common patterns (via templates).
   - LLM fallback for less structured summaries.

7. **Active Learning Loop**
   - Every user input + CLI output + generated result is stored (with consent) in feedback DB.
   - Users can flag incorrect outputs via UI or API.
   - Uncertain model predictions (low confidence or high disagreement between models) are sampled for labeling.
   - Labeling tool updates dataset, retrains lightweight models regularly (weekly or nightly).
   - LLM outputs are also logged and compared with deterministic outputs to detect improvement opportunities.

8. **Safety Layer**
   - All generated CLI commands validated against a safe-command whitelist before execution.
   - No config-modifying command runs without explicit confirmation.

---

## Data Flow

1. **User input** → Normalizer → NLU (Intent + Entities) → Template Mapper → CLI Command
2. CLI Command → Execution Layer → Raw Output → Parser → JSON
3. JSON → NLG (Template or LLM) → User-friendly text
4. All (input, CLI, JSON, output, feedback) → Feedback DB → Active Learning pipeline

---

## Deployment Notes

- Deploy NLU models as microservices (containerized).
- Use feature flags to switch between deterministic and LLM generation.
- Maintain a model registry (MLflow) to track versions.
- Canary test new models before full rollout.

---

## Monitoring & Logging

- Monitor:
  - Intent classification accuracy
  - Parsing success rate
  - Command execution failures
  - LLM latency/cost
- Log:
  - Raw user input
  - Generated CLI commands
  - Raw CLI output
  - Parsed JSON
  - Final user output
  - Feedback/flags

---

## API Endpoints

- `POST /nlu/parse` → {intent, entities}
- `POST /command/generate` → {cli_command}
- `POST /command/execute` → {raw_output}
- `POST /output/parse` → {json_output}
- `POST /output/generate` → {user_text}
- `POST /feedback` → {input, output, rating, notes}

---

## Suggested Repository & Folder Structure

```
netops-automation/
├── README.md                 # Overview & setup
├── requirements.txt          # Python dependencies
├── setup.py                  # Optional packaging
├── configs/
│   ├── config.yaml           # Global config (paths, thresholds, API keys)
│   ├── logging.yaml          # Logging configuration
│   └── model_params.yaml     # NLU/NER hyperparameters
├── data/
│   ├── raw/                  # Unprocessed CLI outputs, feedback samples
│   ├── processed/            # Tokenized text, parsed JSON
│   ├── labels/               # Annotated intents/entities/templates
│   ├── templates/            # TextFSM/regex templates
│   └── registry/             # Dataset snapshots for training
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI entrypoint
│   │   ├── routers/          # Route definitions
│   │   │   ├── nlu.py
│   │   │   ├── parser.py
│   │   │   ├── feedback.py
│   │   │   └── deploy.py
│   │   └── deps.py           # Dependencies (db sessions, configs)
│   ├── nlu/
│   │   ├── intent_classifier.py
│   │   ├── ner_model.py
│   │   ├── fallback_llm.py
│   │   └── postprocessing.py
│   ├── parser/
│   │   ├── textfsm_engine.py
│   │   ├── regex_parser.py
│   │   └── summarizer.py
│   ├── feedback/
│   │   ├── ingestion.py
│   │   ├── active_learning.py
│   │   ├── labeling_ui/
│   │   │   ├── app.py
│   │   │   └── static/
│   │   └── sampler.py
│   ├── training/
│   │   ├── train_intent.py
│   │   ├── train_ner.py
│   │   ├── train_parser.py
│   │   ├── evaluate.py
│   │   └── registry_client.py
│   ├── deploy/
│   │   ├── shadow_mode.py
│   │   ├── canary_mode.py
│   │   └── rollback.py
│   └── utils/
│       ├── logger.py
│       ├── config_loader.py
│       ├── cli_validator.py
│       └── telemetry.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
├── scripts/
│   ├── export_model.py
│   ├── import_dataset.py
│   └── run_shadow_tests.py
├── docs/
│   ├── architecture.md       # This architecture doc
│   ├── api_spec.md
│   └── operations.md
└── .github/
    ├── workflows/
    │   ├── ci.yml
    │   └── retrain.yml
    └── ISSUE_TEMPLATE.md
```

---

## Notes on Structure
- `configs/` centralizes thresholds and paths to support reproducibility.
- `data/registry/` allows you to pin datasets to model versions for audits.
- `feedback/labeling_ui/` is intentionally separate so it can be deployed independently.
- `deploy/` holds rollout and rollback logic, essential for safe canary testing.
- `docs/architecture.md` should be updated whenever pipeline changes occur.
