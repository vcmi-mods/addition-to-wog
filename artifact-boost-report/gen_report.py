import json, html, os

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.expanduser('~/.local/share/vcmi/Mods/addition-to-wog')
BOOST = os.path.join(MOD, 'Mods/wog-artifact-rebalance/Mods/artifact-boost/Content/config')

ru = json.load(open(os.path.join(BOOST, 'translations/russian.json')))
orig = json.load(open(os.path.join(HERE, 'orig_art.json')))

def clean_orig(name):
    """Чистим оригинальный текст: убираем завершающую кавычку, "" -> «»."""
    import re
    s = orig[name]['desc'].strip()
    s = re.sub(r'\.?"\s*$', '', s).strip()
    out, open_q, i = [], True, 0
    while i < len(s):
        if s.startswith('""', i):
            out.append('«' if open_q else '»')
            open_q = not open_q
            i += 2
        else:
            out.append(s[i])
            i += 1
    res = ''.join(out)
    if not res.endswith('.'):
        res += '.'
    return res

def orig_name(name):
    return orig[name]['name']

rows = []
def add(key, status, desc_html, fact_html, era_html, note='', scope='core'):
    ident = key
    rows.append(dict(
        key=ident,
        name=ru.get('artifact.%s.%s.name' % (scope, ident), ident),
        orig_name=orig_name(ident),
        orig_desc=clean_orig(ident),
        status=status,
        desc=desc_html,
        fact=fact_html,
        era=era_html,
        note=note))

C = lambda s: '<code>%s</code>' % s

# ---------------- artifact-boost ----------------
add('birdOfPerception', 'ok',
    'Даёт <b>+5%</b> к навыку Орлиный глаз и <b>6 существ 3-го уровня</b> в неделю в городе, где находится герой.',
    '<li>%s +5%%</li><li>%s → %s, +6/нед., пропагатор %s</li>' % (
        C('LEARN_BATTLE_SPELL_CHANCE'), C('CREATURE_GROWTH'), C('creatureLevel3'), C('TOWN_AND_VISITOR')),
    '6 Королевских грифонов в неделю.<span class="note">Оригинал: еженедельно выдавал 6 Королевских грифонов (5-й уровень). В моде снижено до 6 существ 3-го уровня.</span>')

add('pendantOfLife', 'ok',
    'Даёт вашим войскам иммунитет к заклинанию <b>Волна смерти</b> и приносит <b>24 существа 1-го уровня</b> в неделю в городе, где находится герой.',
    '<li>%s → %s</li><li>%s → %s, +24/нед.</li><li><span class="muted">Бонус здоровья по уровням удалён</span></li>' % (
        C('SPELL_IMMUNITY'), C('deathRipple'), C('CREATURE_GROWTH'), C('creatureLevel1')),
    '24 Феи в неделю.<span class="note">Оригинал: еженедельно 24 Феи. В моде — 24 существа 1-го уровня: Фея относится к 1-му уровню, поэтому у Оплота результат тот же.</span>')

add('pendantOfDeath', 'ok',
    'Даёт вашей нежити иммунитет к заклинанию Уничтожить нежить. Кроме того, все отряды нежити в армии героя получают <b>+2 к атаке и +2 к защите</b>.',
    '<li>%s → %s, лимитер %s</li><li>%s attack <b>+2</b> <span class="muted">(IS_UNDEAD)</span></li><li>%s defence <b>+2</b> <span class="muted">(IS_UNDEAD)</span></li>' % (
        C('SPELL_IMMUNITY'), C('destroyUndead'), C('IS_UNDEAD'), C('PRIMARY_SKILL'), C('PRIMARY_SKILL')),
    '12 Зомби в неделю.<span class="note">Оригинал: еженедельно 12 Зомби. Прирост и +1 скорости убраны; бонусы нежити к атаке и защите — добавка <code>enhanced-artifacts</code>.</span>')

add('pendantOfTotalRecall', 'ok',
    'Иммунитет к «Забывчивости». <b>+10%</b> ко всему опыту героя. В начале боя — «Меткость» эксперта (+6 к атаке стрелков, 50 раундов).',
    '<li>%s → %s</li><li>%s +10%%</li><li>%s → %s, эксперт, 50 раундов</li>' % (
        C('SPELL_IMMUNITY'), C('forgetfulness'), C('HERO_EXPERIENCE_GAIN_PERCENT'),
        C('OPENING_BATTLE_SPELL'), C('precision')),
    '1000 опыта в неделю.<span class="note">Оригинал: еженедельно 1000 опыта. Заменено на постоянный +10% ко всему опыту.</span>')

add('emblemOfCognizance', 'ok',
    'Даёт <b>+15%</b> к навыку Орлиный глаз и приносит <b>2 золота в день за каждое существо</b> в армии героя.',
    '<li>%s: %s +15%%</li><li>%s → %s, <b>val 2</b> × количество существ в армии</li><li>%s: %s, %s — без минимума и максимума</li><li>Оба со %s — копии складываются</li>' % (
        C('instanceBonuses'), C('LEARN_BATTLE_SPELL_CHANCE'), C('GENERATE_RESOURCE'), C('gold'),
        C('updater'), C('TIMES_ARMY_SIZE'), C('stepSize: 1'), C('stacking: ALWAYS')),
    '15 золота за каждое существо в неделю.<span class="note">Оригинал: платил 15 золота за каждого воина раз в неделю. В моде — 2 золота за каждого воина каждый день, что при недельном пересчёте даёт 14 золота против оригинальных 15.</span>')

add('stoicWatchman', 'ok',
    'Даёт <b>+10%</b> к навыку Орлиный глаз и увеличивает радиус обзора <b>на 5</b>.',
    '<li>%s +10%%</li><li>%s +5</li>' % (C('LEARN_BATTLE_SPELL_CHANCE'), C('SIGHT_RADIUS')),
    'Раз в неделю открывал большую область карты.<span class="note">Оригинал: еженедельно раскрывал участок карты. Заменено на постоянный обзор +5.</span>')

add('pendantOfSecondSight', 'ok',
    'Иммунитет к «Слепоте». Бесплатные улучшения в армии героя: Лучники, Лесные эльфы, Гремлины, Гоги, Бехолдеры, Орки, Ящеры, Воздушные элементали. В начале боя «Воздушный щит» эксперта.',
    '<li>%s → %s</li><li>8 × %s: archer→marksman, woodElf→grandElf, gremlin→masterGremlin, gog→magog, beholder→evilEye, orc→orcChieftain, lizardman→lizardWarrior, airElemental→stormElemental</li><li>%s → %s, эксперт, 50 раундов</li>' % (
        C('SPELL_IMMUNITY'), C('blind'), C('SPECIAL_UPGRADE'), C('OPENING_BATTLE_SPELL'), C('airShield')),
    'Раз в неделю улучшал этих существ.<span class="note">Оригинал: еженедельно производил апгрейд стрелков. Заменено на бесплатный апгрейд в любой момент.</span>')

add('pendantOfHoliness', 'ok',
    'Иммунитет к «Проклятию». Обучает героя: Благословение, Лечение, Молитва. В начале боя «Благословение» эксперта.',
    '<li>%s → %s</li><li>3 × %s: bless, cure, prayer</li><li>%s → %s, эксперт, 50 раундов</li>' % (
        C('SPELL_IMMUNITY'), C('curse'), C('SPELL'), C('OPENING_BATTLE_SPELL'), C('bless')),
    'Раз в неделю давал случайное «святое» заклинание.<span class="note">Оригинал: еженедельно случайное святое заклинание. Заменено на постоянное обучение трём.</span>')

add('bootsOfPolarity', 'ok',
    'Повышают сопротивление магии на <b>15%</b> и дают немного очков движения по земле.',
    '<li>%s +15%%</li><li>%s → %s, <b>+300</b></li>' % (C('MAGIC_RESISTANCE'), C('MOVEMENT'), C('heroMovementLand')),
    'Можно было обменять на разовый бонус к движению.<span class="note">Оригинал: обмен на одноразовый прирост движения. Заменено на постоянные +300 — половина от обычных Сапог скорости.</span>')

add('garnitureOfInterference', 'ok',
    'Повышает сопротивление магии на <b>5%</b> и увеличивает уровень владения <b>всеми школами магии на 1</b>.',
    '<li>%s +5%%</li><li>%s → %s, +1</li>' % (C('MAGIC_RESISTANCE'), C('MAGIC_SCHOOL_SKILL'), C('spellSchool.any')),
    'Можно было обменять на магический навык.<span class="note">Оригинал: обмен на изучение школы магии. Заменено на постоянный +1 ко всем школам.</span>')

add('pendantOfDispassion', 'ok',
    'Иммунитет к «Бешенству». <b>+1 Знание</b>. В начале боя «Жажда крови» эксперта.',
    '<li>%s → %s</li><li>%s knowledge +1</li><li>%s → %s, эксперт, 50 раундов</li>' % (
        C('SPELL_IMMUNITY'), C('berserk'), C('PRIMARY_SKILL'), C('OPENING_BATTLE_SPELL'), C('bloodlust')),
    '+1 Знание в неделю.<span class="note">Оригинал: еженедельно +1 Знание. Заменено на постоянный +1.</span>')

add('pendantOfFreeWill', 'ok',
    'Иммунитет к «Гипнозу». Бесплатные улучшения: Крестьяне → Разбойники, Каменные → Железные → Золотые → Алмазные големы. В начале боя «Каменная кожа» эксперта.',
    '<li>%s → %s</li><li>%s: peasant→rogue</li><li>%s: stoneGolem→ironGolem→goldGolem→diamondGolem</li><li>%s → %s, эксперт, 50 раундов</li>' % (
        C('SPELL_IMMUNITY'), C('hypnotize'), C('SPECIAL_UPGRADE'), C('SPECIAL_UPGRADE'),
        C('OPENING_BATTLE_SPELL'), C('stoneSkin')),
    'Раз в неделю улучшал этих существ.<span class="note">Оригинал: еженедельный апгрейд. Заменено на бесплатный апгрейд в любой момент.</span>')

add('diplomatsRing', 'ok',
    'Снижает стоимость капитуляции на <b>10%</b> и приносит <b>500 золота в день</b>.',
    '<li>%s +10%%</li><li>%s → gold, <b>+500/день</b></li>' % (C('SURRENDER_DISCOUNT'), C('GENERATE_RESOURCE')),
    'Можно было обменять на удвоение всех стеков 1-го уровня.<span class="note">Оригинал: обмен на удвоение стеков 1-го уровня. Заменено на постоянный доход 500 золота в день.</span>')

add('surcoatOfCounterpoise', 'ok',
    '+<b>10%</b> сопротивление магии, <b>+1 Знание</b>, <b>+3 обзор</b>, <b>1000 золота в день</b>.',
    '<li>%s +10%%</li><li>%s knowledge +1</li><li>%s +3</li><li>%s → gold, <b>+1000/день</b></li>' % (
        C('MAGIC_RESISTANCE'), C('PRIMARY_SKILL'), C('SIGHT_RADIUS'), C('GENERATE_RESOURCE')),
    'Удваивал эффекты остальных улучшенных артефактов.<span class="note">Оригинал: множитель на другие бустеры. Реализовать нельзя — заменено набором постоянных бонусов.</span>')

add('orbOfVulnerability', 'ok',
    'Устраняет природное сопротивление магии у всех существ на поле боя. <b>1 существо 6-го уровня</b> в неделю в городе, где находится герой. В начале боя «Болезнь» эксперта по всем врагам.',
    '<li>%s ×2 (поле боя + герой врага)</li><li>%s 0, %s, battle-wide</li><li>%s 0, battle-wide</li><li>%s → %s, +1/нед.</li><li>%s → %s, эксперт</li>' % (
        C('NEGATE_ALL_NATURAL_IMMUNITIES'), C('MAGIC_RESISTANCE'), C('INDEPENDENT_MIN'),
        C('SPELL_RESISTANCE_AURA'), C('CREATURE_GROWTH'), C('creatureLevel6'),
        C('OPENING_BATTLE_SPELL'), C('disease')),
    '1 Архимаг + по одному за каждый уровень Мудрости в неделю.<span class="note">Оригинал: число зависело от Мудрости. В моде — 1 существо 6-го уровня в неделю фиксированно.</span>')

add('sphereOfPermanence', 'ok',
    'Даёт вашим войскам иммунитет к заклинанию Развеять магию и приносит <b>2 существа 5-го уровня</b> в неделю в городе, где находится герой.',
    '<li>%s → %s, %s</li><li>%s → %s, %s</li><li>%s → %s, +2/нед., пропагатор %s</li>' % (
        C('SPELL_IMMUNITY'), C('dispel'), C('addInfo: 1'), C('SPELL_IMMUNITY'), C('dispelHelpful'), C('addInfo: 1'),
        C('CREATURE_GROWTH'), C('creatureLevel5'), C('TOWN_AND_VISITOR')),
    '1 Могучий горгон + по одному за каждые 10 Защиты в неделю.<span class="note">Оригинал: прирост зависел от Защиты героя. Заменено на 2 существа 5-го уровня в неделю.</span>')

add('statesmansMedal', 'ok',
    'Снижает стоимость капитуляции на <b>10%</b> и приносит <b>500 золота в день</b>.',
    '<li>%s +10%%</li><li>%s → gold, <b>+500/день</b></li>' % (C('SURRENDER_DISCOUNT'), C('GENERATE_RESOURCE')),
    'Можно было обменять в городе на постройку до трёх зданий.<span class="note">Оригинал: обмен на строительство. Заменено на постоянный доход 500 золота в день.</span>')

add('ambassadorsSash', 'ok',
    'Снижает стоимость капитуляции на <b>10%</b> и приносит <b>500 золота в день</b>.',
    '<li>%s +10%% <span class="muted">(ядро)</span></li><li>%s → gold, <b>+500/день</b></li>' % (
        C('SURRENDER_DISCOUNT'), C('GENERATE_RESOURCE')),
    'Снижала цену выкупа при сдаче в плен.<span class="note">Оригинал: только скидка на капитуляцию. Мод добавил 500 золота в день.</span>')

add('targOfTheRampagingOgre', 'ok',
    'Повышает Защиту на <b>5</b> и увеличивает весь опыт героя на <b>5%</b>.',
    '<li>%s defence +5</li><li>%s +5%%</li>' % (C('PRIMARY_SKILL'), C('HERO_EXPERIENCE_GAIN_PERCENT')),
    'Раз в неделю провоцировал бой с 30 Ограми.<span class="note">Оригинал: еженедельная стычка. Заменено на +5% ко всему опыту героя.</span>')

add('deadMansBoots', 'ok',
    '<b>+15%</b> Некромантия и <b>+2 к скорости</b> всем отрядам нежити в армии героя.',
    '<li>%s +15%%</li><li>%s +2, лимитер %s</li>' % (
        C('UNDEAD_RAISE_PERCENTAGE'), C('STACKS_SPEED'), C('IS_UNDEAD')),
    'Раз в неделю создавал свою копию.<span class="note">Оригинал: еженедельно плодил копии. Прирост существ и апгрейд скелетов убраны — остались некромантия и скорость нежити.</span>')

add('magicWand', 'ok',
    'При атаке вашего героя в бою с шансом <b>25%</b> поражённый вражеский отряд превращается в существ того типа, который его ударил. Суммарное здоровье отряда сохраняется.<br><br>Действует только на живых врагов; преобразованный отряд остаётся на стороне противника.',
    '<li>%s <b>25%%</b></li><li>Подтип %s — количество по сохранённому здоровью</li><li>%s не указан → превращение в атакующего</li><li>%s</li><li>%s — замена всех прежних бонусов</li>' % (
        C('TRANSMUTATION'), C('transmutationPerHealth'), C('addInfo'), C('propagator: ARMY'), C('bonuses#override')),
    'Каждый день случайно заменяла надетые артефакты героя. Пара слотов зависела от того, в какой Misc надет жезл.<span class="note">Оригинал: еженедельная трансформация артефактов, воспроизвести в VCMI нельзя. Заменено на боевую трансмутацию врагов.</span>',
    scope='wake-of-gods.level8units')

boost_rows = list(rows)

# ---------------- сферы стихий ----------------
rows2 = []
add2 = lambda *a, **k: rows2.append((lambda r: (add(*a, **k), rows.pop())[1])(None))

def add_orb(key, desc_html, fact_html, era_html):
    add(key, 'ok', desc_html, fact_html, era_html)
    rows2.append(rows.pop())

add_orb('orbOfTheFirmament',
    '+50% к урону заклинаний магии Воздуха. В начале боя «Оберег Воздуха» эксперта на все войска.',
    '<li>%s → %s, +50 <span class="muted">(ядро)</span></li><li>%s → %s, эксперт <span class="muted">(мод)</span></li>' % (
        C('SPELL_DAMAGE'), C('spellSchool.air'), C('OPENING_BATTLE_SPELL'), C('protectAir')),
    'Базовый эффект ядра без изменений.<span class="note">В WoG отдельного поведения не было; мод добавил боевое заклинание.</span>')

add_orb('orbOfSilt',
    '+50% к урону заклинаний магии Земли. В начале боя «Оберег Земли» эксперта.',
    '<li>%s → %s, +50 <span class="muted">(ядро)</span></li><li>%s → %s, эксперт <span class="muted">(мод)</span></li>' % (
        C('SPELL_DAMAGE'), C('spellSchool.earth'), C('OPENING_BATTLE_SPELL'), C('protectEarth')),
    'Базовый эффект ядра без изменений.')

add_orb('orbOfTempestuousFire',
    '+50% к урону заклинаний магии Огня. В начале боя «Оберег Огня» эксперта.',
    '<li>%s → %s, +50 <span class="muted">(ядро)</span></li><li>%s → %s, эксперт <span class="muted">(мод)</span></li>' % (
        C('SPELL_DAMAGE'), C('spellSchool.fire'), C('OPENING_BATTLE_SPELL'), C('protectFire')),
    'Базовый эффект ядра без изменений.')

add_orb('orbOfDrivingRain',
    '+50% к урону заклинаний магии Воды. В начале боя «Оберег Воды» эксперта.',
    '<li>%s → %s, +50 <span class="muted">(ядро)</span></li><li>%s → %s, эксперт <span class="muted">(мод)</span></li>' % (
        C('SPELL_DAMAGE'), C('spellSchool.water'), C('OPENING_BATTLE_SPELL'), C('protectWater')),
    'Базовый эффект ядра без изменений.')

FLAG = {'ok': 'совпадает', 'warn': 'неточность', 'bad': 'пропуск', 'na': 'без изменений'}

def render(r):
    icon = f"icons/{r['key']}.png"
    icon_html = (f'<div class="articon"><img src="{icon}" alt="{html.escape(r["name"])}"></div>'
                 if os.path.exists(os.path.join(HERE, icon)) else '')
    return f'''      <tr>
        <td class="name"><div class="arthead">{icon_html}<div class="arttext">{html.escape(r['name'])}<span class="id">{r['key']}</span></div></div></td>
        <td class="desc"><span class="flag {r['status']}">{FLAG[r['status']]}</span><br>
          {r['desc']}</td>
        <td><ul>{r['fact']}</ul></td>
        <td class="era">{r['era']}</td>
        <td class="orig"><b>{html.escape(r['orig_name'])}</b><div class="origtext">{html.escape(r['orig_desc'])}</div></td>
      </tr>'''

tpl = open(os.path.join(HERE, 'report_template.html')).read()
out = tpl.replace('{{ROWS_BOOST}}', '\n'.join(render(r) for r in boost_rows))
out = out.replace('{{ROWS_ORBS}}', '\n'.join(render(r) for r in rows2))
out = out.replace('{{COUNT}}', str(len(boost_rows) + len(rows2)))
open(os.path.join(HERE, 'artifact-boost-report.html'), 'w').write(out)
print('строк boost:', len(boost_rows), '| сфер:', len(rows2), '| всего:', len(boost_rows)+len(rows2))
