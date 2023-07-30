# adapted from https://github.com/xImAnton/DockerSetup/blob/main/util.py
import re


def prompt_user(argument_config: dict, cli_args: dict = None) -> dict:
    """
    Prompts the user based on the config

    Example config:
    {
        "arg": "argument",
        "arg2": {
            "prompt": "Argument 2",
            "default": "value",
            "validate": "^regex*or+function$",
            "clean": [chain_of_functions_to_be_executed_on_the_collected_value]
        }
    }

    :param argument_config: argument config that declares how to prompt the specified arguments
    :param cli_args: args that have been declared via the cli args and don't have to be prompted interactively
    :return: dict of arg keys and their collected values
    """
    if not cli_args:
        cli_args = {}

    arguments = {}

    for arg_key, arg_data in argument_config.items():
        if arg_key in cli_args:
            arguments[arg_key] = cli_args[arg_key]
            continue

        prompt = arg_key
        default = None
        clean = []

        def validate(x):
            return x != ""

        if isinstance(arg_data, str):
            prompt = arg_data
        if isinstance(arg_data, dict):
            prompt = arg_data.get("prompt", arg_key)
            default = arg_data.get("default", None)
            clean = arg_data.get("clean", [])

            if callable(clean):
                clean = [clean]

            v = arg_data.get("validate", None)
            if callable(v):
                validate = v
            elif isinstance(v, str):
                validate = re.compile(v).match

        prompt += ": "
        if default:
            prompt += f"({default}) "

        do = True
        value = ""
        while do:
            value = input(prompt.format(**arguments)).strip()
            if value == "" and default is not None:
                value = default.format(**arguments)
            do = not (validate(value) or (value == "" and default == ""))

        for f in clean:
            value = f(value)

        arguments[arg_key] = value
    return arguments


_yesno_vals = ["y", "j", "t", "true", "yes", "1", "+", "ja"], ["n", "f", "false", "no", "nein", "ne", "0", "-"]


def valid_yesno(v: str) -> bool:
    return v in _yesno_vals[0] or v in _yesno_vals[1]


def yesno(v: str, fb: bool = False) -> bool:
    if v in _yesno_vals[0]:
        return True
    if v in _yesno_vals[1]:
        return False
    return fb
