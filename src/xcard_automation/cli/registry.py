from . import approve, configure, evaluate, inspect, run

COMMANDS = {
    "approve-proposals": approve,
    "configure": configure,
    "configure-project": configure,
    "evaluate": evaluate,
    "generate": run,
    "inspect": inspect,
    "run": run,
}
