from .generic import parse_generic
from .zooz import parse_zooz
from .firmstrong import parse_firmstrong

PARSERS = {
    "generic": parse_generic,
    "zooz": parse_zooz,
    "firmstrong": parse_firmstrong,
}