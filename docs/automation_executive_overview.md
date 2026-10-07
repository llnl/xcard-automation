# Executive Overview: Datacard Automation

```mermaid
flowchart LR
    subgraph Legacy["Prior work adapted into this pipeline"]
        M["MAVEN<br/>LANL Streamlit intake workflow"]
        S["AmSC / MODCon / BaseData skills<br/>datacard-generator patterns"]
        O["Genesis ontology<br/>controlled vocabularies + semantic guidance"]
    end

    subgraph Adaptation["How it was adapted"]
        A1["Human-in-the-loop intake flow<br/>adapted from MAVEN's metadata collection style"]
        A2["File introspection + section mapping + validation shape<br/>adapted from BaseData/AmSC/MODCon skills"]
        A3["Ontology-backed vocab alignment<br/>added from Genesis ontology assets"]
    end

    subgraph Current["Current CLI-first automation"]
        C1["Inputs<br/>dataset files, README/CITATION/LICENSE,<br/>public links, answers.json or prompts"]
        C2["Introspect<br/>detect formats, columns, sizes, splits, provenance clues"]
        C3["Merge metadata<br/>combine discovered facts + human answers"]
        C4["Render data card<br/>fill canonical Genesis markdown template"]
        C5["Validate<br/>contract checks + ontology alignment + placeholder rejection"]
        C6["Outputs<br/>normalized metadata, reports, validated final data card"]
    end

    M --> A1
    S --> A2
    O --> A3

    A1 --> C1
    A2 --> C2
    A2 --> C4
    A2 --> C5
    A3 --> C3
    A3 --> C5

    C1 --> C2 --> C3 --> C4 --> C5 --> C6
```

## Narrative

- `MAVEN` contributed the intake philosophy: collect metadata in batches, keep a human in the loop, and make the workflow practical for real dataset stewards.
- `AmSC / MODCon / BaseData skills` contributed the datacard-generation mechanics: inspect data, infer what can be inferred, map findings into a card structure, and validate the result.
- The `Genesis ontology` adds controlled vocabularies and semantic alignment so generated metadata can be checked against project terminology instead of only local hard-coded enums.
- The current implementation turns those ideas into a `CLI-first pipeline` that starts from dataset artifacts and public/source metadata, produces a normalized metadata object, renders the canonical Genesis data card, validates it, and saves a final validated card plus supporting reports.

## High-Level Flow

1. Gather inputs from dataset files, public landing pages, and steward-provided answers.
2. Introspect what the system can discover automatically.
3. Fill gaps with human-supplied metadata.
4. Normalize everything into the target Genesis card structure.
5. Render the markdown data card.
6. Validate the card against required fields, consistency rules, ontology-backed vocabularies, and placeholder cleanup.
7. Emit the final validated data card and machine-readable run artifacts.
