import os


def resolve_config_value(value):
    if isinstance(value, dict) and 'env' in value:
        return os.environ[value['env']]
    return value
