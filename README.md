# xcard-automation

CLI-first automation pipeline for generating Genesis datacards from a dataset
directory plus a reusable sidecar answers file.

## Current status

The packaged Genesis 1.2 `core` bundle produces a card that passes canonical
`xcard-evaluation` validation. It automates Discoverability, Interoperability,
and Reusability from local inspection, supplied answers, and optional cited LLM
evidence. Accessibility, Governed Use, and AI Usability remain disabled until
their authoritative inputs are supplied and mapped.

## Setup

- Clone with `git clone --recurse-submodules ...`, or run
  `git submodule update --init --recursive` in an existing checkout. The
  `xcard-evaluation` submodule provides canonical Genesis 1.2 validation.
- `uv sync` to create virtual environment and install xcard_automation packages.
- Confirm install with `uv pip list`
  - should see 
    - `+ xcard-automation==0.3.0`
    - `+ prompt-toolkit==3.0.53`
    - `+ questionary==2.1.1`
    - `+ wcwidth==0.9.2`
- test inspect with `uv run xcard-cli inspect <path-to-data-folder> --output-root <path-to-output-root-folder>`
- test generation with `uv run xcard-cli run <path-to-data-folder> --profile core --answers <path-to-answers.json> --output-root <path-to-output-root-folder>`
- create a project config with `uv run xcard-cli configure-project`

Project inputs can also live in one JSON or simple YAML config file. Relative
paths are resolved from the config file, and explicit command flags override
its values. The wizard writes `project_name`, `dataset_dir`, and `output_root`;
`answers` and `profile` are optional supported fields:

```yaml
project_name: my-project
dataset_dir: data
output_root: output
answers: answers.json
profile: core
```

### LLM-assisted repository crawl

Configure an external agent to inspect the dataset repository and return cited
metadata evidence. The command receives a JSON request on standard input and
must write one JSON evidence object to standard output; the shipped
`repository-crawl` skill defines that contract.

```yaml
llm:
  command: [my-agent, crawl]
```

The pipeline applies only cited, high-confidence descriptive facts approved by
the bundle policy. The policy currently permits summary, keywords,
science-domain, provenance, schema-version, and dataset-language suggestions.
Access, security, governance, release, legal, identity, and AI-use claims
always require an explicit answer or trusted system-of-record input.

Title, author, and citation suggestions are instead written to
`automation_output/llm_proposals.json` for review. After reviewing its cited
values, apply all proposals—or only selected fields—to the answers file used
for the next generation:

```bash
uv run xcard-cli approve-proposals <run-dir> --answers answers.json
uv run xcard-cli approve-proposals <run-dir> --answers answers.json \
  --field identification.name --field authors
uv run xcard-cli run <dataset-dir> --profile core --answers answers.json \
  --output-root <output-dir>
```

The command refuses to replace an existing answer unless `--force` is passed.
Approval is explicit: proposals are never added to a card until they are
written to the answers file and the pipeline is run again.

Use `--llm-agent <command> [arguments...]` as the final CLI option to override
the configured command for one run. Because the command is an external process,
deploy it in an environment that enforces the skill's file and network limits;
the pipeline validates evidence but cannot sandbox that process itself.

```bash
uv run xcard-cli inspect --config config.yaml
uv run xcard-cli run --config config.yaml --profile core
```

To run a different schema, point the command at a local bundle containing its
`bundle.yaml`, runtime LinkML YAML, mapping, and Jinja template. A bundle may
also include an `ontology` YAML asset for traceability.

```bash
uv run xcard-cli run <dataset_dir> --profile <bundle-profile> \
  --schema-bundle <bundle-dir> --output-root <output-dir>
```

`profiles` is optional bundle metadata: when omitted, any profile name is
accepted. A bundle’s generated card must include YAML frontmatter containing
the projected model so it can be checked later:

```bash
uv run xcard-cli evaluate card.md --schema-bundle <bundle-dir>
```

`evaluate` validates Genesis 1.2 cards through the `xcard-evaluation`
submodule's canonical LinkML schema at
`xcard-evaluation/bundles/genesis_datacard/1.2`. The packaged Genesis `core`
profile generates a canonical, valid card with Discoverability,
Interoperability, and Reusability sections. It explicitly declares
Accessibility, Governed Use, and AI Usability unsupported because access and
governance claims require authoritative user input.

`configure-project` prompts for the project name, dataset root, and output
root. With a project name, inspection results are written consistently to
`<output-root>/<project-name>/input/introspection.json`.

## Testing

Install the development dependencies and run the test suite with coverage:

```bash
uv sync --extra dev
uv run pytest
```

The terminal output includes the coverage summary and `coverage.xml` is created
for GitLab CI. GitLab runs the same test command on every push.

## Commands

```bash
python -m xcard_automation inspect <dataset_dir>
python -m xcard_automation run <dataset_dir> --profile core
python -m xcard_automation evaluate <datacard.md>
python -m xcard_automation approve-proposals <run-dir> --answers answers.json
```

Artifacts are written under `runs/<dataset_slug>/` by default:

```text
.
├── automation_output/
│   ├── normalized_metadata.json # Processed and standardized metadata
│   ├── llm_evidence.json        # Raw external-agent response, when enabled
│   ├── llm_proposals.json       # Human-reviewed title, author, and citation suggestions
│   ├── llm_resolution.json      # Accepted/rejected LLM candidates
│   └── *.md                     # Auto-generated documentation and reports
├── input/
│   ├── answers.yaml            # User-provided answers for project configuration
│   ├── introspection.json      # Output from the `inspect` command
│   ├── llm_crawl_request.json  # Redacted agent request, when enabled
│   ├── ontology_summary.json   # Summary of the dataset ontology
│   └── source_manifest.json    # Manifest of all source files in the dataset
└── validation_output/
    ├── validation_report.json   # Detailed technical validation results
    ├── validation_summary.md    # Human-readable quality and grading summary
    └── *.md                     # Auto-generated documentation and reports
```


## Roadmap

- Map the remaining canonical Genesis 1.2 fields, including facilities,
  structured resources, spatial/temporal coverage, citations, and stewardship.
- Add trusted adapters and structured attestations for Accessibility, Governed
  Use, and AI Usability; then enable `extended`, `sensitive`, and `ai_ready`.
- Produce a schema-coverage report that classifies every canonical field as
  deterministic, LLM-safe, attested, repository-managed, or unsupported.
- Add actual process/network sandboxing for external crawl agents, plus
  URL-response provenance and schema-drift checks in CI.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
