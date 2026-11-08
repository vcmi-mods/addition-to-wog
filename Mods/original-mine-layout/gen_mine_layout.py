#!/usr/bin/env python3
"""
Генерирует mineLayout.json — патч шаблонов случайных карт VCMI.

Убирает дерево и руду из всех зон, КРОМЕ стартовых (playerStart и cpuStart),
где пара шахт должна стоять возле замка, как в оригинальной Heroes III.
Шахты остальных ресурсов не трогаются.

Запуск:  python3 gen_mine_layout.py
"""

import copy
import glob
import json
import os
import re

RMG = "/usr/share/vcmi/Mods/vcmi/Content/config/rmg"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Content", "config", "mineLayout.json")

# Оба типа зон дают игроку город со стартовой парой шахт.
START_ZONE_TYPES = {"playerStart", "cpuStart"}

# Запрет случайных лесопилок и рудных шахт в нестартовых зонах.
BAN_RANDOM_WOOD_ORE = {"bannedObjects": {"mine": {"sawmill": True, "orePit": True}}}


def strip_comments(text):
    """Убирает // комментарии, не затрагивая содержимое строк."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def load_templates():
    """name -> zones, только активные шаблоны (без папок *unused)."""
    result = {}
    for path in sorted(glob.glob(os.path.join(RMG, "*", "*.json"))):
        if "unused" in path.lower():
            continue
        try:
            data = json.loads(strip_comments(open(path, encoding="utf-8").read()))
        except Exception as e:
            print("SKIP", path, e)
            continue
        for name, tpl in data.items():
            result[name] = copy.deepcopy(tpl.get("zones", {}))
    return result


def source_mines(zones, zone_id, seen=None):
    """Шахты зоны с учётом цепочки minesLikeZone."""
    seen = seen or set()
    zid = str(zone_id)
    if zid in seen:
        return {}
    seen.add(zid)
    zone = zones.get(zid, {})
    nxt = zone.get("minesLikeZone")
    if nxt is not None and nxt != -1:
        return source_mines(zones, nxt, seen)
    return zone.get("mines") or {}


def build_patch(templates):
    patch = {}
    for name, zones in templates.items():
        patched = {}
        for zid, zone in zones.items():
            # Стартовые зоны не трогаем: там пара шахт нужна у замка.
            if zone.get("type") in START_ZONE_TYPES:
                continue

            inherit = zone.get("minesLikeZone")
            if inherit is not None and inherit != -1:
                inherited = source_mines(zones, inherit)
                if not (inherited.get("wood") or inherited.get("ore")):
                    continue  # наследовать нечего убирать
                # Явная копия всех ресурсов источника, кроме дерева и руды.
                explicit = {r: n for r, n in inherited.items()
                            if r not in ("wood", "ore") and n}
                patched[zid] = {
                    "minesLikeZone": -1,
                    "mines": explicit,
                    "customObjects": copy.deepcopy(BAN_RANDOM_WOOD_ORE),
                }
                continue

            own = zone.get("mines") or {}
            if own.get("wood") or own.get("ore"):
                patched[zid] = {
                    "mines": {"wood": 0, "ore": 0},
                    "customObjects": copy.deepcopy(BAN_RANDOM_WOOD_ORE),
                }

        if patched:
            patch["vcmi:" + name] = {"zones": patched}
    return patch


def verify(patch, templates):
    """Ни одна стартовая зона не должна лишиться дерева или руды."""
    problems = []
    for key, val in patch.items():
        name = key.split(":", 1)[1]
        zones = templates[name]
        for zid in val["zones"]:
            if zones[zid].get("type") in START_ZONE_TYPES:
                problems.append((name, zid, zones[zid].get("type")))
    return problems


def main():
    templates = load_templates()
    patch = build_patch(templates)

    problems = verify(patch, templates)
    if problems:
        print("ОШИБКА: патч затрагивает стартовые зоны:", len(problems))
        for p in problems[:10]:
            print("   ", p)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(patch, f, indent="\t", ensure_ascii=False)
        f.write("\n")

    zones_total = sum(len(v["zones"]) for v in patch.values())
    print(f"OK: {OUT}")
    print(f"templates: {len(patch)}, zones patched: {zones_total}")


if __name__ == "__main__":
    main()
