from ioctlgw.boards.hhc.hhcn8i8o import HhcN8i8o
from ioctlgw.boards.hiflying.hf6508 import HiFlyingHF6508

MAPPING = {
    "hhc": {
        "hhc-n-8i8o": HhcN8i8o
    },
    "hiflying": {
        "hf6508": HiFlyingHF6508
    }
}


def get_board(identifier):
    parts = identifier.split(".")
    if len(parts) != 2:
        raise Exception("Unexpected number of dots in board identifier.")
    manufacturer = parts[0]
    model = parts[1]
    if manufacturer not in MAPPING.keys():
        raise Exception(f"Manufacturer '{manufacturer}' not found .")
    if model not in MAPPING[manufacturer].keys():
        raise Exception(f"Model '{model}' not found for manufacturer '{manufacturer}'")
    return MAPPING[manufacturer][model]
