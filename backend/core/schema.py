LANG_PARAMETER = {
    "name": "lang",
    "in": "query",
    "required": False,
    "schema": {
        "type": "string",
        "enum": ["en", "fa"],
        "default": "fa",
    },
    "description": "Language code",
}


def add_global_lang_param(result, generator, request, public):
    for path in result["paths"].values():
        for operation in path.values():
            operation.setdefault("parameters", [])
            operation["parameters"].append(LANG_PARAMETER)
    return result
