# Datacard Automation Pipeline Diagram

```mermaid
flowchart TD
    U[User / Operator] --> CLI["CLI entrypoint<br/>datacard_pipeline/cli.py"]

    subgraph Inputs["Inputs"]
        D1["Dataset directory<br/>local files or staged public sample"]
        D2["answers.json / interactive prompts<br/>human metadata"]
        D3["Canonical template intent<br/>/templates/data-card/template.md"]
        D4["Genesis ontology<br/>tools/ontology/genesis.yaml + SHACL/TTL/JSON-LD"]
    end

    subgraph Core["Implemented pipeline core"]
        P1["pipeline.py<br/>orchestrates run"]
        P2["introspect.py<br/>inspect files, README, CITATION, LICENSE,<br/>CSV columns, sizes, splits"]
        P3["questionnaire.py<br/>collect unresolved required metadata"]
        P4["mapper.py<br/>merge introspection + answers into normalized metadata"]
        P5["renderer.py<br/>frontmatter + narrative body generation"]
        P6["validator.py<br/>required fields, enums, dates,<br/>filename/workflow checks, placeholder checks"]
        P7["ontology.py<br/>load ontology enums + alignment report"]
        P8["artifacts.py<br/>write run directories and reports"]
    end

    subgraph Reuse["Adopted / adapted from existing code"]
        R1["From BaseData_Skills/datacard-generator<br/>- introspection pattern<br/>- validation result structure<br/>- body-fill/section mapping approach"]
        R2["From maven<br/>- intake/question batching pattern<br/>- pragmatic metadata collection flow<br/>- future adapter seam, not runtime dependency"]
        R3["Not directly reused in v1<br/>- maven Streamlit UI<br/>- URSA autofill runtime<br/>- BaseData v1.2 capability schema as canonical output"]
    end

    subgraph Validation["Validation + control layers"]
        V1["Repo-local contract<br/>datacard_pipeline/contract.py"]
        V2["Ontology-controlled vocabularies<br/>field-to-enum alignment"]
        V3["Template-oriented rendering rules<br/>no leftover placeholders"]
        V4["Validation report<br/>ok/findings JSON + markdown summary"]
    end

    subgraph Outputs["Run artifacts / outputs"]
        O1["input/source_manifest.json"]
        O2["input/introspection.json"]
        O3["input/answers.yaml"]
        O4["input/ontology_summary.json"]
        O5["automation_output/normalized_metadata.json"]
        O6["automation_output/checksums.sha256"]
        O7["automation_output/ontology_alignment.json"]
        O8["automation_output/genesis_datacard_<slug>.md"]
        O9["validation_output/validation_report.json"]
        O10["validation_output/validation_summary.md"]
        O11["validation_output/genesis_datacard_<slug>.md<br/>final validated data card"]
    end

    D1 --> P2
    D2 --> P3
    D3 --> P5
    D4 --> P7

    CLI --> P1
    P1 --> P2
    P1 --> P3
    P1 --> P4
    P1 --> P5
    P1 --> P6
    P1 --> P7
    P1 --> P8

    P2 --> P4
    P3 --> P4
    P7 --> P3
    P7 --> P6
    P4 --> V1
    V1 --> P5
    P5 --> V3
    V3 --> P6
    P6 --> V2
    V2 --> V4

    R1 -. adopted ideas .-> P2
    R1 -. adopted ideas .-> P6
    R1 -. adopted ideas .-> P5
    R2 -. adopted ideas .-> P3
    R2 -. adopted ideas .-> P1
    R3 -. excluded from v1 runtime .-> P1

    P8 --> O1
    P2 --> O2
    P3 --> O3
    P7 --> O4
    P4 --> O5
    P2 --> O6
    P7 --> O7
    P5 --> O8
    V4 --> O9
    V4 --> O10
    O8 --> O11

    O8 --> P6
```

## Notes

- Canonical output target: the provided Genesis markdown datacard template shape, not the `BaseData_Skills` v1.2 capability-container schema.
- Primary execution surface: CLI first. `maven` is a future integration point, not a current runtime dependency.
- Validation stack:
  - contract-driven required fields and profile rules
  - local enum/date/consistency checks
  - ontology-backed vocabulary alignment warnings
  - unresolved-placeholder rejection
- Main adopted behavior:
  - `BaseData_Skills` informed the file introspection, body-fill, and validation model
  - `maven` informed the human-in-the-loop metadata intake flow
- Main outputs:
  - normalized machine-readable metadata
  - rendered markdown datacard
  - validation report
  - ontology alignment report
  - final validated datacard copy
