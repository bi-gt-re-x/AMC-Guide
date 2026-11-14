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
