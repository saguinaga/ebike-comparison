PREFERRED_FAMILIES = {"white", "light_wood", "sand"}

WHITE_KEYWORDS = {"white", "pearl", "ivory", "cream", "chalk", "snow", "spark white", "ghost white", "pear"}
SAND_KEYWORDS = {"sand", "beige", "tan", "desert", "khaki", "oat", "limestone", "caramel", "baja"}
WOOD_KEYWORDS = {
    "bamboo", "wood", "teak", "walnut", "natural", "driftwood", "maple",
    "vanilla", "glow worm", "diamond dust", "light wood", "light_wood",
}
BLACK_KEYWORDS = {"black", "charcoal", "midnight", "onyx", "matte black"}
GRAY_KEYWORDS = {"gray", "grey", "silver", "slate", "storm", "gunmetal", "graphite", "indigo grey"}
BLUE_KEYWORDS = {"blue", "navy", "indigo", "teal", "aqua", "cosmic", "pacific", "baby blue"}
GREEN_KEYWORDS = {"green", "sage", "mint", "forest", "olive", "glacier mint"}
RED_KEYWORDS = {"red", "rhubarb", "crimson", "burgundy"}
ORANGE_KEYWORDS = {"orange", "mango", "burnt orange", "citrine"}
YELLOW_KEYWORDS = {"yellow", "gold", "lemon"}
PINK_KEYWORDS = {"pink", "rose", "coral"}
PURPLE_KEYWORDS = {"purple", "violet", "aurora", "lavender"}


def normalize_color_family(name: str) -> str:
    lower = (name or "").lower().strip()
    if any(k in lower for k in WHITE_KEYWORDS):
        return "white"
    if lower == "sand" or any(k in lower for k in SAND_KEYWORDS):
        return "sand"
    if any(k in lower for k in WOOD_KEYWORDS):
        return "light_wood"
    if "chrome" in lower:
        return "silver"
    if any(k in lower for k in BLACK_KEYWORDS):
        return "black"
    if any(k in lower for k in GRAY_KEYWORDS):
        return "gray"
    if any(k in lower for k in BLUE_KEYWORDS):
        return "blue"
    if any(k in lower for k in GREEN_KEYWORDS):
        return "green"
    if any(k in lower for k in RED_KEYWORDS):
        return "red"
    if any(k in lower for k in ORANGE_KEYWORDS):
        return "orange"
    if any(k in lower for k in YELLOW_KEYWORDS):
        return "yellow"
    if any(k in lower for k in PINK_KEYWORDS):
        return "pink"
    if any(k in lower for k in PURPLE_KEYWORDS):
        return "purple"
    return "other"


def normalize_colors(colors: list) -> list:
    out = []
    for c in colors or []:
        name = c.get("name", "")
        family = c.get("family") or normalize_color_family(name)
        out.append({**c, "name": name, "family": family})
    return out


def has_preferred_color(colors: list, families: set | None = None) -> bool:
    families = families or PREFERRED_FAMILIES
    return any(c.get("family") in families for c in normalize_colors(colors))


def preferred_colors(colors: list) -> list:
    return [c for c in normalize_colors(colors) if c.get("family") in PREFERRED_FAMILIES]