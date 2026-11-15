r"""Summit's own solutions to official AMC problems.

An imported paper (backend/amc/official.py) carries the MAA's problem text and
the answer key, and that text lives in the database, not in this repository.
What is written here is ours: for each problem its topics (a person's reading,
which replaces the keyword guess in official.guess_topics), the one idea that
cracks it, the solution as a list of steps (the last naming the answer), and
the trap that costs the most people the points. They are keyed by problem id and stored with
the answer they arrive at, so if a paper is ever re-imported with a different
key the solution is left off rather than shown beside the wrong answer
(`for_problem`). tests/test_amc_official_solutions.py checks that each one ends
on its answer.

Written so far: the 2026 AMC 10A, the 2025 AMC 10A and 10B, and the 2024 AMC 10B
(all but problem 19, whose table is missing). Strings with an
apostrophe in them use r"..." so the apostrophe cannot end the raw string.

Steps are written in the site's one math convention, `$...$` inline.
"""

SOLUTIONS = {
    # ------------------------------------------------------------------ 2026 AMC 10A
    '2026-amc-10a-1': {
        'topics': ['word-problems', 'arithmetic'],
        'answer': 'B',
        'insight': r'Measure all the playing time in EP-lengths.',
        'steps': [
            r'One LP lasts as long as $3$ EPs, so the $33$ LPs last as long as $33 \cdot 3 = 99$ EPs.',
            r'Helena already owns $45$ EPs, so she is short by $99 - 45 = 54$.',
            r'The answer is $\textbf{(B)}\ 54$.',
        ],
        'trap': r'Answering $99$, the total number of EPs she needs, instead of how many more she has to buy.',
    },
    '2026-amc-10a-2': {
        'topics': ['word-problems', 'decimals-fractions'],
        'answer': 'A',
        'insight': r'The $27\%$ is taken on the pre-tax price, but the question asks for a share of what is actually paid.',
        'steps': [
            r'Say the price before tax is $100$. The tax is $27$ and the customer pays $127$.',
            r'The tax is $\frac{27}{127} \approx 0.213$ of the amount paid.',
            r'That rounds to $21\%$. The answer is $\textbf{(A)}\ 21\%$.',
        ],
        'trap': r'Picking $27\%$: that is the tax as a share of the price before tax, not of the total.',
    },
    '2026-amc-10a-3': {
        'topics': ['similar-triangles', 'coordinate-geometry', 'area'],
        'answer': 'D',
        'insight': r'Triangles $FBE$ and $FDA$ are similar with ratio $BE : DA = 1 : 2$, so $F$ sits a third of the way from $B$ to $D$.',
        'steps': [
            r'Put $B = (0,0)$, $C = (24,0)$, $A = (0,24)$ and $D = (24,24)$, so $E = (12, 0)$.',
            r'Line $BD$ is $y = x$ and line $AE$ is $y = 24 - 2x$. They meet where $x = 24 - 2x$, at $F = (8, 8)$.',
            r'Triangle $BEF$ has base $BE = 12$ along the bottom side and height $8$, so its area is $\frac12 \cdot 12 \cdot 8 = 48$.',
            r'The answer is $\textbf{(D)}\ 48$.',
        ],
        'trap': r'Using height $12$, as if $F$ were the midpoint of $\overline{BD}$. It is a third of the way along, not halfway.',
    },
    '2026-amc-10a-4': {
        'topics': ['polygons', 'angle-chasing'],
        'answer': 'A',
        'insight': r'Think in exterior angles: they always add up to $360^\circ$, and a $190^\circ$ angle has an exterior angle of $-10^\circ$.',
        'steps': [
            r'A $150^\circ$ angle turns the walker $30^\circ$; a $190^\circ$ angle turns them $10^\circ$ the other way.',
            r'Pair each $150^\circ$ angle with a $190^\circ$ angle: each pair turns $30^\circ - 10^\circ = 20^\circ$ in all.',
            r'The pairs must turn $360^\circ$, so there are $360 \div 20 = 18$ pairs, which is $36$ sides.',
            r'(Check: $18 \cdot 150^\circ + 18 \cdot 190^\circ = 6120^\circ = 180^\circ \cdot 34$.) The answer is $\textbf{(A)}\ 36$.',
        ],
        'trap': r'Treating the $190^\circ$ angles as if they turned the same way as the others, which gives $360 \div 40 = 9$ pairs.',
    },
    '2026-amc-10a-5': {
        'topics': ['sequences-series', 'statistics'],
        'answer': 'C',
        'insight': r'Adding a number equal to the current mean leaves the mean unchanged, so the sequence freezes at $a_3$.',
        'steps': [
            r'$a_3$ is the mean of $94$ and $190$, which is $142$.',
            r'Now the first three terms have mean $142$, so $a_4 = 142$, and adding $142$ keeps the mean at $142$.',
            r'Every later term is $142$ in the same way, so $a_{10} = 142$.',
            r'The answer is $\textbf{(C)}\ 142$.',
        ],
        'trap': r'Grinding out ten terms by hand as if the mean kept moving, and slipping on the arithmetic.',
    },
    '2026-amc-10a-6': {
        'topics': ['circles', 'right-triangles', 'area'],
        'answer': 'A',
        'insight': r'$16$-$30$-$34$ is twice $8$-$15$-$17$, a right triangle, so its hypotenuse is a diameter.',
        'steps': [
            r'Since $16^2 + 30^2 = 34^2$, the triangle has a right angle, and the side of length $34$ is a diameter. The radius is $17$.',
            r'The diameter cuts the circle into two halves of area $\frac{289\pi}{2}$ each. The half without the triangle is the single largest region, $C$.',
            r'The other half holds the triangle, of area $\frac12 \cdot 16 \cdot 30 = 240$, together with regions $A$ and $B$.',
            r'So $A + B = \frac{289\pi}{2} - 240$. The answer is $\textbf{(A)}\ \frac{289\pi}{2}-240$.',
        ],
        'trap': r'Subtracting the triangle from the whole circle, $289\pi - 240$, which counts region $C$ too.',
    },
    '2026-amc-10a-7': {
        'topics': ['diophantine', 'linear-equations'],
        'answer': 'A',
        'insight': r'Subtracting the equations removes $x$ and leaves $y + z$ alone.',
        'steps': [
            r'Subtract the first equation from the second: $2y + 2z = 10$, so $y + z = 5$ and then $x = 26$.',
            r'Positive integers with $y + z = 5$: $(1,4), (2,3), (3,2), (4,1)$.',
            r'Each gives one triple, so there are $4$. The answer is $\textbf{(A)}\ 4$.',
        ],
        'trap': r'Allowing $y = 0$ or $z = 0$, which gives $6$; the problem says positive integers.',
    },
    '2026-amc-10a-8': {
        'topics': ['word-problems', 'estimation'],
        'answer': 'C',
        'insight': r'The kindest case for the driver is the shortest true distance covered in the longest true time.',
        'steps': [
            r'Rounded to $7$, the distance is at least $6.5$ miles. Rounded to $5$, the time is less than $5.5$ minutes.',
            r'So the trip always needs more than $6.5 \div \frac{5.5}{60} = \frac{780}{11} \approx 70.9$ miles per hour.',
            r'A limit of $70$ can never be enough. A limit of $75$ can: $6.5$ miles in $5.4$ minutes needs only about $72.2$ mph.',
            r'The answer is $\textbf{(C)}\ 75$.',
        ],
        'trap': r'Using the rounded numbers as exact: $7$ miles in $5$ minutes is $84$ mph, which points to $85$.',
    },
    '2026-amc-10a-9': {
        'topics': ['similar-triangles', 'triangles'],
        'answer': 'D',
        'insight': r"The larger triangle cannot reuse the smaller one's $9$ and $12$ in the same places, so the sides shift up by one place.",
        'steps': [
            r'Let the smaller triangle have sides $9$, $12$ and $x$, and let the larger be $k > 1$ times as big, with sides $9k$, $12k$ and $xk$.',
            r"Both $9k > 9$ and $12k > 12$, so the larger triangle's $9$ must be $xk$, and its $12$ must be $9k$. So $k = \frac43$ and $x = \frac{27}{4}$.",
            r'The triangles are $\frac{27}{4}, 9, 12$ and $9, 12, 16$. Both are scalene and real triangles, since $\frac{27}{4} + 9 > 12$.',
            r'The longest side of the larger one is $16$. The answer is $\textbf{(D)}\ 16$.',
        ],
        'trap': r'Making $12$ the hypotenuse of a right triangle or guessing $15$; nothing in the problem says right angle.',
    },
    '2026-amc-10a-10': {
        'topics': ['statistics', 'sequences-series'],
        'answer': 'C',
        'insight': r'Use the sum-of-squares formula for the mean and the middle square for the median, then cancel $n + 1$.',
        'steps': [
            r'The mean of $1^2, 2^2, \dots, n^2$ is $\frac{(n+1)(2n+1)}{6}$. With $n$ odd the median is the middle term, $\left(\frac{n+1}{2}\right)^2$.',
            r'We need $\frac{(n+1)(2n+1)}{6} = 1.32 \cdot \frac{(n+1)^2}{4}$. Dividing by $n + 1$: $\frac{2n+1}{6} = 0.33(n+1)$.',
            r'So $2n + 1 = 1.98n + 1.98$, which gives $0.02n = 0.98$ and $n = 49$.',
            r'(Check: the median is $625$ and the mean is $\frac{50 \cdot 99}{6} = 825 = 1.32 \cdot 625$.) The answer is $\textbf{(C)}\ 49$.',
        ],
        'trap': r'Using the median of $1, 2, \dots, n$ instead of the middle square.',
    },
    '2026-amc-10a-11': {
        'topics': ['gcd-lcm', 'casework'],
        'answer': 'D',
        'insight': r'Either $240$ is the LCM of all six, or $n$ is. Do the two cases separately.',
        'steps': [
            r'The five given numbers have LCM $240$.',
            r'If $240$ is the LCM of all six, then $n$ divides $240$. The only three-digit divisor other than $240$ itself is $120$.',
            r'If $n$ is the LCM, then $n$ is a three-digit multiple of $240$: $480$, $720$ or $960$.',
            r'The sum is $120 + 480 + 720 + 960 = 2280$. The answer is $\textbf{(D)}\ 2280$.',
        ],
        'trap': r'Forgetting the case where $240$ stays the LCM: $480 + 720 + 960 = 2160$ is choice $\textbf{(C)}$.',
    },
    '2026-amc-10a-12': {
        'topics': ['probability', 'combinations'],
        'answer': 'D',
        'insight': r'Read the whole drawing order backward: the socks left over are exactly the run of one color at the very end.',
        'steps': [
            r'Imagine all $200$ socks drawn in a random order. One color runs out exactly when the socks still to come are all the other color.',
            r'So exactly $2$ remain when the last two socks match and the third-to-last does not.',
            r'For "last two red, the one before blue": $\frac{100}{200} \cdot \frac{99}{199} \cdot \frac{100}{198}$. Double it for the two colors.',
            r'$2 \cdot \frac12 \cdot \frac{99}{199} \cdot \frac{100}{198} = \frac{50}{199}$. The answer is $\textbf{(D)}\ \frac{50}{199}$.',
        ],
        'trap': r'Forgetting that the third-to-last sock must be the other color, which gives $\frac{99}{199}$, the chance of at least two left.',
    },
    '2026-amc-10a-13': {
        'topics': ['combinations', 'quadratics'],
        'answer': 'C',
        'insight': r'All $119 + 112 = 231$ handshakes together tell you how many people came.',
        'steps': [
            r'Everyone shook hands once, so $\binom{n}{2} = 231$ and $n = 22$.',
            r'With club sizes $a$ and $b$, the handshakes between clubs number $ab = 112$, and $a + b = 22$.',
            r'$a$ and $b$ are the roots of $t^2 - 22t + 112 = 0$, which are $14$ and $8$.',
            r'The difference is $6$. The answer is $\textbf{(C)}\ 6$.',
        ],
        'trap': r'Working only from the $119$ same-club handshakes, which leaves too many unknowns.',
    },
    '2026-amc-10a-14': {
        'topics': ['triangles', 'inequalities', 'quadratics'],
        'answer': 'B',
        'insight': r'Write out all three triangle inequalities, and do not forget the sides must be positive.',
        'steps': [
            r'$c = 4t + 4 > 0$ forces $t \ge 0$.',
            r'$a < b + c$: $t^2 + 1 < 9t + 11$, so $(t - 10)(t + 1) < 0$ and $t < 10$.',
            r'$b < a + c$: $5t + 7 < t^2 + 4t + 5$, so $(t - 2)(t + 1) > 0$ and $t > 2$. The third, $c < a + b$, always holds.',
            r'That leaves $t = 3, 4, \dots, 9$: $7$ values. The answer is $\textbf{(B)}\ 7$.',
        ],
        'trap': r'Counting $t = 2$ or $t = 10$: there the triangle is flat ($17 = 5 + 12$ and $101 = 57 + 44$) and has no area.',
    },
    '2026-amc-10a-15': {
        'topics': ['recursion', 'gcd-lcm'],
        'answer': 'B',
        'insight': r'Run it backward. Each fraction has exactly one parent, found the way the Euclidean algorithm finds a gcd.',
        'steps': [
            r'A fraction $\frac{p}{q}$ with $p < q$ has children $\frac{p}{p+q}$ and $\frac{q}{p+q}$. So a fraction $\frac{x}{y}$ came from the parent made of $x$ and $y - x$, smaller one on top.',
            r'$\frac{20}{27} \leftarrow \frac{7}{20} \leftarrow \frac{7}{13} \leftarrow \frac{6}{7} \leftarrow \frac{1}{6} \leftarrow \frac{1}{5} \leftarrow \frac14 \leftarrow \frac13 \leftarrow \frac12$.',
            r'That is $8$ steps back to row $0$, so $\frac{20}{27}$ is in row $8$.',
            r'The answer is $\textbf{(B)}\ 8$.',
        ],
        'trap': r'Trying to build the pyramid forward; it doubles every row and you will not reach row $8$ in time.',
    },
    '2026-amc-10a-16': {
        'topics': ['probability', 'casework', 'combinations'],
        'answer': 'D',
        'insight': r'To score low you have to waste balls on a color that has already hit its cap.',
        'steps': [
            r'If at least $3$ reds are drawn, red gives $3$ and the other balls give at least $1$, so the score is at least $4$. It is $4$ only with all $6$ reds and one other ball.',
            r'With $2$ or fewer reds, at least $5$ balls are black or white. The lowest such score is $4$, from $0$ reds, $4$ blacks and $3$ whites, or $0$ reds, $3$ blacks and $4$ whites.',
            r'So the lowest score is $4$. The draws that give it: $6$ reds and $1$ black ($4$ ways), $6$ reds and $1$ white ($4$), $4$ blacks and $3$ whites ($4$), $3$ blacks and $4$ whites ($4$). That is $16$ draws.',
            r'Out of $\binom{14}{7} = 3432$, the probability is $\frac{16}{3432} = \frac{2}{429}$. The answer is $\textbf{(D)}\ \frac{2}{429}$.',
        ],
        'trap': r'Finding only the all-reds draws ($\frac{8}{3432}$) and missing the black-and-white ones.',
    },
    '2026-amc-10a-17': {
        'topics': ['polygons', 'area'],
        'answer': 'C',
        'insight': r'Each square reaches $1$ inward but the center is only $\frac{\sqrt3}{2}$ away, so it pokes past the center by $1 - \frac{\sqrt3}{2}$.',
        'steps': [
            r'Let $d = 1 - \frac{\sqrt3}{2}$. A point inside the squares on two opposite edges lies within $d$ of the center line between them.',
            r'The three pairs of opposite edges give three such bands, and they meet in a regular hexagon whose apothem (center to side) is $d$.',
            r'A regular hexagon with apothem $d$ has area $2\sqrt3\, d^2$. Here $d^2 = \frac74 - \sqrt3$, so the area is $2\sqrt3\left(\frac74 - \sqrt3\right) = \frac{7\sqrt3}{2} - 6$.',
            r'So $a + b + c + d = 7 + 3 + 2 + 6 = 18$. The answer is $\textbf{(C)}\ 18$.',
        ],
        'trap': r'Using $d$ as the side of the small hexagon rather than its apothem.',
    },
    '2026-amc-10a-18': {
        'topics': ['sequences-series', 'recursion', 'divisibility'],
        'answer': 'D',
        'insight': r'Find the fixed point ($4$) and measure every term from it: the distance halves each step.',
        'steps': [
            r'$x = \frac12 x + 2$ when $x = 4$, so $a_k - 4 = \frac12(a_{k-1} - 4)$ and $a_k = 4 + \frac{a_0 - 4}{2^k}$.',
            r'For $a_1, \dots, a_{10}$ to be integers, $2^{10} = 1024$ must divide $a_0 - 4$. For the sequence to decrease, $a_0 > 4$.',
            r'So the smallest $a_0$ is $N = 4 + 1024 = 1028$, whose digits add to $1 + 0 + 2 + 8 = 11$.',
            r'The answer is $\textbf{(D)}\ 11$.',
        ],
        'trap': r'Making $a_0$ itself a multiple of $1024$. It is $a_0 - 4$ that has to be.',
    },
    '2026-amc-10a-19': {
        'topics': ['solid-geometry', 'inequalities'],
        'answer': 'C',
        'insight': r"Only the top corners matter. Put the cover's center on the line of symmetry and balance the two kinds of far corner.",
        'steps': [
            r'From above, the two side-by-side cubes cover $-2 \le x \le 2$, $0 \le y \le 2$, and the third covers $-1 \le x \le 1$, $2 \le y \le 4$. All the tops are at height $2$.',
            r'Center the cover at $(0, u)$ on the table. The farthest points are the corners $(\pm2, 0, 2)$, at squared distance $8 + u^2$, and $(\pm1, 4, 2)$, at $5 + (4 - u)^2$.',
            r'The larger of these is smallest when they are equal: $8 + u^2 = 5 + (4 - u)^2$ gives $u = \frac{13}{8}$.',
            r'Then $R^2 = 8 + \frac{169}{64} = \frac{681}{64}$, so $R = \frac{\sqrt{681}}{8}$. The answer is $\textbf{(C)}\ \frac{\sqrt{681}}{8}$.',
        ],
        'trap': r'Centering the cover in the middle of the whole shape ($u = 2$) instead of balancing the corners.',
    },
    '2026-amc-10a-20': {
        'topics': ['factors-divisors', 'combinations'],
        'answer': 'C',
        'insight': r'$510510$ is the product of the first seven primes, so a box is just a way to split seven primes into three groups.',
        'steps': [
            r'$510510 = 2 \cdot 3 \cdot 5 \cdot 7 \cdot 11 \cdot 13 \cdot 17$.',
            r'Every side is at least $2$, so each side gets at least one prime. The order of the sides does not matter.',
            r'The ways to split $7$ different primes into $3$ unlabeled non-empty groups number $\frac{3^7 - 3 \cdot 2^7 + 3}{6} = \frac{1806}{6} = 301$.',
            r'The answer is $\textbf{(C)}\ 301$.',
        ],
        'trap': r'Counting ordered boxes ($1806$) or letting a side be $1$.',
    },
    '2026-amc-10a-21': {
        'topics': ['casework', 'probability'],
        'answer': 'C',
        'insight': r'There are only $10$ ways to cut a $3 \times 3$ grid into three connected trios, so list them.',
        'steps': [
            r'Two cuts are straight: three rows or three columns. The other eight use L-shapes, and listing them gives $10$ partitions in all.',
            r"A section wins a point only with at least two X's. All $5$ X's are in the top two rows, so two winning sections must share them two and two (or two and three).",
            r'Four partitions earn two points: the three rows; the top-left L with the top-right L; the top row with an L-section through the middle; and the left column with the L through the top-right.',
            r'So $4$ of the $10$ win, a fraction of $\frac{2}{5}$. The answer is $\textbf{(C)}\ \frac{2}{5}$.',
        ],
        'trap': r"Treating mirror images as the same partition. The X's and O's make them different, so all $10$ count.",
    },
    '2026-amc-10a-22': {
        'topics': ['conics', 'transformations'],
        'answer': 'A',
        'insight': r'Stretch the picture so the ellipses become circles: tangent circles have centers exactly two radii apart.',
        'steps': [
            r'Neighbors in a row are $4$ apart and touch, so each ellipse has horizontal semi-axis $2$. Call the vertical semi-axis $b$.',
            r'Shrink widths by $2$ and heights by $b$. Every ellipse becomes a circle of radius $1$, so touching neighbors end up $2$ apart.',
            r'$O = (0,0)$ and $A = (2, 4.5)$ touch, and become $(0,0)$ and $\left(1, \frac{4.5}{b}\right)$. So $1 + \frac{20.25}{b^2} = 4$ and $b = \frac{3\sqrt3}{2}$.',
            r'The major axis is $2b = 3\sqrt3$, so $m + p = 6$. The answer is $\textbf{(A)}\ 6$.',
        ],
        'trap': r'Answering with the semi-axis $\frac{3\sqrt3}{2}$, or reading the $9$ as the major axis.',
    },
    '2026-amc-10a-23': {
        'topics': ['divisibility', 'casework'],
        'answer': 'D',
        'insight': r"Fix $b$, the number of multiples of $3$. That pins the list's length into a short range, and the length decides $a$.",
        'steps': [
            r'A list with exactly $b \ge 1$ multiples of $3$ has length between $3b - 2$ and $3b + 2$, and the even count $a$ can be anything between half the shortest and half the longest length.',
            r'For $b = 2k$ (with $k \ge 1$) the lengths are $6k-2$ to $6k+2$, so $a$ is $3k-1$, $3k$ or $3k+1$: $3$ values. For $b = 2k+1$ the lengths are $6k+1$ to $6k+5$, so $a$ runs from $3k$ to $3k+3$: $4$ values. For $b = 0$ the list has $1$ or $2$ numbers, so $a$ is $0$ or $1$.',
            r'Keep $a \le 100$. $b = 0$ gives $2$; $b = 2, 4, \dots, 66$ give $33 \cdot 3 = 99$; $b = 1, 3, \dots, 65$ give $33 \cdot 4 = 132$; $b = 67$ allows only $a = 99, 100$, so $2$; $b \ge 68$ needs $a \ge 101$.',
            r'In all, $2 + 99 + 132 + 2 = 235$. The answer is $\textbf{(D)}\ 235$.',
        ],
        'trap': r'Treating $a$ and $b$ as independent, or forgetting the edge cases $b = 0$ and $b = 67$.',
    },
    '2026-amc-10a-24': {
        'topics': ['polynomials', 'basic-counting'],
        'answer': 'D',
        'insight': r'Subtract $f(3-\sqrt5)$ from $f(3+\sqrt5)$ and factor out $2\sqrt5$: what is left is a linear condition on the coefficients.',
        'steps': [
            r'Let $f(x) = x^3 + ax^2 + bx + c$, $r = 3 + \sqrt5$ and $s = 3 - \sqrt5$, so $r + s = 6$ and $rs = 4$.',
            r'$f(r) - f(s) = (r - s)\left(r^2 + rs + s^2 + a(r + s) + b\right)$, and $r^2 + rs + s^2 = (r+s)^2 - rs = 32$. So the condition is $32 + 6a + b = 0$.',
            r'$b = -32 - 6a$ must lie in $[-10, 10]$, so $a \in \{-7, -6, -5, -4\}$. The constant $c$ can be any of the $21$ integers.',
            r'That is $4 \cdot 21 = 84$ polynomials. The answer is $\textbf{(D)}\ 84$.',
        ],
        'trap': r'Forgetting that $c$ can be anything, which leaves only the $4$ choices of $a$.',
    },
    '2026-amc-10a-25': {
        'topics': ['inequalities', 'modular-arithmetic', 'invariants'],
        'answer': 'B',
        'insight': r'Room $1$ is the bottleneck: it needs the most nuts and can take at most one a day.',
        'steps': [
            r'After $d$ days there are $210 + 18d$ nuts. If every room ends with $T$, then $20T = 210 + 18d$.',
            r'Room $1$ needs $T - 1$ more nuts at one a day, so $T - 1 \le d$. Substituting, $210 + 18d - 20 \le 20d$, so $d \ge 95$.',
            r'For $T$ to be a whole number, $18d \equiv 10 \pmod{20}$, which means $d$ ends in $5$. So $d = 95$ is allowed, with $T = 96$.',
            r'It can be done: room $k$ is skipped on $k - 1$ days, $190 = 2 \cdot 95$ skips in all, and no room is skipped more than $19$ times, so two skips a day can be spread out without repeating a room. The answer is $\textbf{(B)}\ 95$.',
        ],
        'trap': r'Solving only $20T = 210 + 18d$ for the smallest $d$ ($d = 5$) and ignoring that room $1$ can take one nut a day.',
    },
    # ------------------------------------------------------------------ 2025 AMC 10A
    '2025-amc-10a-1': {
        'topics': ['word-problems', 'linear-equations'],
        'answer': 'E',
        'insight': r"By $2{:}30$ Andy is $8$ miles out, and Betsy closes that gap at $12 - 8 = 4$ miles per hour.",
        'steps': [
            r"When Betsy sets off at $2{:}30$, Andy has ridden for an hour and is $8$ miles from the start.",
            r"After that, Betsy gets $4$ miles per hour further from the start than Andy does, so she draws level after $8 \div 4 = 2$ hours.",
            r"That is $4{:}30$. The answer is $\textbf{(E)}~4{:}30$.",
        ],
        'trap': r"Starting both clocks at $1{:}30$, or adding the two hours to $1{:}30$ instead of $2{:}30$ and answering $3{:}30$.",
    },
    '2025-amc-10a-2': {
        'topics': ['word-problems', 'decimals-fractions'],
        'answer': 'B',
        'insight': r"Follow the peanuts: their share is what tells you how much of the second mix went in.",
        'steps': [
            r"The first mix holds $5$ pounds of peanuts and $2$ pounds of cashews.",
            r"Add $w$ pounds of the second mix. Peanuts: $5 + 0.2w = 0.4(10 + w)$, so $1 = 0.2w$ and $w = 5$.",
            r"Cashews now: $2 + 0.4 \cdot 5 = 4$ pounds. The answer is $\textbf{(B) } 4$.",
        ],
        'trap': r"Answering $5$, the weight of the mix that was added, instead of the cashews.",
    },
    '2025-amc-10a-3': {
        'topics': ['triangles', 'basic-counting'],
        'answer': 'D',
        'insight': r"Either the two equal sides are the $2025$s, or $2025$ is the odd side out and the equal sides are shorter.",
        'steps': [
            r"Equal sides $2025$ and a base $b$ with $1 \le b \le 2025$: always a triangle, since $2025 + 2025 > b$. That is $2025$ triangles, the equilateral one included.",
            r"Base $2025$ with equal sides $a < 2025$: a triangle needs $2a > 2025$, so $a = 1013, \dots, 2024$, which is $1012$ more.",
            r"In all $2025 + 1012 = 3037$. The answer is $\textbf{(D) } 3037$.",
        ],
        'trap': r"Stopping after the first case and answering $2025$.",
    },
    '2025-amc-10a-4': {
        'topics': ['statistics', 'linear-equations'],
        'answer': 'A',
        'insight': r"Each average comes with a team size, and Ash joining changes it by one. That gives two equations.",
        'steps': [
            r"With $s$ students, $12s + x = 14(s + 1)$, so Ash is $x = 2s + 14$.",
            r"The $15 - s$ teachers give $55(15 - s) + x = 52(16 - s)$, so $x = 7 + 3s$.",
            r"$2s + 14 = 7 + 3s$ gives $s = 7$ and $x = 28$. (Check: $\frac{8 \cdot 55 + 28}{9} = 52$.) The answer is $\textbf{(A) } 28$.",
        ],
        'trap': r"Forgetting that the team grows by one when Ash joins, so the new total is $14s$ rather than $14(s+1)$.",
    },
    '2025-amc-10a-5': {
        'topics': ['sequences-series', 'arithmetic'],
        'answer': 'E',
        'insight': r"After the opening $1$, the sequence is made of blocks: the $k$th climbs from $2$ to $k + 1$ and falls back to $1$, $2k$ terms in all.",
        'steps': [
            r"After block $k$, the sequence has $1 + 2(1 + 2 + \dots + k) = 1 + k(k+1)$ terms.",
            r"Block $44$ ends at term $1981$ and block $45$ at term $2071$, so term $2025$ is the $44$th term of block $45$.",
            r"Block $45$ climbs $2, 3, \dots, 46$ over its first $45$ terms, so its $44$th term is $45$. The answer is $\textbf{(E) } 45$.",
        ],
        'trap': r"Dropping the lone $1$ at the very start, which shifts everything by one and lands on $44$.",
    },
    '2025-amc-10a-6': {
        'topics': ['angle-chasing', 'polygons'],
        'answer': 'C',
        'insight': r"Each corner of the hexagon is where rays from two vertices cross, and the two kinds of corner alternate.",
        'steps': [
            r"Take side $BC$. The rays from $B$ and $C$ at $20^\circ$ to $BC$ meet at a point $X$ with $\angle BXC = 180^\circ - 40^\circ = 140^\circ$. The hexagon lies beyond $X$, so its angle there is the vertical angle, $140^\circ$.",
            r"The rays from $B$ and $C$ at $40^\circ$ to $BC$ meet at $Y$ with $\angle BYC = 180^\circ - 80^\circ = 100^\circ$, and the hexagon fills that angle itself.",
            r"Both points lie on the bisector from $A$, inside $A$'s middle angle, so each side gives one corner of each kind: $140^\circ, 100^\circ, \dots$ (and $3 \cdot 140^\circ + 3 \cdot 100^\circ = 720^\circ$, as a hexagon needs).",
            r"The smallest angle is $100^\circ$. The answer is $\textbf{(C) } 100$.",
        ],
        'trap': r"Assuming the hexagon is regular because the figure is symmetric, and answering $120$.",
    },
    '2025-amc-10a-7': {
        'topics': ['polynomials', 'linear-equations'],
        'answer': 'E',
        'insight': r"The remainder on dividing by $x - c$ is the value at $c$.",
        'steps': [
            r"At $x = 1$: $1 + 1 + a + b = 4$, so $a + b = 2$.",
            r"At $x = 2$: $8 + 4 + 2a + b = 6$, so $2a + b = -6$.",
            r"Subtracting, $a = -8$ and $b = 10$, so $b - a = 18$. The answer is $\textbf{(E) } 18$.",
        ],
        'trap': r"Reporting $a - b = -18$ after a sign slip.",
    },
    '2025-amc-10a-8': {
        'topics': ['logic', 'casework'],
        'answer': 'B',
        'insight': r"Call the number of true statements $T$, write when each statement holds, and look for the $T$ that agrees with itself.",
        'steps': [
            r"The four statements hold when $T \ge 1$, $T \ge 2$, $T \le 2$ and $T \le 3$ respectively.",
            r"$T = 3$: statements $1$, $2$ and $4$ hold and $3$ does not. That is exactly three true, so it is consistent.",
            r"Every other value contradicts itself: $T = 0$ makes two true, $T = 1$ makes three true, $T = 2$ makes four true, and $T = 4$ makes statement $4$ false.",
            r"So exactly one statement is false. The answer is $\textbf{(B) } 1$.",
        ],
        'trap': r"Treating statements $1$ and $4$, or $2$ and $3$, as opposites. They are not each other's negations.",
    },
    '2025-amc-10a-9': {
        'topics': ['polynomials', 'graphs-transformations'],
        'answer': 'C',
        'insight': r"Each value $t = 1 - a$ with $f(t) = 25$ gives one shift, so count how often the cubic reaches height $25$.",
        'steps': [
            r"We need $f(1 - a) = 25$. Writing $t = 1 - a$, that is $100t(t-1)(t-2) = 25$, or $t(t-1)(t-2) = \frac14$.",
            r"With $u = t - 1$ the left side is $u^3 - u$, whose peak and dip are $\pm\frac{2}{3\sqrt3} \approx \pm 0.385$, at $u = \mp\frac{1}{\sqrt3}$.",
            r"Since $\frac14$ lies between them, the horizontal line crosses the graph three times. So there are $3$ values of $a$.",
            r"The answer is $\textbf{(C) } 3$.",
        ],
        'trap': r"Assuming a cubic equation has just one real solution.",
    },
    '2025-amc-10a-10': {
        'topics': ['circles', 'area'],
        'answer': 'C',
        'insight': r"The small semicircle's radius is the height of the chord, and Pythagoras ties that to the big radius.",
        'steps': [
            r"Let the big radius be $R$ and the chord's height above $AB$ be $h$. The small semicircle touches the chord, so its radius is $h$.",
            r"From the center, half the chord and the height make a right triangle with hypotenuse $R$: $R^2 = h^2 + 8^2$.",
            r"Shaded area: $\frac{\pi R^2}{2} - \frac{\pi h^2}{2} = \frac{\pi}{2}(R^2 - h^2) = \frac{64\pi}{2} = 32\pi$. The answer is $\textbf{(C) } 32\pi$.",
        ],
        'trap': r"Trying to find where the small semicircle sits; its position makes no difference.",
    },
    '2025-amc-10a-11': {
        'topics': ['sequences-series', 'perfect-powers'],
        'answer': 'E',
        'insight': r"A geometric sequence of integers starting at $1$ is $1, p, p^2, p^3$, so $z$ is a cube, and the arithmetic one needs $3 \mid z - 1$.",
        'steps': [
            r"$z = p^3$ for an integer $p \ge 2$, and $z = 1 + 3d$ for the common difference $d$.",
            r"$p = 2$: $7$ is not a multiple of $3$. $p = 3$: $26$ is not. $p = 4$: $63 = 3 \cdot 21$ is.",
            r"So $z = 64$, $x = 22$, $y = 43$, $p = 4$, $q = 16$, and the sum is $22 + 43 + 64 + 4 + 16 = 149$.",
            r"The answer is $\textbf{(E) } 149$.",
        ],
        'trap': r"Taking $z = 8$ without checking that $1, x, y, 8$ can be arithmetic.",
    },
    '2025-amc-10a-12': {
        'topics': ['basic-counting', 'casework'],
        'answer': 'D',
        'insight': r"Sort the digits $1$ to $9$: $2$ is even and prime, $4, 6, 8$ only even, $3, 5, 7$ only prime, $1, 9$ neither.",
        'steps': [
            r"If a $2$ is used, it is the one even digit and the one prime digit, and the other three come from $\{1, 9\}$: $4 \cdot 2^3 = 32$ codes.",
            r"Otherwise one digit comes from $\{4,6,8\}$, a different one from $\{3,5,7\}$, and two from $\{1,9\}$: $4 \cdot 3$ ways to place them and $3 \cdot 3 \cdot 2 \cdot 2$ ways to choose them, $432$ codes.",
            r"In all $32 + 432 = 464$. The answer is $\textbf{(D) } 464$.",
        ],
        'trap': r"Forgetting that $2$ is both even and prime, which leaves $432$, choice $\textbf{(C)}$.",
    },
    '2025-amc-10a-13': {
        'topics': ['area', 'sequences-series'],
        'answer': 'D',
        'insight': r"Each shaded ring is $k^4$ times the one outside it, so the shaded area is a geometric series.",
        'steps': [
            r"Let the outer square have area $1$. The rings have areas $1 - k^2$ (shaded), $k^2 - k^4$, $k^4 - k^6$ (shaded), and so on.",
            r"Shaded: $(1 - k^2)(1 + k^4 + k^8 + \dots) = \frac{1 - k^2}{1 - k^4} = \frac{1}{1 + k^2}$.",
            r"$\frac{1}{1 + k^2} = \frac{16}{25}$ gives $k^2 = \frac{9}{16}$, so $k = \frac34$. The answer is $\textbf{(D) } \frac{3}{4}$.",
        ],
        'trap': r"Setting $k$ itself equal to $64\%$ and picking $\frac{16}{25}$.",
    },
    '2025-amc-10a-14': {
        'topics': ['probability', 'permutations'],
        'answer': 'B',
        'insight': r"Seat the students first. The four chairs left over form a row, not a circle.",
        'steps': [
            r"Seating four different people in six chairs can be done in $6 \cdot 5 \cdot 4 \cdot 3 = 360$ ways.",
            r"The students take one of the $6$ neighboring pairs, in either order: $12$ ways.",
            r"The other four chairs form a row with $3$ neighboring pairs, so the teachers have $3 \cdot 2 = 6$ ways.",
            r"$\frac{12 \cdot 6}{360} = \frac15$. The answer is $\textbf{(B) } \frac{1}{5}$.",
        ],
        'trap': r"Giving the teachers $4$ neighboring pairs, as if the leftover chairs still went all the way round.",
    },
    '2025-amc-10a-15': {
        'topics': ['coordinate-geometry', 'right-triangles', 'area'],
        'answer': 'A',
        'insight': r"Put $E$ at the origin with $D$ on the $x$-axis. Then $B$ is the point $7$ from $E$ and $1$ from $A$.",
        'steps': [
            r"$AE^2 = AF^2 + AB^2 = 50$ and $AD = 5$, so $DE = 5$. Take $E = (0,0)$, $D = (5,0)$, $A = (5,5)$.",
            r"$B$ satisfies $x^2 + y^2 = 49$ and $(x-5)^2 + (y-5)^2 = 1$. Subtracting, $x + y = 9.8$, and then $xy = 23.52$, so $B = (5.6, 4.2)$ (on the far side of $AD$).",
            r"Line $EB$ is $y = 0.75x$, which meets $AD$ ($x = 5$) at $C = (5, 3.75)$. So $AC = 1.25$, and $B$ is $0.6$ from line $AD$.",
            r"Area $= \frac12 \cdot 1.25 \cdot 0.6 = \frac38$. The answer is $\textbf{(A) } \frac{3}{8}$.",
        ],
        'trap': r"Mixing up the rectangle's sides: $AF = BE = 7$ are the long ones, and $AB = EF = 1$ the short ones.",
    },
    '2025-amc-10a-16': {
        'topics': ['expected-value', 'probability'],
        'answer': 'D',
        'insight': r"There are only three patterns, all together, two and one, or one each, but they are not equally likely.",
        'steps': [
            r"There are $3^3 = 27$ equally likely placements.",
            r"All three in one jar: $3$ ways, most coins $3$. One in each jar: $3! = 6$ ways, most coins $1$. The other $18$ ways split two and one, most coins $2$.",
            r"Expected value: $\frac{3 \cdot 3 + 18 \cdot 2 + 6 \cdot 1}{27} = \frac{51}{27} = \frac{17}{9}$. The answer is $\textbf{(D) } \frac{17}{9}$.",
        ],
        'trap': r"Averaging the three patterns as if each were equally likely: $\frac{3 + 2 + 1}{3} = 2$.",
    },
    '2025-amc-10a-17': {
        'topics': ['modular-arithmetic', 'gcd-lcm'],
        'answer': 'E',
        'insight': r"$N$ divides $273436 - 16$ and $272760 - 15$, and it must be bigger than $16$ to leave a remainder of $16$.",
        'steps': [
            r"$N$ divides $273420$ and $272745$, so it divides their difference, $675 = 3^3 \cdot 5^2$.",
            r"$273420 = 675 \cdot 405 + 45$, so the greatest common divisor is $\gcd(675, 45) = 45$.",
            r"The only divisor of $45$ above $16$ is $45$ itself, so $N = 45$ and its tens digit is $4$. The answer is $\textbf{(E) } 4$.",
        ],
        'trap': r"Forgetting that a remainder of $16$ needs $N > 16$, which leaves several candidates.",
    },
    '2025-amc-10a-18': {
        'topics': ['polynomials', 'quadratics'],
        'answer': 'B',
        'insight': r"For one quadratic, the reciprocals of its roots add to (sum of roots)/(product of roots), and here that is the same for every factor.",
        'steps': [
            r"$kx^2 - 4x - 3$ has discriminant $16 + 12k > 0$, so two real roots, with sum $\frac{4}{k}$ and product $-\frac{3}{k}$.",
            r"Their reciprocals add to $\frac{4/k}{-3/k} = -\frac43$, whatever $k$ is.",
            r"All $4050$ roots: the reciprocals add to $2025 \cdot \left(-\frac43\right) = -2700$, with mean $-\frac{2700}{4050} = -\frac23$.",
            r"The harmonic mean is the reciprocal of that, $-\frac32$. The answer is $\textbf{(B) } -\frac{3}{2}$.",
        ],
        'trap': r"Stopping at the mean of the reciprocals, $-\frac23$, which is choice $\textbf{(E)}$.",
    },
    '2025-amc-10a-19': {
        'topics': ['sequences-series', 'recursion'],
        'answer': 'A',
        'insight': r"Each row's sum doubles, and the second entry drops by $1$ each row. The third entry follows from the second.",
        'steps': [
            r"The new inside entries count every entry above twice except the two ends, $-1$ and $1$, and the new ends add $-1 + 1 = 0$. So sums double: $3, 6, 12, \dots$, and row $n$ sums to $3 \cdot 2^{n-1}$.",
            r"$12288 = 3 \cdot 2^{12}$, so it is row $13$.",
            r"The second entry is $3, 2, 1, \dots$, which is $4 - n$ in row $n$. The third entry grows by the second entry of the row above: $t_n = t_{n-1} + (5 - n)$, starting from $t_1 = 1$.",
            r"$t_{13} = 1 + (3 + 2 + \dots + (-8)) = 1 - 30 = -29$. The answer is $\textbf{(A) } -29$.",
        ],
        'trap': r"Being off by one row: row $12$ gives $-21$, which is choice $\textbf{(B)}$.",
    },
    '2025-amc-10a-20': {
        'topics': ['coordinate-geometry', 'circles'],
        'answer': 'A',
        'insight': r"Tangent to the silo means the line of sight passes exactly $10$ meters from its center.",
        'steps': [
            r"Put the silo's center at the origin. MacDonald is at $(-20, -15)$, and the line of sight is $y + 15 = m(x + 20)$.",
            r"Distance from the origin: $\frac{|20m - 15|}{\sqrt{1 + m^2}} = 10$, which simplifies to $12m^2 - 24m + 5 = 0$, so $m = 1 \pm \frac{\sqrt{21}}{6}$.",
            r"At $x = 20$ the line is at $y = -15 + 40m$, so $g = 15 - 40m$. Only $m = 1 - \frac{\sqrt{21}}{6}$ makes $g > 0$, giving $g = \frac{20\sqrt{21} - 75}{3}$.",
            r"$a + b + c + d = 20 + 21 + 75 + 3 = 119$. The answer is $\textbf{(A) } 119$.",
        ],
        'trap': r"Taking the other tangent line, which puts McGregor north of the silo ($g < 0$).",
    },
    '2025-amc-10a-21': {
        'topics': ['pigeonhole', 'casework'],
        'answer': 'C',
        'insight': r"The largest element $m$ pairs everything else off: $x$ and $m - x$ cannot both be in the set.",
        'steps': [
            r"$\{11, 12, \dots, 20\}$ is sum-free (any two add to at least $22$), and so are the ten odd numbers. So $10$ is possible.",
            r"Let $m$ be the largest element. For every other element $x$, $m - x$ is not in the set, and $m - x \ne x$ (that would make $2x = m$).",
            r"So the other elements and the numbers $m - x$ are two separate groups inside $\{1, \dots, m-1\}$. That gives $2(|S| - 1) \le m - 1 \le 19$, so $|S| \le 10$.",
            r"The answer is $\textbf{(C) } 10$.",
        ],
        'trap': r"Adding $10$ to $\{11, \dots, 20\}$ to reach $11$: $10 + 10 = 20$.",
    },
    '2025-amc-10a-22': {
        'topics': ['circles', 'coordinate-geometry'],
        'answer': 'B',
        'insight': r"The centers of the circles of radius $1$, $2$ and $3$ are $3$, $4$ and $5$ apart: a right triangle you can set on axes.",
        'steps': [
            r"Put the radius-$1$ center at $(0,0)$, the radius-$2$ center at $(3,0)$ and the radius-$3$ center at $(0,4)$.",
            r"The small circle's center $(x, y)$ is $1 + r$, $2 + r$ and $3 + r$ from them. Subtracting pairs of these equations gives $x = 1 - \frac{r}{3}$ and $y = 1 - \frac{r}{2}$.",
            r"Then $\left(1 - \frac r3\right)^2 + \left(1 - \frac r2\right)^2 = (1 + r)^2$, which becomes $23r^2 + 132r - 36 = 0$, that is $(23r - 6)(r + 6) = 0$.",
            r"So $r = \frac{6}{23}$. The answer is $\textbf{(B) } \frac{6}{23}$.",
        ],
        'trap': r"Using the other sign in Descartes' formula, which gives the circle around all three instead.",
    },
    '2025-amc-10a-23': {
        'topics': ['triangles', 'trigonometry'],
        'answer': 'D',
        'insight': r"$P$ is on the altitude, so $BP$ is the hypotenuse of a right triangle with angle $\frac{B}{2}$ at $B$.",
        'steps': [
            r"Law of cosines: $\cos B = \frac{80^2 + 45^2 - 75^2}{2 \cdot 80 \cdot 45} = \frac{2800}{7200} = \frac{7}{18}$.",
            r"The altitude from $C$ meets $AB$ at $H$ with $BH = 45 \cos B = \frac{35}{2}$.",
            r"In right triangle $BHP$, $\angle PBH = \frac{B}{2}$ and $\cos\frac{B}{2} = \sqrt{\frac{1 + 7/18}{2}} = \frac56$. So $BP = \frac{35}{2} \cdot \frac{6}{5} = 21$.",
            r"The answer is $\textbf{(D) } 21$.",
        ],
        'trap': r"Using the bisector's foot on $AC$ (the angle bisector theorem) when $P$ is where the bisector meets the altitude.",
    },
    '2025-amc-10a-24': {
        'topics': ['permutations', 'combinations'],
        'answer': 'C',
        'insight': r"No digit is lower than both its neighbors, so the digits climb to the largest one and then fall.",
        'steps': [
            r"A dip anywhere inside the number would be a digit smaller than both neighbors. So a fair number rises strictly to its largest digit and then falls strictly.",
            r"Choose the set of $k$ digits. The largest is the peak, and each other digit goes either before it (in rising order) or after it (in falling order): $2^{k-1}$ numbers.",
            r"$\sum_{k=1}^{9} \binom{9}{k} 2^{k-1} = \frac{3^9 - 1}{2} = \frac{19682}{2} = 9841$.",
            r"The answer is $\textbf{(C) } 9841$.",
        ],
        'trap': r"Forgetting to halve and answering $3^9 - 1 = 19682$.",
    },
    '2025-amc-10a-25': {
        'topics': ['geometric-probability', 'circles', 'area'],
        'answer': 'A',
        'insight': r"$AP$ is in the middle when $BP < AP < 1$ or $1 < AP < BP$. The line $x = \frac12$ and the circle of radius $1$ around $A$ cut out both regions.",
        'steps': [
            r"Take side $1$ with $A = (0,0)$ and $B = (1,0)$. Then $AP > BP$ exactly when $x > \frac12$, and $AP < 1$ inside the quarter circle around $A$.",
            r"Under the circle, the strip $0 \le x \le \frac12$ is a $30^\circ$ sector plus a triangle, area $\frac{\pi}{12} + \frac{\sqrt3}{8}$. So the quarter circle has $\frac{\pi}{4} - \frac{\pi}{12} - \frac{\sqrt3}{8} = \frac{\pi}{6} - \frac{\sqrt3}{8}$ to the right of $x = \frac12$.",
            r"$BP < AP < 1$ is that right-hand piece. $1 < AP < BP$ is the left half of the square outside the circle: $\frac12 - \frac{\pi}{12} - \frac{\sqrt3}{8}$.",
            r"Together: $\frac12 + \frac{\pi}{12} - \frac{\sqrt3}{4} = \frac{6 + \pi - 3\sqrt3}{12}$, so the sum is $6 + 1 + 3 + 3 + 12 = 25$. The answer is $\textbf{(A) }25$.",
        ],
        'trap': r"Missing the second region, near $D$, where $AP$ is longer than the side but still shorter than $BP$.",
    },
    # ------------------------------------------------------------------ 2025 AMC 10B
    '2025-amc-10b-1': {
        'topics': ['arithmetic', 'word-problems'],
        'answer': 'B',
        'insight': r"Only full mugs count, so round down.",
        'steps': [
            r"$350 \div 20 = 17.5$.",
            r"Half a mug is not a properly brewed mug, so the bag makes $17$. The answer is $\textbf{(B) } 17$.",
        ],
        'trap': r"Rounding $17.5$ up to $18$.",
    },
    '2025-amc-10b-2': {
        'topics': ['modular-arithmetic', 'sequences-series'],
        'answer': 'D',
        'insight': r"The ones digit of $n^2$ depends only on the ones digit of $n$, so the digits repeat every ten.",
        'steps': [
            r"One full cycle is $1, 4, 9, 6, 5, 6, 9, 4, 1, 0$, which adds to $45$.",
            r"$2025 = 202 \cdot 10 + 5$: $202$ full cycles give $9090$, and the last five add $1 + 4 + 9 + 6 + 5 = 25$.",
            r"$9090 + 25 = 9115$. The answer is $\textbf{(D) } 9115$.",
        ],
        'trap': r"Leaving out the five extra squares and answering $9090$.",
    },
    '2025-amc-10b-3': {
        'topics': ['sequences-series', 'binomial-coefficients'],
        'answer': 'D',
        'insight': r"As in Pascal's triangle, each row adds up to twice the row above.",
        'steps': [
            r"The inside entries of a row count every entry above twice, except the two ends, $10$ and $1$, which they count once. The new row's own ends put back $10 + 1$. So each row sums to twice the one before.",
            r"Row $2$ sums to $11$, so row $n$ sums to $11 \cdot 2^{n-2}$, and row $11$ to $11 \cdot 512 = 5632$.",
            r"Its digits add to $5 + 6 + 3 + 2 = 16$. The answer is $\textbf{(D) } 16$.",
        ],
        'trap': r"Being off by one row: $11 \cdot 2^{10} = 11264$ has digit sum $14$, which is choice $\textbf{(C)}$.",
    },
    '2025-amc-10b-4': {
        'topics': ['digits-bases', 'linear-equations'],
        'answer': 'A',
        'insight': r"Write both numbers out and remember that a base-seven digit is at most $6$.",
        'steps': [
            r"$7a + b = 9b + a$, so $6a = 8b$, or $3a = 4b$.",
            r"With digits below $7$, the only nonzero solution is $a = 4$, $b = 3$. (Check: $43_7 = 31 = 34_9$.)",
            r"$a + b = 7$. The answer is $\textbf{(A)}~7$.",
        ],
        'trap': r"Taking $a = 8$, $b = 6$, which is not a base-seven digit pair, and answering $14$.",
    },
    '2025-amc-10b-5': {
        'topics': ['circles', 'angle-chasing'],
        'answer': 'C',
        'insight': r"The obtuse angle at $B$ says the arc $AC$ away from $B$ is $260^\circ$, so the central angle $AOC$ is $100^\circ$.",
        'steps': [
            r"An inscribed angle is half its arc: $\angle B = 130^\circ$ cuts off an arc $AC$ of $260^\circ$ on the side away from $B$.",
            r"The other arc $AC$, through $B$, is $100^\circ$, so $\angle AOC = 100^\circ$.",
            r"$OA = OC$, so $\angle CAO = \frac{180^\circ - 100^\circ}{2} = 40^\circ$. The side lengths are not needed. The answer is $\textbf{(C)}~40$.",
        ],
        'trap': r"Reaching for $AB = 10$ and $AC = 18$ and the law of sines; they play no part.",
    },
    '2025-amc-10b-6': {
        'topics': ['coordinate-geometry', 'area', 'quadratics'],
        'answer': 'C',
        'insight': r"The region below the line is a trapezoid, and the piece left of $x = a$ is one too.",
        'steps': [
            r"Below the line, from $x = 0$ to $x = 2$, the heights are $1$ and $\frac53$, so the area is $\frac{1 + 5/3}{2} \cdot 2 = \frac83$.",
            r"Left of $x = a$ the area is $a + \frac{a^2}{6}$. Setting that to $\frac43$ gives $a^2 + 6a - 8 = 0$.",
            r"$a = \sqrt{17} - 3$, so $s + t = 20$. The answer is $\textbf{(C) }20$.",
        ],
        'trap': r"Cutting at $x = 1$ as if the region were a rectangle.",
    },
    '2025-amc-10b-7': {
        'topics': ['right-triangles', 'word-problems'],
        'answer': 'C',
        'insight': r"Each route is a straight walk to a gate plus a walk along the fence, so set the two totals equal.",
        'steps': [
            r"West gate: $\sqrt{8^2 + 15^2} = 17$ to the gate, then $8 + x$ back along the fence, $x + 25$ in all.",
            r"East gate (at $x + 9$): $\sqrt{(x+9)^2 + 15^2}$ to the gate, then $9$ back.",
            r"$\sqrt{(x+9)^2 + 225} = x + 16$. Squaring gives $306 = 14x + 256$, so $x = \frac{25}{7} = 3\frac47$. The answer is $\textbf{(C)}~3\frac47$.",
        ],
        'trap': r"Forgetting the walk back along the fence from the gate to the box.",
    },
    '2025-amc-10b-8': {
        'topics': ['divisibility', 'digits-bases'],
        'answer': 'C',
        'insight': r"The total in cents, the five-digit number $ABBBA$, must divide evenly by $36$: by $4$ and by $9$.",
        'steps': [
            r"Divisible by $9$: $2A + 3B$ is a multiple of $9$, which forces $3 \mid A$.",
            r"Divisible by $4$: the last two digits $BA$ make a multiple of $4$, so $A$ is even. With $A \ne 0$, that leaves $A = 6$.",
            r"Then $12 + 3B$ is a multiple of $9$, so $B \in \{2, 5, 8\}$, and only $56$ is a multiple of $4$. So $B = 5$: $\$655.56 = 36 \cdot \$18.21$.",
            r"$A + B = 11$. The answer is $\textbf{(C)}~11$.",
        ],
        'trap': r"Requiring a whole-dollar price per shirt; it only needs to be whole cents.",
    },
    '2025-amc-10b-9': {
        'topics': ['inequalities', 'casework', 'parity'],
        'answer': 'C',
        'insight': r"Rename the three expressions $a = -x+y+z$, $b = x-y+z$, $c = x+y-z$. The system becomes very simple.",
        'steps': [
            r"The conditions say $a, b, c \le 2$ and $a + b + c = x + y + z \ge 2$. Since $x = \frac{b+c}{2}$ and so on, the triple is integral exactly when $a, b, c$ have the same parity.",
            r"All even (so each is at most $2$): $(2,2,2)$, and the orderings of $(2,2,0)$, $(2,2,-2)$ and $(2,0,0)$. That is $1 + 3 + 3 + 3 = 10$.",
            r"All odd (each at most $1$): only $(1,1,1)$ has sum at least $2$.",
            r"$10 + 1 = 11$ triples. The answer is $\textbf{(C)}\ 11$.",
        ],
        'trap': r"Mixing parities, for example $(2, 1, 0)$, which gives non-integer $x, y, z$.",
    },
    '2025-amc-10b-10': {
        'topics': ['polynomials', 'divisibility'],
        'answer': 'A',
        'insight': r"Both cubics share the factors $(n + 1)$ and $(n - 4)$. Cancel them, and keep in mind where $g$ is $0$.",
        'steps': [
            r"$f(n) = (n+1)(n-2)(n-4)$ and $g(n) = (n+1)(n-3)(n-4)$.",
            r"For $n \ne -1, 4$: $\frac{f}{g} = \frac{n-2}{n-3} = 1 + \frac{1}{n-3}$, an integer only when $n - 3 = \pm 1$.",
            r"$n = 4$ makes $g = 0$, so only $n = 2$ works (the quotient is $0$). The sum is $2$. The answer is $\textbf{(A)}~2$.",
        ],
        'trap': r"Counting $n = 4$, where the fraction is undefined, and answering $6$.",
    },
    '2025-amc-10b-11': {
        'topics': ['probability', 'permutations'],
        'answer': 'B',
        'insight': r"Compared with Monday, Tuesday's assignment is just a random rearrangement, and we want exactly two students to stay put.",
        'steps': [
            r"Choose the two students who see the same tutor: $\binom62 = 15$ ways.",
            r"The other four must all see a different tutor from Monday: $4$ items with none in place, $9$ ways.",
            r"$\frac{15 \cdot 9}{6!} = \frac{135}{720} = \frac{3}{16}$. The answer is $\textbf{(B) } \frac{3}{16}$.",
        ],
        'trap': r"Letting the other four do anything ($15 \cdot 4!$), which counts the cases where more than two stay put.",
    },
    '2025-amc-10b-12': {
        'topics': ['area', 'circles', 'polygons'],
        'answer': 'C',
        'insight': r"In the hexagon and the rhombus, each disk is the incircle of one of the equilateral triangles the shape splits into.",
        'steps': [
            r"An equilateral triangle of side $s$ has inradius $\frac{s}{2\sqrt3}$, so its incircle fills $\frac{\pi s^2/12}{\sqrt3 s^2/4} = \frac{\pi}{3\sqrt3}$ of it.",
            r"The hexagon is six equilateral triangles and the rhombus is two, each with its disk as incircle. So $H = R = \frac{\pi}{3\sqrt3} \approx 0.60$.",
            r"In the triangle, use disks of radius $1$: the side is $2 + 2\sqrt3$, the area is $6 + 4\sqrt3$, and $T = \frac{3\pi}{6 + 4\sqrt3} \approx 0.73$.",
            r"So $H = R < T$. The answer is $\textbf{(C)}\ H=R<T$.",
        ],
        'trap': r"Guessing that more disks pack better, and choosing $H$ as the largest.",
    },
    '2025-amc-10b-13': {
        'topics': ['right-triangles', 'coordinate-geometry'],
        'answer': 'A',
        'insight': r"Coordinates make this quick: put the right angle at the origin and the short leg on the $x$-axis.",
        'steps': [
            r"Take $C = (0,0)$, $B = (1,0)$ and $A = (0, \sqrt3)$. The altitude from $C$ meets $AB$ at $H = \left(\frac34, \frac{\sqrt3}{4}\right)$, on the line $y = \frac{x}{\sqrt3}$.",
            r"The median to the short side runs from $A$ to $\left(\frac12, 0\right)$, through the points $\left(\frac s2, \sqrt3(1 - s)\right)$.",
            r"It meets the altitude when $\sqrt3(1 - s) = \frac{s}{2\sqrt3}$, so $s = \frac67$, at $\left(\frac37, \frac{\sqrt3}{7}\right)$, which is $\frac47$ of the way from $C$ to $H$.",
            r"The pieces are $\frac47$ and $\frac37$ of the altitude, so $\frac{x}{x+y} = \frac37$. The answer is $\textbf{(A)}~\frac 37$.",
        ],
        'trap': r"Using the median to the hypotenuse, which runs from the right angle instead.",
    },
    '2025-amc-10b-14': {
        'topics': ['probability', 'combinations'],
        'answer': 'C',
        'insight': r"The captains are the three tallest exactly when those three land in different groups.",
        'steps': [
            r"Follow only the three tallest. Wherever the tallest goes, the second tallest lands in another group with probability $\frac68$.",
            r"The third tallest then avoids both of those groups with probability $\frac37$.",
            r"$\frac68 \cdot \frac37 = \frac{9}{28}$. The answer is $\textbf{(C) } \frac9{28}$.",
        ],
        'trap': r"Using $\frac23 \cdot \frac13$, as if each athlete picked a color independently. The bands run out.",
    },
    '2025-amc-10b-15': {
        'topics': ['sequences-series', 'decimals-fractions'],
        'answer': 'D',
        'insight': r"Factor the denominator as $k(k+2)(k+4)$ and split it into simple fractions that telescope.",
        'steps': [
            r"$\frac{1}{k(k+2)(k+4)} = \frac18\left(\frac1k - \frac{2}{k+2} + \frac{1}{k+4}\right)$.",
            r"Summed over all $k$, each $\frac1j$ with $j \ge 5$ appears as $1 - 2 + 1 = 0$ times. What is left is $1 + \frac12 + \left(\frac13 - \frac23\right) + \left(\frac14 - \frac24\right) = \frac{11}{12}$.",
            r"The sum is $\frac{11}{96}$, so $a + b = 107$. The answer is $\textbf{(D) } 107$.",
        ],
        'trap': r"Splitting into only two fractions, $\frac1k$ and $\frac{1}{k+4}$, which leaves the middle term out.",
    },
    '2025-amc-10b-16': {
        'topics': ['casework', 'permutations'],
        'answer': 'D',
        'insight': r"The sectors are all different sizes, so every position counts. Pair them off first and color the pairs afterwards.",
        'steps': [
            r"Number the sectors $1$ to $6$ around. Same-colored sectors are $2$ or $3$ apart. Sectors $2$ apart have the same parity, and three odd sectors cannot all be paired that way, so at least one pair is opposite.",
            r"If $\{1,4\}$ is one pair, the rest pair as $\{2,6\},\{3,5\}$ or as $\{2,5\},\{3,6\}$, which makes every pair opposite. So there are $3$ pairings with exactly one opposite pair and $1$ with all three opposite: $4$ pairings.",
            r"Each pairing takes the three colors in $3! = 6$ ways: $4 \cdot 6 = 24$. The answer is $\textbf{(D)}~24$.",
        ],
        'trap': r"Dividing by rotations as if the sectors were identical. They are different sizes, so a rotated coloring is a new one.",
    },
    '2025-amc-10b-17': {
        'topics': ['sequences-series', 'statistics'],
        'answer': 'B',
        'insight': r"The averages are $2028 - k$ from $k = 3$ on, which pins down every term after the third: $x_k = 2029 - 2k$.",
        'steps': [
            r"The average of the first $k$ terms is $2025 - (k - 3) = 2028 - k$, so the first $k$ terms add to $k(2028 - k)$.",
            r"For $k \ge 4$: $x_k = k(2028 - k) - (k - 1)(2029 - k) = 2029 - 2k$.",
            r"Positive means $k \le 1014$. The first three terms can be chosen to fit (for example $2030, 2023, 2022$, which add to $6075$ and sit above $x_4 = 2021$).",
            r"So $n$ is at most $1014$. The answer is $\textbf{(B) } 1014$.",
        ],
        'trap': r"Requiring $x_n \ge 2$, or counting from the wrong starting term, and answering $1013$.",
    },
    '2025-amc-10b-18': {
        'topics': ['floor-ceiling', 'perfect-powers'],
        'answer': 'D',
        'insight': r"$\lfloor\sqrt i\rfloor = m$ for the $2m + 1$ numbers from $m^2$ to $(m+1)^2 - 1$.",
        'steps': [
            r"For $m = 1, \dots, 44$ the value $m$ appears $2m + 1$ times, and $2025 = 45^2$ adds one $45$.",
            r"$\sum_{m=1}^{44} m(2m+1) = 2 \cdot \frac{44 \cdot 45 \cdot 89}{6} + \frac{44 \cdot 45}{2} = 58740 + 990 = 59730$, and $59730 + 45 = 59775$.",
            r"The ones digit is $5$. The answer is $\textbf{(D) } 5$.",
        ],
        'trap': r"Forgetting the last term, $\lfloor\sqrt{2025}\rfloor = 45$.",
    },
    '2025-amc-10b-19': {
        'topics': ['solid-geometry', 'word-problems'],
        'answer': 'D',
        'insight': r"Extend the sloping sides down to a point: the container is a big pyramid with a small one cut off, and the midline cut is $2 \times 2$.",
        'steps': [
            r"The side of the cross-section grows steadily from $1$ to $3$, so at the midline it is $2$.",
            r"Extended to their apex, the pyramids with bases $1 \times 1$, $2 \times 2$ and $3 \times 3$ are similar, with volumes in the ratio $1 : 8 : 27$.",
            r"The lower half holds $8 - 1 = 7$ parts and the upper half $27 - 8 = 19$. Seven parts took $35$ minutes, so $19$ take $95$.",
            r"The answer is $\textbf{(D) }95$.",
        ],
        'trap': r"Assuming the two halves hold the same amount, or that the volume grows like the side, not its cube.",
    },
    '2025-amc-10b-20': {
        'topics': ['circles', 'coordinate-geometry'],
        'answer': 'A',
        'insight': r"Two tangencies, two equations. Neighboring semicircles touch, which fixes their radius, and the small circle touches each one, which fixes its own.",
        'steps': [
            r"The bottom semicircle has center $(r, 0)$ and the right one $(1, r)$. They touch: $(1 - r)^2 + r^2 = (2r)^2$, so $2r^2 + 2r - 1 = 0$ and $r = \frac{\sqrt3 - 1}{2}$.",
            r"The small circle's center $\left(\frac12, \frac12\right)$ is $\sqrt{\left(\frac12 - r\right)^2 + \frac14} = \sqrt{2 - \sqrt3} = \frac{\sqrt6 - \sqrt2}{2}$ from $(r, 0)$, and that equals $r + \rho$.",
            r"$\rho = \frac{\sqrt6 - \sqrt2 - \sqrt3 + 1}{2}$, so the diameter is $\sqrt6 - \sqrt2 - \sqrt3 + 1 = (\sqrt2 - 1)(\sqrt3 - 1)$.",
            r"$a + b + c + d = 2 - 1 + 3 - 1 = 3$. The answer is $\textbf{(A) } 3$.",
        ],
        'trap': r"Forgetting that $b$ and $d$ are negative here, and adding $2 + 1 + 3 + 1 = 7$.",
    },
    '2025-amc-10b-21': {
        'topics': ['symmetry-counting', 'casework'],
        'answer': 'C',
        'insight': r"Turning every red to blue, blue to yellow and yellow to red keeps a coloring valid, so count the colorings with a yellow center and multiply by $3$.",
        'steps': [
            r"The center stays the center under every rotation and reflection, and the color swap above sends yellow-center colorings to blue-center and then red-center ones. So the answer is $3$ times the number of yellow-center shapes.",
            r"A yellow center needs a red edge square, that red needs a blue corner next to it, and so on around. Checking the edge rings one by one, only two kinds work: a red, a yellow and two neighboring blues ($8$ rings, each finished in $2$ ways), or red and blue opposite with yellows between ($4$ rings, each finished in $3$ ways). That is $28$ colorings.",
            r"Up to rotations and reflections they form $4$ shapes: one that a reflection maps to itself, so it has only $4$ distinct copies, and three with no symmetry, $8$ copies each. Check: $4 + 8 + 8 + 8 = 28$.",
            r"$4 \cdot 3 = 12$. The answer is $\textbf{(C) } 12$.",
        ],
        'trap': r"Dividing the $84$ valid colorings by $8$. Symmetric colorings make some classes smaller, so the classes have to be counted.",
    },
    '2025-amc-10b-22': {
        'topics': ['conditional-probability', 'divisibility'],
        'answer': 'A',
        'insight': r"A digit sum of $61$ is just $2$ short of all nines, so there are very few such numbers to check.",
        'steps': [
            r"Either one digit is $7$ and the rest $9$ ($7$ numbers), or two digits are $8$ ($\binom72 = 21$ numbers). That is $28$ numbers.",
            r"Divisibility by $11$ uses odd places minus even places. All nines gives $36 - 27 = 9$.",
            r"To reach $11$, the shortfall of $2$ must come from the even places: a $7$ in one of the $3$ even places, or both $8$s in even places ($\binom32 = 3$). That is $6$ numbers.",
            r"$\frac{6}{28} = \frac{3}{14}$. The answer is $\textbf{(A) } \frac{3}{14}$.",
        ],
        'trap': r"Putting the shortfall in the odd places, which brings the alternating sum to $7$, not $11$.",
    },
    '2025-amc-10b-23': {
        'topics': ['diophantine', 'modular-arithmetic'],
        'answer': 'C',
        'insight': r"Write both numbers for the square in row $i$, column $j$ and set them equal: a linear equation in integers.",
        'steps': [
            r"Horace writes $91(i - 1) + j$ there and Vera writes $141(j - 1) + i$. They are equal when $90i - 140j = -50$, that is $9i = 14j - 5$.",
            r"Modulo $9$: $5j \equiv 5$, so $j \equiv 1$. So $j = 1, 10, 19, \dots, 91$ (that is $11$ values), and $i = 1 + 14t$ stays at most $141$ for each.",
            r"$11$ squares. The answer is $\textbf{(C) } 11$.",
        ],
        'trap': r"Stopping at $j = 82$, or missing the corner square $(141, 91)$ where both write $12831$.",
    },
    '2025-amc-10b-24': {
        'topics': ['probability', 'recursion'],
        'answer': 'E',
        'insight': r"Let $p_n$ be the chance of reaching $4$ from $n$. Each rule is a linear equation, and they chain from $p_1$ upward.",
        'steps': [
            r"$p_0 = \frac12 p_1$, $p_n = \frac14 p_{n+1} + \frac14 p_{n-1}$ for $n = 1, 2, 3$, and $p_4 = 1$.",
            r"Write everything in terms of $p_1$: $p_2 = 4p_1 - p_0 = \frac72 p_1$ and $p_3 = 4p_2 - p_1 = 13p_1$.",
            r"$1 = p_4 = 4p_3 - p_2 = \frac{97}{2} p_1$, so $p_1 = \frac{2}{97}$ and $p_0 = \frac{1}{97}$.",
            r"The answer is $\textbf{(E) } \frac{1}{97}$.",
        ],
        'trap': r"Multiplying the forward chances $\frac12 \cdot \left(\frac14\right)^3$ and ignoring the steps back.",
    },
    '2025-amc-10b-25': {
        'topics': ['transformations', 'modular-arithmetic'],
        'answer': 'B',
        'insight': r"Reflect the square instead of the path. The path becomes a straight line across a grid of copies, and corners are points whose coordinates are both multiples of $4$.",
        'steps': [
            r"Put $A = (0,0)$, $B = (4,0)$, $D = (0,4)$. Then $P = \left(0, \frac85\right)$ and $Q = \left(\frac{10}{3}, 4\right)$, and the direction from $P$ to $Q$ is parallel to $(25, 18)$.",
            r"The line is $\left(25t, \frac85 + 18t\right)$. It hits a corner when $25t = 4m$ and $\frac85 + 18t = 4n$, which becomes $10 + 18m = 25n$.",
            r"The smallest solution is $m = 5$, $n = 4$: the point $(20, 16)$.",
            r"$20$ is an odd multiple of $4$, so it folds back to $x = 4$. $16$ is an even multiple, so it folds to $y = 0$. The corner is $(4, 0) = B$. The answer is $\textbf{(B) } B$.",
        ],
        'trap': r"Following the bounces one at a time and losing track. There are eight of them before the path reaches $B$.",
    },
    # ------------------------------------------------------------------ 2024 AMC 10B
    # Problem 19 depends on a table that was missing from the pasted paper,
    # so it has no write-up yet.
    '2024-amc-10b-1': {
        'topics': ['arithmetic', 'basic-counting'],
        'answer': 'B',
        'insight': r"Counting from both ends counts that one person twice.",
        'steps': [
            r"There are $1012$ people to the person's left and $1009$ to the right.",
            r"$1012 + 1 + 1009 = 2022$. The answer is $\textbf{(B) } 2022$.",
        ],
        'trap': r"Adding $1013 + 1010 = 2023$ and counting the person twice.",
    },
    '2024-amc-10b-2': {
        'topics': ['factorials', 'arithmetic'],
        'answer': 'B',
        'insight': r"$6! = 720 = 8 \cdot 9 \cdot 10$, which is exactly what takes $7!$ up to $10!$.",
        'steps': [
            r"$7! \cdot 6! = 7! \cdot 720 = 7! \cdot 8 \cdot 9 \cdot 10 = 10!$.",
            r"So the difference is $0$. The answer is $\textbf{(B) } 0$.",
        ],
        'trap': r"Multiplying out the factorials in full and slipping somewhere.",
    },
    '2024-amc-10b-3': {
        'topics': ['absolute-value', 'inequalities'],
        'answer': 'E',
        'insight': r"$|2x| \le 7\pi$ means $|x| \le \frac{7\pi}{2} \approx 10.996$.",
        'steps': [
            r"$\frac{7\pi}{2}$ is just under $11$, so the integers allowed are $-10, -9, \dots, 10$.",
            r"That is $21$ integers. The answer is $\textbf{(E) } 21$.",
        ],
        'trap': r"Forgetting $0$ or the negative values and answering $10$ or $20$.",
    },
    '2024-amc-10b-4': {
        'topics': ['sequences-series', 'modular-arithmetic'],
        'answer': 'D',
        'insight': r"After step $n$, exactly $1 + 2 + \dots + n = \frac{n(n+1)}{2}$ balls have been placed, and step $n$ uses bin number $n$ counted round the five bins.",
        'steps': [
            r"$\frac{63 \cdot 64}{2} = 2016$ and $\frac{64 \cdot 65}{2} = 2080$, so ball $2024$ goes in at step $64$.",
            r"Steps $1, 2, 3, 4, 5$ use $A, B, C, D, E$, and the bins repeat every $5$ steps. $64 = 5 \cdot 12 + 4$, so step $64$ uses the fourth bin, $D$.",
            r"The answer is $\textbf{(D) } D$.",
        ],
        'trap': r"Placing ball $2024$ at step $63$ by using $2016$ as the last ball of step $64$.",
    },
    '2024-amc-10b-5': {
        'topics': ['inequalities', 'sequences-series'],
        'answer': 'B',
        'insight': r"Flipping a $+$ to a $-$ subtracts twice that number from $2500$, so flip the biggest numbers first.",
        'steps': [
            r"$1 + 3 + \dots + 99 = 50^2 = 2500$. Flipping numbers that add up to $S$ gives $2500 - 2S$, which is negative when $S > 1250$.",
            r"The $k$ largest odd numbers add to $99 + 97 + \dots + (101 - 2k) = k(100 - k)$.",
            r"$k = 14$ gives $1204$ (not enough) and $k = 15$ gives $1275$. So $15$ flips are needed. The answer is $\textbf{(B) } 15$.",
        ],
        'trap': r"Requiring $S > 2500$ and forgetting that a flip both removes the number and subtracts it.",
    },
    '2024-amc-10b-6': {
        'topics': ['factors-divisors', 'area'],
        'answer': 'B',
        'insight': r"For a fixed area, the perimeter is smallest when the sides are as close as possible to $\sqrt{2024} \approx 45$.",
        'steps': [
            r"$2024 = 44 \cdot 46$, two sides right next to $45$.",
            r"The perimeter is $2(44 + 46) = 180$. The answer is $\textbf{(B) } 180$.",
        ],
        'trap': r"Taking $8 \times 253$ or another pair of factors without checking the pair closest to the square root.",
    },
    '2024-amc-10b-7': {
        'topics': ['modular-arithmetic', 'factors-divisors'],
        'answer': 'A',
        'insight': r"Factor out $7^{2024}$: what is left is $1 + 7 + 49 = 57 = 3 \cdot 19$.",
        'steps': [
            r"$7^{2024} + 7^{2025} + 7^{2026} = 7^{2024}(1 + 7 + 49) = 57 \cdot 7^{2024}$.",
            r"$57 = 3 \cdot 19$, so the sum is a multiple of $19$ and the remainder is $0$. The answer is $\textbf{(A) } 0$.",
        ],
        'trap': r"Hunting for the cycle of powers of $7$ mod $19$, which works but takes far longer.",
    },
    '2024-amc-10b-8': {
        'topics': ['factors-divisors', 'modular-arithmetic'],
        'answer': 'D',
        'insight': r"The divisors of $42$ pair off as $d$ and $\frac{42}{d}$, so their product is $42$ to the power of half the number of divisors.",
        'steps': [
            r"$42 = 2 \cdot 3 \cdot 7$ has $8$ divisors, forming $4$ pairs that each multiply to $42$. So $N = 42^4$.",
            r"The units digit of $42^4$ is the units digit of $2^4 = 16$, which is $6$. The answer is $\textbf{(D) } 6$.",
        ],
        'trap': r"Thinking $N$ ends in $0$ because $2$ and $7$ are both divisors. There is no $5$ to make a $10$.",
    },
    '2024-amc-10b-9': {
        'topics': ['quadratics', 'statistics'],
        'answer': 'A',
        'insight': r"Square the sum: $(a + b + c)^2 = a^2 + b^2 + c^2 + 2(ab + ac + bc)$.",
        'steps': [
            r"$a + b + c = 0$ and $a^2 + b^2 + c^2 = 30$.",
            r"$0 = 30 + 2(ab + ac + bc)$, so $ab + ac + bc = -15$.",
            r"The mean of the three products is $-5$. The answer is $\textbf{(A) } -5$.",
        ],
        'trap': r"Stopping at the sum $-15$, or dividing by $9$ instead of $3$.",
    },
    '2024-amc-10b-10': {
        'topics': ['area-ratios', 'similar-triangles'],
        'answer': 'A',
        'insight': r"Triangles $FAE$ and $FCB$ are similar with ratio $AE : CB = 1 : 2$, so $F$ is a third of the way along both $AC$ and $EB$.",
        'steps': [
            r"Give the parallelogram area $12$. Each of the triangles $ABC$ and $ACD$ has area $6$.",
            r"$CF$ is $\frac23$ of $CA$, so triangle $CFB$ has $\frac23$ of the area of $ABC$: $4$.",
            r"Triangle $ABE$ has area $3$ (half of $ABD$), and $EF$ is $\frac13$ of $EB$, so triangle $AEF$ has area $1$. Then $CDEF = ACD - AEF = 6 - 1 = 5$.",
            r"The ratio is $5 : 4$. The answer is $\textbf{(A) } 5:4$.",
        ],
        'trap': r"Taking $F$ as the middle of $AC$, which would be true only if $E$ were at $D$.",
    },
    '2024-amc-10b-11': {
        'topics': ['coordinate-geometry', 'right-triangles', 'area'],
        'answer': 'C',
        'insight': r"Put $X$ at the origin. The right angle and the equal areas give two equations for where $M$ and $A$ are.",
        'steps': [
            r"Take $X = (0,0)$, $W = (0,4)$, $Y = (8,0)$, $Z = (8,4)$, $M = (m, 0)$, $A = (8, a)$.",
            r"Equal areas: $\frac12 \cdot 4 \cdot m = \frac12 \cdot 8 \cdot (4 - a)$, so $2m = 16 - 4a$. Right angle at $M$: $(-m)(8 - m) + 4a = 0$, so $4a = m(8 - m)$.",
            r"Then $2m = 16 - 8m + m^2$, so $m^2 - 10m + 16 = 0$ and $m = 2$ ($m = 8$ puts $M$ and $A$ both at $Y$). So $a = 3$.",
            r"$\triangle WMA = 32 - 4 - 4 - \frac12 \cdot 6 \cdot 3 = 15$. The answer is $\textbf{(C) }15$.",
        ],
        'trap': r"Forgetting the third corner triangle, $MYA$, when subtracting from the rectangle.",
    },
    '2024-amc-10b-12': {
        'topics': ['combinations', 'logic'],
        'answer': 'A',
        'insight': r"With everyone speaking $k$ languages, the condition just says no two students speak exactly the same set.",
        'steps': [
            r"Two sets of the same size with neither containing the other are simply two different sets. So we need $100$ different $k$-language sets.",
            r"With $n$ languages the most sets of one size is the middle binomial coefficient. $\binom84 = 70 < 100$, but $\binom94 = 126 \ge 100$.",
            r"So $9$ languages are enough, and $8$ are not. The answer is $\textbf{(A) } 9$.",
        ],
        'trap': r"Giving each student a language of their own ($100$), or reaching for $\log_2 100$.",
    },
    '2024-amc-10b-13': {
        'topics': ['perfect-powers', 'inequalities'],
        'answer': 'B',
        'insight': r"$\sqrt{1183} = 13\sqrt7$, so both square roots must be whole-number multiples of $\sqrt7$.",
        'steps': [
            r"$\sqrt x = 13\sqrt7 - \sqrt y$. Squaring: $x = 1183 + y - 26\sqrt{7y}$, so $\sqrt{7y}$ is rational, and $y = 7b^2$. Likewise $x = 7a^2$, with $a + b = 13$.",
            r"$x + y = 7(a^2 + b^2)$ is smallest when $a$ and $b$ are as close as possible: $6$ and $7$.",
            r"$7(36 + 49) = 595$. The answer is $\textbf{(B) } 595$.",
        ],
        'trap': r"Taking $a = 1$, $b = 12$, which gives the largest sum.",
    },
    '2024-amc-10b-14': {
        'topics': ['geometric-probability', 'circles', 'area'],
        'answer': 'B',
        'insight': r"The target is the ring $18 \le x^2 + y^2 \le 32$, and its outer circle exactly fits inside the diamond.",
        'steps': [
            r"$|x^2 + y^2 - 25| \le 7$ means $18 \le x^2 + y^2 \le 32$: a ring of area $\pi(32 - 18) = 14\pi$.",
            r"The diamond $|x| + |y| \le 8$ has area $2 \cdot 8^2 = 128$. Its sides are $\frac{8}{\sqrt2} = \sqrt{32}$ from the center, so the whole ring is inside.",
            r"The probability is $\frac{14\pi}{128} = \frac{7}{64}\pi$, so $m + n = 71$. The answer is $\textbf{(B) } 71$.",
        ],
        'trap': r"Reading the target as the disk of radius $5$, or forgetting to take square roots of $18$ and $32$ for the radii.",
    },
    '2024-amc-10b-15': {
        'topics': ['statistics', 'casework'],
        'answer': 'C',
        'insight': r"The six given numbers add to $24.8$ and run from $1$ to $7$. A range of $7$ allows only three shapes for $x$ and $z$, and then the mean and median pin everything down.",
        'steps': [
            r"Range $7$: either $x = 0$ and $z \le 7$, or $0 < x < 1$ and $z = x + 7$, or $x \ge 1$ and $z = 8$. ($x < 0$ is impossible, since $7$ is in the list.)",
            r"If $x < 1$, the four smallest are $x, 1, 2.2, 3.2$, so the median (the fifth number) is $3.2$, $y$ or $5.2$, and it is a whole number only when it is $y$, with $y = 4$ or $5$. With $x = 0$, the total $24.8 + y + z$ must be a multiple of $9$ with $y \le z \le 7$: only $y = 5$, $z = 6.2$. With $0 < x < 1$, the total $31.8 + 2x + y$ must be a multiple of $9$: only $y = 4$, $x = 0.1$, $z = 7.1$.",
            r"If $z = 8$, the total $32.8 + x + y$ is $36$ or $45$. $x + y = 3.2$ leaves the median at $3.2$. $x + y = 12.2$ needs one of $x, y$ to be the whole-number median, and only $(x, y) = (6, 6.2)$ works (median $6$).",
            r"That is $3$ triples. The answer is $\textbf{(C) } 3$.",
        ],
        'trap': r"Assuming the new numbers must sit at the ends, and missing $(0.1, 4, 7.1)$ where the range runs from $x$ to $z$.",
    },
    '2024-amc-10b-16': {
        'topics': ['invariants', 'parity'],
        'answer': 'A',
        'insight': r"An odd result needs at least one odd number in the four, so one step clears at most three even numbers.",
        'steps': [
            r"A sum is odd only with an odd number of odd terms, and a product only with four. So every step that leaves an odd number uses at least one odd, and clears at most $3$ evens. A step with an even result clears none.",
            r"There are $1012$ evens, so at least $\lceil 1012/3 \rceil = 338$ steps are needed, each removing $3$ numbers from the board: at most $2024 - 3 \cdot 338 = 1010$ remain.",
            r"$1010$ is reachable: $337$ steps of three evens and one odd, then one step of the last even and three odds (both sums are odd).",
            r"The answer is $\textbf{(A) } 1010$.",
        ],
        'trap': r"Thinking a single step can clear four evens. Their sum and product are both even.",
    },
    '2024-amc-10b-17': {
        'topics': ['permutations', 'casework'],
        'answer': 'D',
        'insight': r"Treat a tied group as a single block, then line up the blocks.",
        'steps': [
            r"No tie: $5! = 120$ results.",
            r"A tie among $k$ snails: choose them in $\binom5k$ ways, then order the block and the other $5 - k$ snails in $(6 - k)!$ ways. $k = 2$: $10 \cdot 24 = 240$. $k = 3$: $10 \cdot 6 = 60$. $k = 4$: $5 \cdot 2 = 10$. $k = 5$: $1$.",
            r"$120 + 240 + 60 + 10 + 1 = 431$. The answer is $\textbf{(D) } 431$.",
        ],
        'trap': r"Leaving out the no-tie case or the five-way tie.",
    },
    '2024-amc-10b-18': {
        'topics': ['modular-arithmetic', 'perfect-powers'],
        'answer': 'B',
        'insight': r"Euler's theorem: $\varphi(125) = 100$, so $n^{100} \equiv 1$ whenever $5 \nmid n$.",
        'steps': [
            r"If $5 \nmid n$, then $n^{100} \equiv 1 \pmod{125}$.",
            r"If $5 \mid n$, then $n^{100}$ is divisible by $5^{100}$, so it leaves $0$.",
            r"Only $0$ and $1$ occur. The answer is $\textbf{(B) } 2$.",
        ],
        'trap': r"Expecting many remainders because $125$ has many residues. The $100$th power flattens them.",
    },
    '2024-amc-10b-20': {
        'topics': ['permutations', 'casework'],
        'answer': 'A',
        'insight': r"Neighbors must be the same hand, or a left and right from the same pair. So every switch between left and right happens inside one pair.",
        'steps': [
            r"Write the row as runs of lefts and rights. At each switch the two shoes are a matched pair. A run of length $1$ in the middle would have to match both its neighbors, which is impossible, so inner runs have length at least $2$.",
            r"One switch (LLLRRR or RRRLLL): pick the pair at the switch, then order the rest, $3 \cdot 2 \cdot 2 = 12$ each, so $24$. Two switches (L RRR LL, LL RRR L and the mirror ones): the two switch pairs are chosen in $3 \cdot 2$ ways and the rest is fixed, $4 \cdot 6 = 24$.",
            r"Three switches need the pattern L RR LL R or R LL RR L, with all three pairs at switches: $2 \cdot 3! = 12$. Four or more switches do not fit in six shoes.",
            r"$24 + 24 + 12 = 60$. The answer is $\textbf{(A) } 60$.",
        ],
        'trap': r"Only counting rows where each pair stands together, and missing the arrangements that group by hand.",
    },
    '2024-amc-10b-21': {
        'topics': ['circles', 'coordinate-geometry'],
        'answer': 'C',
        'insight': r"Two circles of radii $r$ and $s$ resting on the floor and touching have their contact points $2\sqrt{rs}$ apart.",
        'steps': [
            r"Measure along the floor from the big pipe's contact point. The small pipe touches the floor at $2\sqrt{1 \cdot \frac14} = 1$.",
            r"A third pipe of radius $r$ touches at $t$ with $|t| = 2\sqrt r$ and $|t - 1| = 2\sqrt{\frac r4} = \sqrt r$.",
            r"Between the two: $2\sqrt r + \sqrt r = 1$, so $r = \frac19$. Beyond the small pipe: $2\sqrt r - \sqrt r = 1$, so $r = 1$. Beyond the big pipe there is no solution.",
            r"$\frac19 + 1 = \frac{10}{9}$. The answer is $\textbf{(C)}~\frac{10}{9}$.",
        ],
        'trap': r"Finding only the small pipe in the gap and missing the radius-$1$ pipe on the far side.",
    },
    '2024-amc-10b-22': {
        'topics': ['combinations', 'factorials'],
        'answer': 'A',
        'insight': r"Count the committees, then the officers, and track only the factors of $3$.",
        'steps': [
            r"Splitting into $4$ unlabeled groups of $4$: $\frac{16!}{(4!)^4 \cdot 4!}$. Officers in each group: $4 \cdot 3 = 12$, so $12^4$ in all.",
            r"Powers of $3$: $16!$ has $5 + 1 = 6$, $(4!)^4$ has $4$, $4!$ has $1$, and $12^4$ has $4$.",
            r"$r = 6 - 4 - 1 + 4 = 5$. The answer is $\textbf{(A) } 5$.",
        ],
        'trap': r"Treating the committees as labeled and forgetting to divide by $4!$, which gives $6$.",
    },
    '2024-amc-10b-23': {
        'topics': ['sequences-series', 'recursion'],
        'answer': 'B',
        'insight': r"$\frac{F_{2n}}{F_n}$ is the Lucas number $L_n$ ($1, 3, 4, 7, 11, \dots$), which follows the same rule as the Fibonacci numbers.",
        'steps': [
            r"$F_{2n} = F_n L_n$, where $L_1 = 1$, $L_2 = 3$, and each term is the sum of the two before. (Check: $\frac{F_4}{F_2} = 3$ and $\frac{F_6}{F_3} = 4$.)",
            r"$L_1, \dots, L_{10}$: $1, 3, 4, 7, 11, 18, 29, 47, 76, 123$.",
            r"They add to $319$. The answer is $\textbf{(B) } 319$.",
        ],
        'trap': r"Using $\frac{F_{2n}}{F_n} = F_n$ or similar guesses instead of checking the first few ratios.",
    },
    '2024-amc-10b-24': {
        'topics': ['modular-arithmetic', 'parity'],
        'answer': 'E',
        'insight': r"$P(m)$ is an integer when $8$ divides $8P(m) = 4m + 2m^2 + m^4 + m^8$.",
        'steps': [
            r"For even $m = 2k$: $8k + 8k^2 + 16k^4 + 256k^8$ is a multiple of $8$.",
            r"For odd $m$: $m^2 \equiv 1 \pmod 8$, so $m^4 \equiv m^8 \equiv 1$, and $4m + 2m^2 + m^4 + m^8 \equiv 4 + 2 + 1 + 1 = 8 \equiv 0$.",
            r"So $P(m)$ is an integer for every integer $m$, including all four. The answer is $\textbf{(E) } 4$.",
        ],
        'trap': r"Assuming odd $m$ fails because $\frac m2$ is not an integer. The four fractions together are.",
    },
    '2024-amc-10b-25': {
        'topics': ['solid-geometry', 'diophantine'],
        'answer': 'E',
        'insight': r"The old block measures $3a \times 3b \times 3c$ and the new one $2 \times 2 \times 7$ bricks, so each of $3a + 1$, $3b + 1$, $3c + 1$ is $2$ or $7$ times a brick edge.",
        'steps': [
            r"With every brick facing the same way, $\{3a + 1, 3b + 1, 3c + 1\} = \{2p, 2q, 7r\}$, where $p, q, r$ are $a, b, c$ in some order. No edge can pair with itself ($3a + 1 = 2a$ or $7a$ has no positive solution), so the pairing goes round in a cycle.",
            r"Name them so that $3a + 1 = 2b$, $3b + 1 = 2c$ and $3c + 1 = 7a$. Then $b = \frac{3a + 1}{2}$, $c = \frac{9a + 5}{4}$, and $\frac{27a + 19}{4} = 7a$, so $a = 19$.",
            r"That gives $b = 29$ and $c = 44$ (pairwise relatively prime). The blocks are $57 \times 87 \times 132$ and $58 \times 88 \times 133$.",
            r"$a + b + c = 92$. The answer is $\textbf{(E) } 92$.",
        ],
        'trap': r"Comparing volumes alone. $28abc = (3a+1)(3b+1)(3c+1)$ has many near-solutions; matching edge by edge is what decides it.",
    },
}


def for_problem(problem_id, answer):
    """The solution for an official problem, if Summit has written one for this answer.

    `answer` is the imported key's answer; a solution written for a different
    one is not returned, since showing it would contradict the key.
    """
    entry = SOLUTIONS.get(problem_id)
    if not entry or str(entry['answer']) != str(answer):
        return None
    return entry
