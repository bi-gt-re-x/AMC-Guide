"""Why a miss happened, and what to do about it.

A wrong answer on its own says little: a careless slip on a problem the
student could do and a problem whose method they had never seen look the same
in the history, and they want opposite training. So after a miss the student
says which it was, from five reasons (`REASONS`), and each reason has its own
next step (`next_step`):

    careless  an accuracy drill in the topic: the slip, not the idea, is the gap
    method    the technique's idea, the worked solution, then two problems that
              use the same technique, near this one's rating and within reach
    misread   two wordier problems in the topic, where the question is easy to
              misread, and the habit of rereading what is asked
    time      a timed set in the topic: sprint problems and heavy ones
    guess     a learn set: no way in yet, so start easy, with worked solutions

Over time the reasons add up to a profile (`profile`): which reason comes up
most, and on which stretch of the paper ("mostly careless slips, on #1-10").
The reasons are stored in amc_miss_reasons (data/sql/amc.sql), and joined onto
the attempts they explain, the weakness kinds in backend/amc/planning.py read
them too, so the study plan trains what the student says went wrong.
"""
from collections import Counter
from datetime import date, timedelta

from backend.amc import catalog, engine, pitch, reach, smart
from backend.amc import problems as pb

#: (id, label on the button, what it means, phrase for "your most common reason is ...").
REASONS = [
    ('careless', 'Careless slip', 'I knew how, but slipped: arithmetic, a sign, the wrong letter.', 'careless slips'),
    ('method', 'Didn’t know the method', 'I didn’t see how to start, or which idea to use.', 'not knowing the method'),
    ('misread', 'Misread it', 'I answered a different question from the one asked.', 'misreading the question'),
    ('time', 'Ran out of time', 'I could have got it with more time.', 'running out of time'),
    ('guess', 'Guessed', 'I picked an answer without really working it out.', 'guessing'),
]
IDS = [r[0] for r in REASONS]
LABEL = {r[0]: r[1] for r in REASONS}
MEANS = {r[0]: r[2] for r in REASONS}
PHRASE = {r[0]: r[3] for r in REASONS}
#: What a blank in a sitting can be put down to: nothing was answered, so it
#: was neither a slip, a misreading nor a guess.
BLANK_REASONS = ('method', 'time')

#: The weakness kind (backend/amc/planning.py KINDS) each reason is evidence of.
KIND = {'careless': 'execution', 'misread': 'execution', 'method': 'conceptual', 'guess': 'conceptual',
        'time': 'speed'}

#: The practice set each reason leads to (backend/amc/practice.py MODES).
MODE = {'careless': 'accuracy', 'time': 'timed', 'guess': 'learn'}

#: How far back the profile reads, and the fewest reasons it says anything about.
WINDOW_DAYS = 90
MIN_FOR_PATTERN = 3


def position(problem_id):
    """(number on its paper, the paper's contest) for a problem, (0, its level) when it has no paper."""
    p = pb.get(problem_id)
    found = catalog.sources(problem_id)
    return (found[0]['number'] if found else 0), (p['level'] if p else '')


def band(level, number):
    """The stretch of the paper a problem number is in: '#1–10', '#11–20', '#21–25'
    on the AMC, '#1–5', '#6–10', '#11–15' on the AIME. None without a number."""
    if not number:
        return None
    if level == 'AIME':
        lo = (number - 1) // 5 * 5 + 1
        return '#{}–{}'.format(lo, min(lo + 4, 15))
    if number <= 10:
        return '#1–10'
    return '#11–20' if number <= 20 else '#21–25'


#: Technique names that keep their capital in the middle of a sentence.
_PROPER = {'British', 'Chinese', 'Euclidean', 'Pythagorean', 'Cauchy-Schwarz', 'AM-GM'}


def _lower(name):
    """A technique's name for the middle of a sentence: "casework", but
    "Simon's factoring trick" and "AM-GM" as they are."""
    first = name.split(' ')[0]
    if "'" in first or first in _PROPER:
        return name
    return name[:1].lower() + name[1:]


def _brief(q):
    found = catalog.sources(q['id'])
    return {'id': q['id'], 'short': catalog.short_label(q['id']), 'rating': q.get('rating'),
            'topic_name': catalog.TOPIC_BY_ID[q['topic']]['name'],
            'source': '{} #{}'.format(found[0]['name'], found[0]['number']) if found else 'Drill',
            'preview': engine.plain(q['statement'])[:140]}


def _pick(problem, keep, hist, review_by_id, today, key, n=2):
    """Up to `n` problems like `problem` that `keep` accepts, within reach, best `key` first.

    Never this problem, one already solved, one put on hold as too
    challenging, or one out of reach and harder than this one; problems never
    tried before those tried and still open, and the problem's own contest
    before others."""
    theta, topic_theta = reach.levels(hist, today)
    out = []
    for q in pb.all_problems():
        if q['id'] == problem['id'] or q.get('rating') is None or not keep(q):
            continue
        h = hist.get(q['id'])
        rev = review_by_id.get(q['id'])
        if (h and h['solved']) or (rev and rev['status'] == 'parked'):
            continue
        # Within reach, or no harder than the problem just missed: right after a
        # miss the level estimate dips, but the student was just working there.
        chance = smart.chance(reach.level_for(q, theta, topic_theta), q['rating'])
        if pitch.band(chance) == 'beyond' and q['rating'] > float(problem.get('rating') or 0):
            continue
        out.append(((q['level'] != problem['level'], bool(h), key(q)), q))
    out.sort(key=lambda x: (x[0], x[1]['id']))
    return [_brief(q) for _, q in out[:n]]


def next_step(reason, problem, hist, review_by_id, today):
    """What to do after a miss put down to `reason`: a title, a line of advice,
    and where to go (`action`, a practice set) or what to try (`problems`)."""
    topic = catalog.TOPIC_BY_ID[problem['topic']]
    tech, tech_name = problem['technique'], catalog.technique_name(problem['technique'])
    rating = float(problem.get('rating') or 0)
    step = {'reason': reason, 'label': LABEL[reason], 'idea': None, 'problems': [], 'action': None,
            'more': None}

    def practice(mode, label):
        return {'label': label, 'to': '/practice/{}?mode={}'.format(topic['id'], mode)}

    if reason == 'careless':
        step.update(
            title='Win back the slip',
            body='A slip is the cheapest point there is: you had the method. Before you check an answer, '
                 'redo the last line of arithmetic and make sure the letter you pick is the value you found.',
            action=practice('accuracy', 'Accuracy drill: {}'.format(topic['name'])))
    elif reason == 'method':
        idea = catalog.TECHNIQUE_IDEA.get(tech)
        near = lambda q: abs(q['rating'] - (rating - 0.5))
        same = _pick(problem, lambda q: q['technique'] == tech, hist, review_by_id, today, key=near)
        # Few problems use some techniques: fill up from the same family of
        # ideas in the same topic, so there are always two to try.
        family = catalog.TECHNIQUE_FAMILY.get(tech)
        in_topic = lambda q: q['topic'] == topic['id'] or topic['id'] in q['also']
        taken = {q['id'] for q in same}
        extra = _pick(problem, lambda q: q['id'] not in taken and q['technique'] != tech and in_topic(q)
                      and catalog.TECHNIQUE_FAMILY.get(q['technique']) == family,
                      hist, review_by_id, today, key=near, n=2 - len(same)) if len(same) < 2 else []
        taken |= {q['id'] for q in extra}
        if len(same) + len(extra) < 2:
            extra += _pick(problem, lambda q: q['id'] not in taken and in_topic(q), hist, review_by_id, today,
                           key=near, n=2 - len(same) - len(extra))
        for q in same:
            q['why'] = 'Uses {}'.format(_lower(tech_name))
        for q in extra:
            q['why'] = 'A related idea: {}'.format(_lower(catalog.technique_name(pb.get(q['id'])['technique'])))
        step.update(
            title='Learn the idea, then use it twice',
            body='Read the worked solution below, then try {}.'.format(
                'two problems that use {} too'.format(_lower(tech_name)) if len(same) >= 2 else
                'these two: {} is rare on the papers, so they use it or an idea close to it'.format(_lower(tech_name))),
            idea={'technique': tech, 'name': tech_name, 'text': idea} if idea else None,
            problems=same + extra,
            more={'label': 'Every {} problem'.format(_lower(tech_name)),
                  'to': '/problems?technique={}&sort=difficulty'.format(tech)})
    elif reason == 'misread':
        step.update(
            title='Read for the question',
            body='Before you solve, find what is actually asked: the quantity, the units, words like “not”, '
                 '“least” or “how many”. Read it once more before you answer. These two are wordier, '
                 'so the question is easy to lose.',
            problems=_pick(problem, lambda q: q['topic'] == topic['id'] or topic['id'] in q['also'],
                           hist, review_by_id, today,
                           key=lambda q: (-len(engine.plain(q['statement'])), abs(q['rating'] - rating))))
    elif reason == 'time':
        step.update(
            title='Practice under the clock',
            body='You can do these; the contest gives about three minutes each. A timed set mixes sprint '
                 'problems to bank fast with heavy ones that eat time, so you learn which to start.',
            action=practice('timed', 'Timed set: {}'.format(topic['name'])))
    else:
        step.update(
            title='Start from a worked example',
            body='A guess means there was no way in yet. A learn set starts easy and every problem has a '
                 'worked solution, so the method comes before the speed.',
            action=practice('learn', 'Learn set: {}'.format(topic['name'])))
    return step


def _recent(rows, today, days=WINDOW_DAYS):
    since = (today - timedelta(days=days)).isoformat()
    return [r for r in rows if (r.get('at') or '')[:10] >= since]


def profile(reasons, attempts, today=None):
    """Why this account misses, from the reasons given in the last `WINDOW_DAYS`.

    {'total', 'untagged' (recent wrong answers with no reason yet), 'reasons':
    [{id, label, count, share, band, topic, action}] most common first,
    'headline': a sentence or None, 'top': the most common reason's id, or
    None when there are too few or two lead together}."""
    today = today or date.today()
    recent = _recent(reasons, today)
    total = len(recent)
    untagged = sum(1 for a in _recent(attempts, today, 30)
                   if not a['correct'] and a.get('source') in ('practice', 'review', 'mock') and not a.get('miss_reason'))
    counts = Counter(r['reason'] for r in recent)
    rows = []
    for rid in sorted(counts, key=lambda k: (-counts[k], IDS.index(k))):
        mine = [r for r in recent if r['reason'] == rid]
        bands = Counter(b for b in (band(r['level'], r['number']) for r in mine) if b)
        top_band = None
        if bands:
            b, n = bands.most_common(1)[0]
            if n >= 2 and n * 2 >= sum(bands.values()):
                top_band = b
        topics = Counter(pb.get(r['problem_id'])['topic'] for r in mine if pb.get(r['problem_id']))
        topic_id = topics.most_common(1)[0][0] if topics else None
        topic = catalog.TOPIC_BY_ID.get(topic_id) if topic_id else None
        action = None
        if topic and rid in MODE:
            action = {'label': {'accuracy': 'Accuracy drill', 'timed': 'Timed set', 'learn': 'Learn set'}[MODE[rid]]
                      + ': ' + topic['name'], 'to': '/practice/{}?mode={}'.format(topic['id'], MODE[rid])}
        elif topic and rid == 'method':
            action = {'label': 'Learn the ideas: ' + topic['name'], 'to': '/practice/{}?mode=learn'.format(topic['id'])}
        elif topic and rid == 'misread':
            action = {'label': 'Untimed practice: ' + topic['name'], 'to': '/practice/{}?mode=practice'.format(topic['id'])}
        rows.append({'id': rid, 'label': LABEL[rid], 'phrase': PHRASE[rid], 'count': counts[rid],
                     'share': counts[rid] / total, 'band': top_band,
                     'topic': {'id': topic['id'], 'name': topic['name']} if topic else None, 'action': action})
    headline, top_id = None, None
    if total >= MIN_FOR_PATTERN:
        top = rows[0]
        tied = [r for r in rows if r['count'] == top['count']]
        if len(tied) == 1:
            top_id = top['id']
            headline = 'Your most common reason is {}: {} of your last {} tagged misses{}.'.format(
                top['phrase'], top['count'], total, ', mostly on {}'.format(top['band']) if top['band'] else '')
        else:
            names = [r['phrase'] for r in tied]
            headline = 'No one reason leads yet: {} and {} are level at {} each.'.format(
                ', '.join(names[:-1]), names[-1], top['count'])
    return {'total': total, 'untagged': untagged, 'reasons': rows, 'headline': headline,
            'top': top_id, 'window_days': WINDOW_DAYS,
            'choices': [{'id': i, 'label': LABEL[i], 'means': MEANS[i]} for i in IDS]}


def choices(blank=False):
    """The reasons offered for a miss (for a blank in a sitting, only those that fit one)."""
    return [{'id': i, 'label': LABEL[i], 'means': MEANS[i]} for i in IDS if not blank or i in BLANK_REASONS]
