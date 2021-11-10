# NOTE: These variable will be overwritten during the build process by the Github action.

__BUILD__ = "unknown"
__VERSION__ = "localdev"

def build():
    return __BUILD__

def version():
    return __VERSION__