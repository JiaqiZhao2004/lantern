from typing import Any
import json


def pretty_print_response(response: Any) -> None:
    print(json.dumps(response, indent=2, sort_keys=True, default=str))
