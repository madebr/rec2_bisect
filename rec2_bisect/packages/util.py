import os


def join_environments(*args) -> dict[str, str]:
    result = {k.upper(): v for k,v in os.environ.items()}
    for extra_env in args:
        for k, v in extra_env.items():
            k_upper = k.upper()
            if k_upper in ("INCLUDE", "LIB", "PATH"):
                if k_upper in result:
                    result[k_upper] = v + os.path.pathsep + result[k_upper]
                else:
                    result[k_upper] = v
            else:
                result[k_upper] = v
    return result
