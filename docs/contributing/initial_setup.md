# Initial Setup

## uv

We use [uv][uv] to manage our development environment.

- See [here][install_uv] for installation instructions.
- Create or sync your virtual environment with `uv sync --all-groups`.
- Activate your virtual environment with 
    - Mac/linux - `source .venv/bin/activate`.
    - Windows - `.venv/Scripts/activate`.

- Any time you need to add a dependency to the project, use
  `uv add <dependency>`.
- If the dependency is only used for development (e.g., for testing),
  use `uv add --dev <dependency>`.
- If the dependency should be grouped another way (e.g. "docs") then you add the dependency in a new group,
  e.g. `uv add --docs <dependency>`.

See uv's documentation for more details.

[uv]: https://docs.astral.sh/uv/
[install_uv]: https://docs.astral.sh/uv/#installation


## Pre-Commit

We also use [pre-commit][pre_commit] to handle keeping our repository
clean. You can run `pre-commit install` to install the pre-commit hooks
in your local repository. This will run the hooks defined in our
`.pre-commit-config.yaml`, and if any of them fail, it will prevent you
from committing.

Since this can occasionally be frustrating for developers, you can
choose to not install the pre-commit hook locally and instead rely on
the corresponding CI job to catch any problems for you.

[pre_commit]: https://pre-commit.com/

## Ruff

One of the tools used by our pre-commit configuration is [ruff][ruff],
which is both a [linter][linter] and [formatter][formatter]. You can
run these manually with `ruff check` or `ruff format`, but they will
also be run by pre-commit to make sure all is well.

A number of lint rules have automated fixes available for them, which
you can apply by running `ruff check --fix`. However, oftentimes lint
findings indicate more rework would be beneficial than the brute-force
fix supplied, so our pre-commit configuration doesn't supply `--fix` to
encourage you to reevaluate whether doing things a different way would
be more appropriate.

[ruff]: https://docs.astral.sh/ruff/
[linter]: https://docs.astral.sh/ruff/linter/
[formatter]: https://docs.astral.sh/ruff/formatter/