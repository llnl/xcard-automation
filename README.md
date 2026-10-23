# xcard-automation

CLI-first automation pipeline for generating Genesis datacards from a dataset
directory plus a reusable sidecar answers file.

## Setup

- `uv sync` to create virtual environment and install xcard_automation packages.
- Confirm install with `uv pip list`
  - should see 
    - `+ xcard-automation==0.3.0`
    - `+ prompt-toolkit==3.0.53`
    - `+ questionary==2.1.1`
    - `+ wcwidth==0.9.2`
- test inspect with `uv run xcard-cli inspect <path-to-data-folder> --output-root <path-to-output-root-folder>`
- test generate with `uv run xcard-cli generate  <path-to-data-folder> --profile core --answers <path-to-answers.json>  --output-root <path-to-output-root-folder>`
- test configure with `uv run xcard-cli configure`

Project inputs can also live in one JSON or simple YAML config file. Relative
paths are resolved from the config file, and explicit command flags override
its values. The supported fields are `dataset_dir`, `output_root`, `answers`,
and `profile`:

```yaml
dataset_dir: data
output_root: output
answers: answers.json
profile: core
```

```bash
uv run xcard-cli inspect --config config.yaml
uv run xcard-cli generate --config config.yaml
```

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
python3 -m datacard_pipeline.cli inspect <dataset_dir>
python3 -m datacard_pipeline.cli run <dataset_dir> --profile core
python3 -m datacard_pipeline.cli validate <datacard.md>
```

Artifacts are written under `runs/<dataset_slug>/` by default:

```text
.
├── automation_output/
│   ├── normalized_metadata.json # Processed and standardized metadata
│   ├── ontology_alignment.json  # Results of the ontology alignment process
│   └── *.md                     # Auto-generated documentation and reports
├── input/
│   ├── answers.yaml            # User-provided answers for project configuration
│   ├── introspection.json      # Output from the `inspect` command
│   ├── ontology_summary.json   # Summary of the dataset ontology
│   └── source_manifest.json    # Manifest of all source files in the dataset
└── validation_output/
    ├── validation_report.json   # Detailed technical validation results
    ├── validation_summary.md    # Human-readable quality and grading summary
    └── *.md                     # Auto-generated documentation and reports
```


## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

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
