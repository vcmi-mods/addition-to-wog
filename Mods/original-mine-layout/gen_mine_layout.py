#!/usr/bin/env python3
"""
Генерирует mineLayout.json — патч шаблонов случайных карт VCMI.

Правило: дерево и руда должны стоять только рядом с замком.
- В стартовых зонах (playerStart и cpuStart) остаётся РОВНО одна лесопилка
  и ровно один рудник. Движок ставит первую шахту каждого ресурса отдельным
  проходом рядом с центром зоны (у замка), поэтому лишние надо убрать —
  иначе вторая шахта встаёт где попало в пределах зоны.
- Во всех остальных зонах дерево и руда убираются полностью, а случайные
  лесопилки и рудники запрещаются, чтобы не появились из пула наград.
- Шахты остальных ресурсов (ртуть, сера, кристалл, самоцветы, золото)
  не трогаются.

Запуск:  python3 gen_mine_layout.py
"""

import copy
import glob
import json
import os

RMG = "/usr/share/vcmi/Mods/vcmi/Content/config/rmg"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Content", "config", "mineLayout.json")

# Оба типа зон дают игроку город со стартовой парой шахт.
START_ZONE_TYPES = {"playerStart", "cpuStart"}

# Запрет случайных лесопилок и рудных шахт.
BAN_RANDOM_WOOD_ORE = {"bannedObjects": {"mine": {"sawmill": True, "orePit": True}}}

WOOD, ORE = "wood", "ore"


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


def resolve_mines(zones, zone_id, seen=None):
    """Итоговый набор шахт зоны с учётом цепочки minesLikeZone."""
    seen = seen or set()
    zid = str(zone_id)
    if zid in seen:
        return {}
    seen.add(zid)
    zone = zones.get(zid, {})
    nxt = zone.get("minesLikeZone")
    if nxt is not None and nxt != -1:
        return resolve_mines(zones, nxt, seen)
    return copy.deepcopy(zone.get("mines") or {})


def build_patch(templates):
    patch = {}
    for name, zones in templates.items():
        patched = {}

        for zid, zone in zones.items():
            is_start = zone.get("type") in START_ZONE_TYPES
            mines = resolve_mines(zones, zid)

            if is_start:
                # В старте нужна ровно одна лесопилка и один рудник.
                wood, ore = mines.get(WOOD, 0), mines.get(ORE, 0)
                if wood <= 1 and ore <= 1:
                    continue  # уже правильный набор, трогать нечего

                kept = dict(mines)
                kept[WOOD] = 1
                kept[ORE] = 1
                if not wood:
                    kept.pop(WOOD, None)
                if not ore:
                    kept.pop(ORE, None)

                entry = {"mines": kept}
                # Если зона наследовала — отключаем наследование и пишем явно.
                if zone.get("minesLikeZone", -1) != -1:
                    entry["minesLikeZone"] = -1
                patched[zid] = entry
                continue

            # Не стартовая зона: дерево и руду убираем полностью.
            if not (mines.get(WOOD) or mines.get(ORE)):
                continue

            # Пустой объект при мерже ничего не затирает — нужны явные нули.
            explicit = {r: n for r, n in mines.items()
                        if r not in (WOOD, ORE) and n}
            explicit[WOOD] = 0
            explicit[ORE] = 0
            entry = {"mines": explicit,
                     "customObjects": copy.deepcopy(BAN_RANDOM_WOOD_ORE)}
            if zone.get("minesLikeZone", -1) != -1:
                entry["minesLikeZone"] = -1
            patched[zid] = entry

        if patched:
            patch["vcmi:" + name] = {"zones": patched}
    return patch


def verify(patch, templates):
    """Каждая стартовая зона должна получить ровно 1 лесопилку и 1 рудник."""
    problems = []
    for key, val in patch.items():
        name = key.split(":", 1)[1]
        zones = templates[name]
        for zid, entry in val["zones"].items():
            zone = zones[zid]
            is_start = zone.get("type") in START_ZONE_TYPES
            mines = entry.get("mines") or {}

            if is_start:
                wood, ore = mines.get(WOOD, 0), mines.get(ORE, 0)
                if wood != 1 or ore != 1:
                    problems.append((name, zid, "start zone must keep 1/1", wood, ore))
            else:
                if mines.get(WOOD) or mines.get(ORE):
                    problems.append((name, zid, "non-start must have no wood/ore", mines))

    # Ни одна нестартовая зона не должна остаться с деревом/рудой.
    for name, zones in templates.items():
        patched = patch.get("vcmi:" + name, {}).get("zones", {})
        for zid, zone in zones.items():
            if zone.get("type") in START_ZONE_TYPES:
                continue
            final = patched.get(zid, {}).get("mines")
            if final is None:
                final = resolve_mines(zones, zid)
                if final.get(WOOD) or final.get(ORE):
                    problems.append((name, zid, "unpatched non-start still has wood/ore", final))
    return problems


def main():
    templates = load_templates()
    patch = build_patch(templates)

    problems = verify(patch, templates)
    if problems:
        print("ОШИБКА проверки:", len(problems))
        for p in problems[:15]:
            print("   ", p)
        raise SystemExit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(patch, f, indent="\t", ensure_ascii=False)
        f.write("\n")

    zones_total = sum(len(v["zones"]) for v in patch.values())
    start_fixed = sum(
        1 for name, val in patch.items()
        for zid in val["zones"]
        if templates[name.split(":", 1)[1]][zid].get("type") in START_ZONE_TYPES
    )
    print(f"OK: {OUT}")
    print(f"templates: {len(patch)}, zones patched: {zones_total}")
    print(f"start zones trimmed to 1 wood + 1 ore: {start_fixed}")


if __name__ == "__main__":
    main()
