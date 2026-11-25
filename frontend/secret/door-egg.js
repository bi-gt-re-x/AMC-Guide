/* door-egg.js — the first door in the chain, on the dashboard.
 *
 * The dashboard's big title (how many days to the contest) is a door. Click it
 * ten times in a row (each within a second and a half of the last) and it
 * gives: from the third click it ticks, on the tenth it shudders, and a quote
 * fades in at the foot of the page:
 *
 *     "The pentagon is the key. Find it."
 *
 * Opening it writes today's unlock, `easterEgg:<account>:<YYYY-MM-DD>`, the
 * key every later stage reads: the pentagon on the landing page
 * (pentagon-egg.js) stays inert without it, and /engine (engine.js) turns
 * away anybody without it. The quote stays for the rest of the day, so a
 * reload does not ask for ten more clicks.
 *
 * Loaded by pages/amc/Dashboard.tsx through hooks/useSecretScripts.ts once the
 * page is on screen; it binds to `[data-egg="door"] .am-title`, which React
 * renders and otherwise leaves alone.
 */
(function () {
    'use strict';

    var NEEDED = 10;          // clicks to open the door
    var GAP = 1500;           // ms between clicks before the count starts again
    var QUOTE = 'The pentagon is the key. Find it.';

    function user() {
        try { return localStorage.getItem('currentUser') || 'Default'; } catch (e) { return 'Default'; }
    }
    function todayStr() {
        var d = new Date();
        var p = function (n) { return n < 10 ? '0' + n : '' + n; };
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
    }
    function key() { return 'easterEgg:' + user() + ':' + todayStr(); }
    function unlocked() {
        try { return localStorage.getItem(key()) === '1'; } catch (e) { return false; }
    }
    function unlock() {
        try { localStorage.setItem(key(), '1'); } catch (e) { /* the quote still shows; it will not survive a reload */ }
    }

    function init() {
        var page = document.querySelector('[data-egg="door"]');
        var title = page && page.querySelector('.am-title');
        if (!title || title.getAttribute('data-egg-bound')) return;
        title.setAttribute('data-egg-bound', '1');
        if (unlocked()) showQuote(page, false);

        var clicks = 0;
        var last = 0;
        title.addEventListener('click', function () {
            var now = Date.now();
            clicks = now - last <= GAP ? clicks + 1 : 1;
            last = now;
            if (clicks >= 3 && clicks < NEEDED) replay(title, 'door-tick');
            if (clicks < NEEDED) return;
            clicks = 0;
            replay(title, 'door-open');
            unlock();
            showQuote(page, true);
        });
    }

    // Take a class off and put it back, so its animation plays again.
    function replay(el, name) {
        el.classList.remove('door-tick', 'door-open');
        void el.offsetWidth;
        el.classList.add(name);
    }

    function showQuote(page, fresh) {
        var q = document.getElementById('doorQuote');
        if (!q) {
            q = document.createElement('figure');
            q.id = 'doorQuote';
            q.innerHTML = '<blockquote></blockquote>';
            q.firstChild.textContent = '“' + QUOTE + '”';
            page.appendChild(q);
        }
        if (!fresh) { q.classList.add('show', 'still'); return; }
        // A beat after it is in the page, so the fade has a start to fade from.
        // (A timeout, not requestAnimationFrame, which waits on a hidden tab.)
        setTimeout(function () {
            q.classList.add('show');
            q.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 40);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
