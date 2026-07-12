PREFERRED_FAMILIES = {"white", "light_wood", "sand"}

WHITE_KEYWORDS = {"white", "pearl", "ivory", "cream", "chalk", "snow", "spark white"}
SAND_KEYWORDS = {"sand", "beige", "tan", "desert", "khaki", "oat"}
WOOD_KEYWORDS = {
    "bamboo", "wood", "teak", "walnut", "natural", "driftwood", "maple",
    "vanilla", "glow worm", "chrome", "diamond dust", "light wood", "light_wood",
}


def normalize_color_family(name: str) -> str:
    lower = (name or "").lower().strip()
    if any(k in lower for k in WHITE_KEYWORDS):
        return "white"
    if lower == "sand" or any(k in lower for k in SAND_KEYWORDS):
        return "sand"
    if any(k in lower for k in WOOD_KEYWORDS):
        return "light_wood"
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