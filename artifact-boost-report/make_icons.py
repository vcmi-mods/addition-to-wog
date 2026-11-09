import os, json, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from def2png import lod_get, parse_def, decode_frame, write_png, LOD

REPORT = os.path.expanduser('~/.local/share/vcmi/Mods/addition-to-wog/artifact-boost-report')
ICONS = os.path.join(REPORT, 'icons')
os.makedirs(ICONS, exist_ok=True)

# индекс артефакта -> имя кадра HrArtNNN.pcx
ARTIFACTS = {
    'birdOfPerception':        63,
    'pendantOfLife':           103,
    'pendantOfDeath':          104,
    'pendantOfTotalRecall':    107,
    'emblemOfCognizance':      65,
    'stoicWatchman':           64,
    'pendantOfSecondSight':    101,
    'pendantOfHoliness':       102,
    'bootsOfPolarity':         59,
    'garnitureOfInterference': 57,
    'pendantOfDispassion':     100,
    'pendantOfFreeWill':       105,
    'diplomatsRing':           67,
    'surcoatOfCounterpoise':   58,
    'orbOfVulnerability':      93,
    'sphereOfPermanence':      92,
    'statesmansMedal':         66,
    'targOfTheRampagingOgre':  16,
    'deadMansBoots':           56,
    'ambassadorsSash':         68,
    'collarOfConjuring':       76,
    'speculum':                52,
    'orbOfTheFirmament':       79,
    'orbOfSilt':               80,
    'orbOfTempestuousFire':    81,
    'orbOfDrivingRain':        82,
}

raw = lod_get(LOD, 'Artifact.def')
palette, blocks = parse_def(raw)
names, offsets = blocks[0]
# ВАЖНО: кадр берётся ПО ПОЗИЦИИ (iconIndex артефакта), а не по имени.
# Имена кадров в Artifact.def сдвинуты относительно позиций (HrArt063 лежит на позиции 68).

ok, fail = [], []
for ident, idx in ARTIFACTS.items():
    out = os.path.join(ICONS, ident + '.png')
    if idx >= len(offsets):
        fail.append((ident, str(idx), 'позиция вне диапазона'))
        continue
    res = decode_frame(raw, offsets[idx], palette)
    if not res:
        fail.append((ident, key, 'декодирование не удалось'))
        continue
    w, h, rgba = res
    write_png(out, w, h, rgba)
    ok.append((ident, w, h, os.path.getsize(out)))

print('Создано иконок:', len(ok))
for ident, w, h, sz in ok:
    print('  %-24s %2dx%-2d  %5d байт' % (ident, w, h, sz))
if fail:
    print('\nПроблемы:')
    for f in fail: print('  ', f)
