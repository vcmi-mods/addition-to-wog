#!/usr/bin/env python3
"""
Генератор HTML-отчёта по шаблонам случайных карт VCMI.

Читает шаблоны из установленного VCMI и собирает статическую HTML-страницу
с таблицами и сортировкой по колонкам.

Запуск:
    python3 gen_rmg_report.py
Результат:
    rmg-templates-report.html рядом со скриптом
"""

import json
import os
import re
import unicodedata

VCMI = "/usr/share/vcmi/Mods/vcmi"
RMG = os.path.join(VCMI, "Content", "config", "rmg")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rmg-templates-report.html")

GROUPS = [
    ("hdmod", "HD mod pack",
     "Стандартный набор шаблонов из HD-мода — то, что видят игроки, выбирая карту по имени в лобби. "
     "Дуэльные, командные и большие карты, у большинства есть оригинальное описание автора."),
    ("heroes3", "Heroes III classics",
     "Девять карт из оригинальной Heroes III, перенесённые в генератор: Dwarven Tunnels, Small Ring, "
     "Worlds at War и другие. Их легко узнать по названиям, но структура пересобрана под новый генератор."),
    ("symmetric", "Symmetric",
     "Симметричные шаблоны с классической схемой имён: первое число — игроков, второе — нейтральных городов, "
     "буква — тип связей (S/M/L, B/D/F). Все построены на зеркальной симметрии для честных дуэлей."),
]

# ── Особенности каждого шаблона (написаны вручную по данным конфигов) ────────
NOTES = {
    "Around A Marsh": "Стартовые зоны связаны кольцом вокруг болота в центре. Запрещены Крепость, Сопряжение и Некрополь; монстры — только из Крепости.",
    "Balance M": "Сбалансированный дуэльный шаблон: у обоих игроков одинаковый набор городов, Некрополь и Сопряжение игрокам запрещены и доступны только в нейтральных зонах. Очень высокая плотность сокровищ при низкой максимальной ценности.",
    "Balance L": "То же, что Balance M, но на поверхности и с восемью нейтральными городами. Все города, кроме Замка, разрешены игрокам.",
    "Balance XL": "Расширенная версия Balance: 12 зон, десять нейтральных городов, подземелье. Максимальная ценность сокровища по-прежнему низкая — упор на количество, а не на крупные награды.",
    "Blockbuster M": "Компактная дуэль от Midnight: мало зон, но очень сильная охрана на связях. Некрополь разрешён, Сопряжение запрещено.",
    "Blockbuster L": "Версия Blockbuster на L. Охрана вырастает до 110 000 — пробиваться к центру приходится через очень сильных стражей.",
    "Blockbuster XL": "Самая крупная версия Blockbuster: то же число зон, что и на L, но больше площадь и охрана до 140 000.",
    "Clash of Dragons": "Огромная карта с подземельем и очень богатыми зонами: 16 сокровищниц, ценность до 120 000, охрана до 180 000. Города ограничены Замком, Башней и нейтральными; монстры — из Подземелья, Рампорта и нейтральные.",
    "Coldshadow's Fantasy": "Фэнтези-карта с шестью стартовыми компьютерными игроками и четырьмя соединительными зонами. Разрешены только нейтральные города, но их семнадцать. Максимальная награда — 150 000.",
    "Cube": "Куб с подземным уровнем: каждая зона связана с несколькими соседями, образуя трёхмерную решётку. Слабая охрана (11 000) — карта про маневрирование, а не про пробивание стен.",
    "Diamond": "Ромбовидная симметрия на восемь игроков: у каждого своя зона с восемью связями и нейтральный город. Охрана всего 6000 — быстрый выход на контакт.",
    "Extreme L": "Хардкорная дуэль: запрещены Замок, Сопряжение и Некрополь игрокам, огромная охрана (100 000) и богатые награды до 120 000. По описанию автора — запрещены Полёт, Дверь измерения и Сфера Подавления.",
    "Extreme XL": "Extreme на XL: та же структура, охрана до 140 000, плотность сокровищ ниже — награды крупнее, но их меньше.",
    "Extreme II L": "Переработанный Extreme: меньше зон (10), но больше связей на каждую — плотнее сеть боёв. Те же запреты городов.",
    "Extreme II XL": "Самая тяжёлая версия семейства Extreme: охрана до 160 000 при десяти зонах.",
    "Fear": "Рекорд по плотности сокровищ (187) при полном отсутствии охраны на связях и скромной максимальной награде 35 000. Карта-гонка за мелочью.",
    "Frozen Dragons": "Максимальная охрана среди всех шаблонов — 240 000. Монстры разрешены из всех городов; игрокам запрещены Замок, Сопряжение и Некрополь.",
    "Gimlis Revenge": "Небольшая карта с одной соединительной зоной в центре. Слабая охрана (12 000) и скромные награды (20 000) — учебный темп.",
    "Guerilla": "Партизанская война: 28 зон, 44 связи, 26 сокровищниц, но охрана всего 12 500. Много мелких стычек вместо одной решающей битвы.",
    "Headquarters": "Семь стартовых зон сходятся к двум общим (у них по 8 связей) — это «штаб». Все города, кроме Инферно и Башни, разрешены игрокам.",
    "HyperCube": "Двадцатизонная гиперкубическая решётка поверх подземелья. Минимальная охрана (3000) и самая низкая плотность сокровищ — карта о скорости и позиции.",
    "Jebus Cross": "Классика дуэлей: всего пять зон. Четыре стартовых соединены звездой с одной общей центральной зоной, где десять нейтральных городов и награды до 55 000. Все бои за центр — через охрану 45 000.",
    "Long Run M": "Бег на длинную дистанцию: длинная цепочка зон (у каждой всего 2 связи) и одиннадцать нейтральных городов. Высокая плотность сокровищ, крупные награды до 90 000.",
    "Long Run XL": "Long Run на XL: та же линейная структура, но пятнадцать нейтральных городов и охрана до 60 000.",
    "Marathon XL": "Марафон: 23 зоны, 21 сокровищница, охрана до 280 000. Игрокам запрещены Замок, Сопряжение, Некрополь, Рампорт и Цитадель — остаются Подземелье и Крепость.",
    "Marathon XXL": "Самая большая карта в игре: 350 000 охраны, двадцать три зоны, почти все города разрешены. Абсолютный максимум по масштабу.",
    "Mini Nostalgia": "Уменьшенная Nostalgia на восемь игроков: пятнадцать зон, умеренные награды. Промежуточный вариант между дуэлью и большой картой.",
    "Nostalgia": "Родоначальник семейства: 24 зоны на восемь игроков, 16 сокровищниц, шесть нейтральных городов. Охрана умеренная — 45 000.",
    "Oceans Eleven": "Морская карта (много водных зон) с высокой плотностью сокровищ, но низкой их ценностью (20 000). Охрана слабая — карта про грабёж, а не про штурм.",
    "Panic": "Паника: одиннадцать нейтральных городов при максимальной награде всего 9500. Много мелких сокровищниц, Некрополь — единственный разрешённый игрокам город.",
    "Poor Jebus": "Бедная версия Jebus Cross: та же звезда из пяти зон, но с подземельем и меньшей плотностью сокровищ. Делалась для игры без избытка ресурсов.",
    "Reckless": "Безрассудная: слабая охрана (11 000) при наградах до 60 000. Автор намеренно убрал барьеры — кто первым добежит, тот и забрал.",
    "Roadrunner": "Дорожный бегун: полностью без охраны на связях и с четырнадцатью нейтральными городами. Карта про максимально быстрый захват.",
    "Schaafworld": "Минимум зон — всего три: две стартовые и одна общая. Охрана 80 000 на единственном проходе. Один бой решает всё.",
    "Skirmish M": "Стычка на M: семь зон, одиннадцать связей, умеренная охрана. Монстры ограничены набором из семи фракций.",
    "Skirmish L": "Skirmish на L: та же структура, но награды крупнее (60 000) при той же охране.",
    "Speed 1": "Скоростная карта на шесть игроков: семь зон, всего одна сокровищница, стартовые зоны почти вплотную друг к другу. Замок, Сопряжение и Некрополь недоступны игрокам.",
    "Speed 2": "Дуэльная «скорость»: шесть зон, восемь нейтральных городов, награды не крупнее 9000. Игрокам доступны только Рампорт, Подземелье, Некрополь и Сопряжение.",
    "Spider": "Паучья сеть: восемь стартовых зон по пять связей каждая, 24 зоны, 40 связей. Охрана слабая (12 500) — карта про постоянные перебежки.",
    "SuperSlam": "Для любителей силы: шесть зон, восемь нейтральных городов, охрана 120 000 при скромных наградах. Без подземелья. Игрокам запрещены Замок, Сопряжение и Некрополь.",
    "Triad L": "Триада: три стартовых зоны с пятью связями каждая, десять нейтральных городов. Башня разрешена, Сопряжение и Некрополь — нет.",
    "Triad XL": "Triad XL: строго три игрока, та же структура, чуть сильнее охрана (24 000).",
    "Vortex": "Воронка: четыре стартовых зоны закручены вокруг единственной центральной (у неё 4 связи). Монстры только из Некрополя, игрокам разрешена одна Башня.",

    "Dwarven Tunnels": "Одиннадцать соединительных зон из восемнадцати — настоящий лабиринт туннелей. Десять нейтральных городов при всего трёх сокровищницах.",
    "Golems Aplenty": "Големов в изобилии: играть можно только за Башню. Семь зон, один нейтральный город, скромная охрана.",
    "Meeting in Muzgob": "Встреча в Музгобе: шесть стартовых зон плюс два компьютерных игрока и три соединительных зоны. Ни одного нейтрального города — только свои.",
    "Monk's Retreat": "Обитель монахов: шесть стартовых зон, у каждой свой нейтральный город. Мало сокровищниц (3) — рост идёт через города, а не через награды.",
    "Newcomers": "Новички: играть можно только за Сопряжение, есть один компьютерный игрок. Слабая охрана (6000) — дружелюбная карта для старта.",
    "Ready or Not": "Готов или нет: играть можно только за Рампорт, Инферно или Крепость, и монстры — только из этих фракций плюс нейтральные.",
    "Small Ring": "Малое кольцо: восемь стартовых зон по кругу, без сокровищниц и нейтральных городов. Самая низкая плотность сокровищ (16) и охрана 4500. Чистое PvP.",
    "South of Hell": "Юг Ада: только Инферно, два игрока и один компьютерный. Три соединительных зоны, высокая плотность сокровищ (86).",
    "Worlds at War": "Миры в войне: два игрока против трёх компьютерных, 17 зон, 12 сокровищниц. Высокая плотность наград при умеренной охране — карта про экспансию.",

    "2SM0k": "Симметрия «2 стартовые + 0 нейтральных городов + K-образная схема»: восемь зон, шесть сокровищниц, без нейтральных городов.",
    "2SM2a": "Самая маленькая симметричная карта: всего четыре зоны и две сокровищницы. Быстрая дуэль на поверхности.",
    "2SM2b": "Симметрия 2SM2b: шесть зон, четыре сокровищницы, подземный уровень.",
    "2SM2b(2)": "Версия 2SM2b на четырёх игроков: та же сетка из шести зон, но все они стартовые.",
    "2SM2c": "2SM2c: шесть зон на поверхности, вариант с более плотной сеткой связей, чем у 2SM2b.",
    "2SM2f": "2SM2f: диапазон размеров от S до L — заметно растягивается вместе с опцией размера. Шесть зон, подземелье.",
    "2SM2f(2)": "2SM2f на четверых: все шесть зон стартовые, сокровищниц всего две.",
    "2SM2h": "2SM2h: пять зон, один нейтральный город — вариант с «домом» в центре.",
    "2SM2h(2)": "2SM2h на четверых: четыре стартовые зоны и одна общая центральная без городов.",
    "2SM2i": "2SM2i: два нейтральных города на пять зон — самый «богатый городами» вариант среди малых симметричных.",
    "2SM2i(2)": "2SM2i(2): переработанная версия с одним нейтральным городом и меньшим числом связей.",
    "2SM4d": "2SM4d: десять зон, четыре нейтральных города. Схема с «бутылочным горлышком» — пятнадцать связей на десять зон.",
    "2SM4d(2)": "2SM4d(2): версия на четырёх игроков — четыре стартовые зоны вместо двух.",
    "2SM4d(3)": "2SM4d(3): на шестерых, без нейтральных городов и всего с четырьмя сокровищницами.",
    "3SB0b": "Схема «3 старта, 0 городов, B-вариант»: два игрока и один компьютерный, восемь зон.",
    "3SB0c": "3SB0c: расширенная версия с десятью зонами и густой сетью из четырнадцати связей.",
    "3SM3d": "3SM3d: три старта, четыре соединительные зоны — редкое сочетание, сеть связей плотнее обычного.",
    "4SM0d": "4SM0d: четыре стартовые зоны, один нейтральный город, сильный разброс размеров (S..L+).",
    "4SM0f": "4SM0f: компактная четвёрка на поверхности, без нейтральных городов, слабая охрана 3000.",
    "4SM0g": "4SM0g: тот же размер, что 4SM0f, но связей на четыре больше — зоны переплетены плотнее.",
    "4SM4e": "4SM4e: четыре старта и восемь сокровищниц на поверхности — «четвёрки с избытком наград».",
    "5SB0a": "5SB0a: три игрока и два компьютерных, без нейтральных городов.",
    "5SB0b": "5SB0b: та же компания, но карта компактнее — семь зон и всего две сокровищницы.",
    "6LM10": "6LM10: шесть стартов, пять соединительных зон, 47 связей — самая плотная сеть среди шестиигровых.",
    "6LM10a": "6LM10a: вариант на восемь игроков, без соединительных зон, но с 17 сокровищницами.",
    "6SM0b": "6SM0b: шесть стартов на компактной карте, без нейтральных городов.",
    "6SM0d": "6SM0d: только шесть стартовых зон и ни одной сокровищницы — чистое противостояние игроков.",
    "6SM0e": "6SM0e: 14 зон на шестерых, восемь сокровищниц, слабая охрана.",
    "7SB0b": "7SB0b: шесть игроков и один компьютерный, семь зон, без сокровищниц и городов.",
    "7SB0c": "7SB0c: вариант с меньшим числом связей (8) — зоны изолированнее, чем в 7SB0b.",
    "8MM0e": "8MM0e: восемь стартовых зон почти без сокровищниц — дуэль на восемь игроков в тесном пространстве.",
    "8MM6": "8MM6: 26 зон на восемь игроков, 18 сокровищниц, шесть нейтральных городов.",
    "8MM6a": "8MM6a: фиксированный XL+ вместо диапазона размеров, остальное как в 8MM6.",
    "8SM0c": "8SM0c: восемь стартов на поверхности, пять сокровищниц, без городов.",
    "8SM0f": "8SM0f: компактнее 8SM0c и с подземельем, 12 зон.",
    "8XM12": "8XM12: 33 зоны, двенадцать соединительных и 68 связей — самая разветвлённая карта на восемь игроков.",
    "8XM12a": "8XM12a: вместо соединительных зон — 25 сокровищниц. Тот же масштаб, но награды лежат прямо в зонах.",
    "8XM8": "8XM8: рекорд по числу зон — 48, из них 40 сокровищниц. Малая охрана (6000) и очень много наград: карта про широкую экспансию.",
}


# ── Разбор конфигов ──────────────────────────────────────────────────────────

def strip_comments(text):
    """Убирает // комментарии, не затрагивая содержимое строк."""
    out, i, n = [], 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\":
                if i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
            elif c == '"':
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
    mod = json.load(open(os.path.join(VCMI, "mod.json"), encoding="utf-8"))
    items = []
    for rel in mod.get("templates", []):
        path = os.path.join(VCMI, "Content", rel)
        if not os.path.exists(path):
            alt = path[:-5] + ".json" if path.lower().endswith(".json") else path
            path = alt if os.path.exists(alt) else path
        if not os.path.exists(path):
            print("MISSING:", rel)
            continue
        group = rel.split("/")[2]
        data = json.loads(strip_comments(open(path, encoding="utf-8").read()))
        for name, t in data.items():
            items.append(dict(build(name, group, os.path.basename(rel), t)))
    return items


def build(name, group, file, t):
    zones = t.get("zones", {})
    conns = t.get("connections", [])

    kinds = {}
    for z in zones.values():
        kinds[z.get("type")] = kinds.get(z.get("type"), 0) + 1

    neutral_towns = 0
    towns = set()
    monsters = set()
    density = 0
    tre_max = 0
    for z in zones.values():
        nt = z.get("neutralTowns") or {}
        neutral_towns += sum(v for v in nt.values() if isinstance(v, int))
        for m in z.get("allowedTowns") or []:
            towns.add("+" + m)
        for m in z.get("bannedTowns") or []:
            towns.add("-" + m)
        for m in z.get("allowedMonsters") or []:
            monsters.add(m)
        for m in z.get("bannedMonsters") or []:
            monsters.add("-" + m)
        for ti in z.get("treasure") or []:
            density += ti.get("density", 0)
            tre_max = max(tre_max, ti.get("max", 0))

    guards = [c.get("guard", 0) for c in conns if c.get("guard")]

    return {
        "name": name,
        "group": group,
        "file": file,
        "minSize": t.get("minSize", "?"),
        "maxSize": t.get("maxSize", "?"),
        "players": str(t.get("players", "?")),
        "zones": len(zones),
        "starts": kinds.get("playerStart", 0),
        "cpu": kinds.get("cpuStart", 0),
        "treasureZones": kinds.get("treasure", 0),
        "junction": kinds.get("junction", 0),
        "neutralTowns": neutral_towns,
        "conns": len(conns),
        "guardMax": max(guards) if guards else 0,
        "underground": "u" in str(t.get("maxSize", "")),
        "towns": sorted(towns),
        "monsters": sorted(monsters),
        "density": density,
        "treMax": tre_max,
        "authorNote": t.get("description", ""),
        "note": NOTES.get(name, "—"),
    }


# ── Рендер ──────────────────────────────────────────────────────────────────

SIZE_ORDER = {s: i for i, s in enumerate(
    ["S", "S+", "M", "M+", "L", "L+", "XL", "XL+", "XH", "XH+", "H", "H+", "G", "G+"])}


def size_rank(min_size, max_size):
    return SIZE_ORDER.get(str(max_size), -1)


def players_rank(p):
    """'2-8' -> 2, '2' -> 2, '3' -> 3: сортируем по нижней границе."""
    m = re.match(r"(\d+)", str(p))
    return int(m.group(1)) if m else 0


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def guard_text(v):
    if v == 0:
        return '<span class="zero">нет</span>'
    if v >= 1000:
        return f"{v // 1000}k" if v % 1000 == 0 else f"{v / 1000:.0f}k"
    return str(v)


def towns_text(towns):
    if not towns:
        return '<span class="zero">—</span>'
    parts = []
    for t in towns:
        cls = "plus" if t.startswith("+") else "minus"
        parts.append(f'<span class="{cls}">{esc(t[1:])}</span>')
    return " ".join(parts)


def row(it, idx):
    towns = it["towns"]
    note = esc(it["note"])
    if it["authorNote"]:
        note += f'<span class="author-note">«{esc(it["authorNote"])}»</span>'
    if it["monsters"]:
        note += f'<span class="meta">монстры: {esc(", ".join(it["monsters"]))}</span>'
    return f"""
      <tr data-group="{it['group']}" data-i="{idx}">
        <td class="c-name"><span class="name">{esc(it['name'])}</span><span class="file">{esc(it['file'])}</span></td>
        <td data-v="{size_rank(it['minSize'], it['maxSize'])}" class="c-size">{esc(it['minSize'])} → {esc(it['maxSize'])}</td>
        <td data-v="{players_rank(it['players'])}" class="num">{esc(it['players'])}</td>
        <td data-v="{it['zones']}" class="num">{it['zones']}</td>
        <td data-v="{it['starts']}" class="num">{it['starts']}{f"<span class='cpu'>+{it['cpu']}</span>" if it['cpu'] else ""}</td>
        <td data-v="{it['treasureZones']}" class="num">{it['treasureZones']}</td>
        <td data-v="{it['neutralTowns']}" class="num">{it['neutralTowns']}</td>
        <td data-v="{it['guardMax']}" class="num">{guard_text(it['guardMax'])}</td>
        <td data-v="{it['treMax']}" class="num">{it['treMax']:,}</td>
        <td data-v="{it['density']}" class="num">{it['density']}</td>
        <td data-v="{1 if it['underground'] else 0}" class="c-under">{'есть' if it['underground'] else '—'}</td>
        <td data-v="{it['conns']}" class="num">{it['conns']}</td>
        <td class="c-towns">{towns_text(towns)}</td>
        <td class="c-note">{note}</td>
      </tr>"""


COLUMNS = [
    ("Шаблон", "text"),
    ("Размер", "num"),
    ("Игроки", "num"),
    ("Зоны", "num"),
    ("Старт", "num"),
    ("Сокр.", "num"),
    ("Города", "num"),
    ("Охрана", "num"),
    ("Макс. награда", "num"),
    ("Плотн.", "num"),
    ("Подзем.", "num"),
    ("Связей", "num"),
    ("Города: +разрешены / -запрещены", "text"),
    ("Особенность", "text"),
]


def table_block(items, gid, gtitle, gblurb, idx0):
    rows = []
    for i, it in enumerate(items):
        rows.append(row(it, idx0 + i))
    heads = "".join(
        f'<th class="{typ}" data-type="{typ}">{esc(title)}<span class="arrow"></span></th>'
        for title, typ in COLUMNS
    )
    return f"""
  <section class="group" data-group="{gid}">
    <div class="group-head">
      <h2>{esc(gtitle)} <span class="count">{len(items)}</span></h2>
      <p class="group-blurb">{esc(gblurb)}</p>
    </div>
    <div class="table-scroll">
      <table class="sortable">
        <thead><tr>{heads}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>"""


def main():
    items = load_templates()

    total_zones = sum(i["zones"] for i in items)
    with_under = sum(1 for i in items if i["underground"])
    described = sum(1 for i in items if i["authorNote"])
    with_ban = sum(1 for i in items if re.search(r"ban\s+fly", i["authorNote"], re.I))

    blocks = []
    idx = 0
    for gid, gtitle, gblurb in GROUPS:
        group_items = [i for i in items if i["group"] == gid]
        if not group_items:
            continue
        blocks.append(table_block(group_items, gid, gtitle, gblurb, idx))
        idx += len(group_items)

    css = """
  :root {
    --bg: #f7f5f0;
    --panel: #ffffff;
    --panel-alt: #fbfaf7;
    --border: #e0dbd1;
    --border-strong: #cfc7b8;
    --text: #26241f;
    --muted: #7a7468;
    --gold: #a8813a;
    --ok: #3f7d2e;  --ok-bg: #eef6ea;
    --warn: #a8620f; --warn-bg: #fdf3e5;
    --neg: #b03030; --neg-bg: #fbeded;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 36px 28px 72px;
    background: var(--bg); color: var(--text);
    font-family: "Segoe UI", "Noto Sans", system-ui, -apple-system, sans-serif;
    font-size: 14px; line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1900px; margin: 0 auto; }

  header {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; padding: 26px 30px; margin-bottom: 22px;
  }
  h1 { font-size: 27px; font-weight: 700; margin: 0 0 8px; letter-spacing: -.2px; }
  h1 .accent { color: var(--gold); }
  .subtitle { color: var(--muted); margin: 0; font-size: 13.5px; max-width: 1180px; }

  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
           gap: 12px; margin-bottom: 22px; }
  .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; }
  .stat .n { font-size: 25px; font-weight: 700; color: var(--gold); line-height: 1.15; }
  .stat .l { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; margin-top: 2px; }

  .callout { background: var(--warn-bg); border: 1px solid #e8cfa8; border-left: 3px solid var(--warn);
             border-radius: 10px; padding: 16px 20px; margin-bottom: 26px; font-size: 13.5px; }
  .callout b { color: var(--warn); }
  .callout code { background: #fff; border: 1px solid #e8cfa8; border-radius: 4px;
                  padding: 1px 5px; font-size: 12.5px; }

  .controls { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 26px; }
  .search { flex: 1 1 260px; max-width: 380px; }
  .search input {
    width: 100%; padding: 9px 13px; border: 1px solid var(--border-strong);
    border-radius: 8px; font: inherit; font-size: 13.5px; background: var(--panel); color: var(--text);
  }
  .search input:focus { outline: 2px solid var(--gold); outline-offset: -1px; }
  .pills { display: flex; gap: 7px; flex-wrap: wrap; }
  .pill {
    padding: 7px 14px; border: 1px solid var(--border-strong); border-radius: 999px;
    background: var(--panel); color: var(--muted); font-size: 12.5px; cursor: pointer;
    transition: background .12s, color .12s, border-color .12s;
  }
  .pill:hover { border-color: var(--gold); color: var(--text); }
  .pill.active { background: var(--gold); border-color: var(--gold); color: #fff; font-weight: 600; }

  .group { margin-bottom: 42px; }
  .group-head { margin-bottom: 12px; }
  h2 { font-size: 19px; font-weight: 700; margin: 0 0 5px; }
  h2 .count { font-size: 12px; font-weight: 600; color: var(--muted); background: #f0ece3;
              border-radius: 999px; padding: 2px 9px; vertical-align: 3px; margin-left: 6px; }
  .group-blurb { color: var(--muted); margin: 0; font-size: 13px; max-width: 1100px; }

  .table-scroll { overflow-x: auto; border-radius: 12px; }
  table {
    width: 100%; border-collapse: separate; border-spacing: 0;
    background: var(--panel); border: 1px solid var(--border-strong);
    border-radius: 12px; overflow: hidden; font-size: 13px;
  }
  thead th {
    position: sticky; top: 0; z-index: 2;
    background: #f0ece3; color: #5c5344;
    font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .75px;
    text-align: left; padding: 11px 12px; white-space: nowrap;
    border-bottom: 1px solid var(--border-strong);
    cursor: pointer; user-select: none;
  }
  thead th:hover { background: #e9e3d6; color: var(--text); }
  thead th.num { text-align: right; }
  thead th .arrow { display: inline-block; width: 10px; margin-left: 4px; opacity: .28; }
  thead th .arrow::after { content: "↕"; font-size: 10px; }
  thead th.sorted-asc .arrow, thead th.sorted-desc .arrow { opacity: 1; color: var(--gold); }
  thead th.sorted-asc .arrow::after { content: "↑"; }
  thead th.sorted-desc .arrow::after { content: "↓"; }

  tbody td { padding: 10px 12px; vertical-align: top; border-bottom: 1px solid #eeeae1; }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:nth-child(even) td { background: var(--panel-alt); }
  tbody tr:hover td { background: #fdfaf3; }
  tbody td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }

  .c-name { min-width: 190px; }
  .name { font-weight: 700; color: #1d1c19; display: block; }
  .file { display: block; font-family: ui-monospace, "Cascadia Code", "SF Mono", monospace;
          font-size: 10.5px; color: var(--muted); margin-top: 3px; }
  .c-size { white-space: nowrap; font-size: 12.5px; color: #4a4437; }
  .c-towns { max-width: 230px; font-size: 11.5px; line-height: 1.9; }
  .c-towns .plus { background: var(--ok-bg); color: var(--ok); border-radius: 4px; padding: 1px 5px; }
  .c-towns .minus { background: var(--neg-bg); color: var(--neg); border-radius: 4px; padding: 1px 5px;
                    text-decoration: line-through; }
  .c-note { min-width: 380px; max-width: 620px; font-size: 12.5px; color: #3d3830; }
  .c-note .author-note { display: block; margin-top: 5px; font-style: italic; color: var(--muted); font-size: 11.5px; }
  .c-note .meta { display: block; margin-top: 5px; color: var(--muted); font-size: 11.5px; }
  .c-under { white-space: nowrap; font-size: 12px; color: var(--muted); }
  .zero { color: #b8b0a2; }
  .cpu { color: var(--warn); font-size: 11px; margin-left: 2px; }

  .hidden { display: none !important; }

  footer { color: var(--muted); font-size: 12px; margin-top: 30px; border-top: 1px solid var(--border);
           padding-top: 16px; max-width: 1100px; }
  footer code { background: #efece4; border-radius: 4px; padding: 1px 5px; font-size: 11.5px; }
"""

    js = """
(function () {
  function cellValue(row, colIndex) {
    var td = row.children[colIndex];
    if (!td) return '';
    var raw = td.getAttribute('data-v');
    if (raw !== null) return parseFloat(raw);
    return td.textContent.trim().toLowerCase();
  }

  function sortTable(table, colIndex, type, asc) {
    var tbody = table.tBodies[0];
    var rows = Array.prototype.slice.call(tbody.rows);

    rows.sort(function (a, b) {
      var x = cellValue(a, colIndex);
      var y = cellValue(b, colIndex);
      var res;
      if (type === 'num') {
        res = (isNaN(x) ? -Infinity : x) - (isNaN(y) ? -Infinity : y);
      } else {
        res = String(x).localeCompare(String(y), 'ru');
      }
      return asc ? res : -res;
    });

    rows.forEach(function (r) { tbody.appendChild(r); });
  }

  function setup(table) {
    var ths = table.tHead.rows[0].cells;
    Array.prototype.forEach.call(ths, function (th, idx) {
      th.addEventListener('click', function () {
        var type = th.getAttribute('data-type') || 'text';
        var isAsc = !th.classList.contains('sorted-asc');
        Array.prototype.forEach.call(ths, function (o) {
          o.classList.remove('sorted-asc', 'sorted-desc');
        });
        th.classList.add(isAsc ? 'sorted-asc' : 'sorted-desc');
        sortTable(table, idx, type, isAsc);
      });
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll('table.sortable'), setup);

  // Фильтр по группам и поиск
  var pills = Array.prototype.slice.call(document.querySelectorAll('.pill'));
  var search = document.getElementById('q');
  var sections = Array.prototype.slice.call(document.querySelectorAll('section.group'));
  var activeGroup = 'all';

  function apply() {
    var q = (search.value || '').toLowerCase();
    sections.forEach(function (sec) {
      var gid = sec.getAttribute('data-group');
      var groupOk = activeGroup === 'all' || activeGroup === gid;
      var visible = 0;
      Array.prototype.forEach.call(sec.querySelectorAll('tbody tr'), function (tr) {
        var text = tr.textContent.toLowerCase();
        var show = groupOk && (q === '' || text.indexOf(q) !== -1);
        tr.classList.toggle('hidden', !show);
        if (show) visible++;
      });
      sec.classList.toggle('hidden', visible === 0);
    });
  }

  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      pills.forEach(function (o) { o.classList.remove('active'); });
      p.classList.add('active');
      activeGroup = p.getAttribute('data-group');
      apply();
    });
  });
  search.addEventListener('input', apply);
})();
"""

    groups_html = "".join(blocks)

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Шаблоны случайных карт VCMI 1.7.5</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>Шаблоны случайных карт <span class="accent">VCMI 1.7.5</span></h1>
    <p class="subtitle">
      {len(items)} шаблонов из {len(set(i['file'] for i in items))} файлов, объявленных в <code>mod.json</code>
      мода <code>vcmi</code> — это ровно тот список, который виден в лобби. Данные извлечены
      из <code>Content/config/rmg/*/*.json</code>; папки <code>*unused</code> в отчёт не входят.
      Клик по заголовку колонки сортирует таблицу, повторный клик меняет направление.
    </p>
  </header>

  <div class="stats">
    <div class="stat"><div class="n">{len(items)}</div><div class="l">шаблонов</div></div>
    <div class="stat"><div class="n">{total_zones}</div><div class="l">зон суммарно</div></div>
    <div class="stat"><div class="n">{with_under}</div><div class="l">с подземельем</div></div>
    <div class="stat"><div class="n">{described}</div><div class="l">с описанием автора</div></div>
  </div>

  <div class="callout">
    <b>Запреты Fly / Dimension Door в шаблонах не работают.</b>
    У {with_ban} шаблонов в поле <code>description</code> написано «Ban fly/DD», но ни один файл не содержит
    <code>bannedSpells</code>. Проверены все {len(items)}: полей <code>bannedSpells</code>,
    <code>bannedArtifacts</code>, <code>bannedSkills</code>, <code>settings</code> — ноль вхождений.
    Надпись осталась от эпохи HD-мода и на генерацию в VCMI не влияет: Полёт и Дверь измерения на этих
    картах доступны. Запретить их можно только отдельным модом.
  </div>

  <div class="controls">
    <div class="search"><input id="q" type="search" placeholder="Поиск по названию, городам, описанию…"></div>
    <div class="pills">
      <button class="pill active" data-group="all">все ({len(items)})</button>
      <button class="pill" data-group="hdmod">HD mod pack ({sum(1 for i in items if i['group']=='hdmod')})</button>
      <button class="pill" data-group="heroes3">Heroes III classics ({sum(1 for i in items if i['group']=='heroes3')})</button>
      <button class="pill" data-group="symmetric">Symmetric ({sum(1 for i in items if i['group']=='symmetric')})</button>
    </div>
  </div>

{groups_html}

  <footer>
    <p><b>Как читать размеры.</b> S / M / L / XL / H / G — от маленькой до гигантской;
    суффикс «+» — шаг вверх, «u» — наличие подземного уровня. Диапазон «M → XL+» означает,
    что шаблон подстраивается под выбранный в лобби размер в этих пределах.</p>
    <p><b>Охрана</b> — максимальная сила стража на связях между зонами (0 — связей без охраны нет).
    <b>Плотность</b> — суммарная density сокровищниц по всем зонам.
    <b>Старт</b> — число стартовых зон игроков; «+N» — дополнительные стартовые зоны компьютера.</p>
    <p>Отчёт сгенерирован из установленного VCMI 1.7.5 скриптом <code>gen_rmg_report.py</code>.</p>
  </footer>

</div>
<script>{js}</script>
</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {OUT}")
    print(f"templates: {len(items)}, zones: {total_zones}")


if __name__ == "__main__":
    main()
