from . import configure, evaluate, inspect, run

COMMANDS = {
    "configure": configure,
    "configure-project": configure,
    "evaluate": evaluate,
    "generate": run,
    "inspect": inspect,
    "run": run,
}
