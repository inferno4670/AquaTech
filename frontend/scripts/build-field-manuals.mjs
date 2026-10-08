/**
 * Derives the AquaTrack landing document from the authored "Bestsellers Book Showcase".
 *
 * Why a generator instead of a hand-edited file: the authored document is 3.5 MB of HTML
 * with six base64 payloads embedded in it (per book, a cover plate and its motion loop).
 * Editing it by hand means the renderer, the styles and the media drift out of sync with
 * the source with no way to tell. Here the source stays byte-exact on disk at
 * `public/landing-pages/bestsellers-book-showcase.html` (checksum below) and this script
 * proves it before deriving anything. Re-running it is the supported way to change copy.
 *
 * What the script changes — content only:
 *   · page title, meta description, brand, hero word, menu, panel labels and ARIA text
 *   · the three cover blurbs (the cover *typography*; the cover art is authored media)
 *   · the `books` data object the renderer reads
 *   · `data-go` on the first two cards, so the host router can open the app's own pages
 *   · one appended host-integration script (see HOST_SCRIPT below)
 *
 * What it never touches: the stylesheet, the renderer, the interaction code, and the six
 * embedded media payloads. All of those stay byte-identical.
 *
 * Run:  node scripts/build-field-manuals.mjs      (or: npm run build:landing)
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const pagesDir = join(here, '..', 'public', 'landing-pages');
const SOURCE = join(pagesDir, 'bestsellers-book-showcase.html');
const TARGET = join(pagesDir, 'aquatrack-field-manuals.html');

/** Revision of the authored document this derivation is written against. */
const SOURCE_SHA256 = '7c1ed1ca4a4c58f1c33956c84edd8f7ba450ea0312df718701e634a207568138';

/** The three volumes. Volume I opens the search page, II the recording page, III stays. */
const BOOKS = {
  scroll: {
    cover: { title: 'Holy<br>Scroll', subtitle: 'The Searching Volume', footer: 'Species · Habitat · Season' },
    title: 'The Holy Scroll of Fishing',
    year: '2026',
    description:
      'The Holy Scroll is the searching volume. It reads the sea the way a fisherman reads it — species by species, month by month — and turns that reading into water worth a look. Name a fish, name the range you can actually steam in a day, and it answers with habitat suitability, the live sea state, and the sightings your own community has already recorded.',
    steps: [
      { title: 'Name the fish', body: 'Pick a species from the scroll. Each entry carries its season, its protected status and the water it genuinely holds in.' },
      { title: 'Choose your waters', body: 'Set the region and the radius you can reach and return from. The scroll never sends you to ground you cannot safely work.' },
      { title: 'Read the sea', body: 'Suitability is scored against today’s temperature, depth, current and wind — not against one fixed map drawn once.' },
      { title: 'Check the record', body: 'See what other contributors have already recorded nearby, and when. The scroll remembers, so you do not have to guess.' },
    ],
    prompt: 'species: Indian Oil Sardine · region: Maharashtra · radius: 60 km',
    review:
      'Suitability is a probability, not a promise. It reads the water, never the fish. Check the season, the licence, the closed areas and the weather before you leave the shore.',
  },
  ledger: {
    cover: { title: 'The<br>Ledger', subtitle: 'The Recording Volume', footer: 'Species · Place · Time' },
    title: 'The Ledger of Recorded Waters',
    year: '2026',
    description:
      'The Ledger is the recording volume. Every fish you see is a line of evidence no model can invent: the species, the place, the hour, the gear, and the sea it came out of. What you write here is what the next boat is told — which is why the ledger asks for what you saw, not for what you hoped.',
    steps: [
      { title: 'Write it while it is fresh', body: 'Time and position matter more than prose. Record the sighting the same day whenever you can.' },
      { title: 'Say what you actually saw', body: 'Size, weight, condition, gear, and whether it was kept, released or lost. Honest entries are the only useful ones.' },
      { title: 'Attach the conditions', body: 'The wheelhouse data — swell, wind, surface temperature — is what makes a record explainable years later.' },
      { title: 'Let it be checked', body: 'Entries are reviewed before they join the record. Corrections are part of the work, not an accusation.' },
    ],
    prompt: 'species · date · time · position · gear · depth · sea state · notes',
    review:
      'Never publish a precise position for a protected, spawning or restricted species. Records are reviewed, and a record you cannot stand behind is worse than no record at all.',
  },
  tide: {
    cover: { title: 'Respect', subtitle: 'The Etiquette of Water', footer: 'Restraint · Care · Return' },
    title: 'In Respect of the Sea',
    year: '2026',
    description:
      'The third volume carries no map and no form. It is the etiquette of the water: what we take, what we leave, and what is owed to the ground that feeds us. It is bound first for a reason — read it before the other two.',
    steps: [
      { title: 'Know what is protected', body: 'Protected, restricted and spawning species have closed seasons for a reason. The scroll marks them; the law enforces them.' },
      { title: 'Take only what you need', body: 'Effort for need, not effort for maximum. A full hold has never been proof of a healthy sea.' },
      { title: 'Leave the ground as you found it', body: 'No gear over the side, no anchoring on reef, no litter in the water. The sea keeps a long record and settles slowly.' },
      { title: 'Report what you cannot fix', body: 'Oil, dead water, ghost nets, a stranded animal. A report is the cheapest thing you will ever do for the sea.' },
    ],
    prompt: 'Take the record. Leave the ground.',
    review:
      'Respect is a practice before it is a feeling. Follow local rules, seasonal closures and protected-area boundaries — then teach the next hand on deck to do the same.',
  },
};

/** Cover kickers are already numbered in the authored document; reuse them verbatim. */
const KICKERS = { scroll: 'Field Manual · I', ledger: 'Field Manual · II', tide: 'Field Manual · III' };

/**
 * The renderer keys each volume by ID: `books[card.dataset.book]`, four CSS selectors and
 * the card's own attribute. Renaming a key means renaming all six references or a card
 * dead-ends on click, so both spellings are rewritten together and counted below.
 *
 * Note `cursor`: the old key collides with the CSS `cursor:` property, which is why the
 * rename is done by attribute and object-key, never by a bare word substitution.
 */
const RENAMES = { codex: 'scroll', claude: 'ledger', cursor: 'tide' };

/** Where each volume sends the reader. Volume III stays on the page — no route. */
const ROUTES = { scroll: '/find', ledger: '/contribute' };

/**
 * The authored document is LF throughout — measured, not assumed: zero CR bytes in 3.5 MB.
 * So the needles below are written in LF and inserted text goes in exactly as written, and
 * this helper only guards the assumption. Nothing here may translate newlines: the base64
 * payloads would be rewritten along with everything else.
 */
const authoredNewlines = (text) => {
  if (text.includes('\r')) throw new Error('inserted text must not contain CR — the document is LF');
  return text;
};

/**
 * The rendered cover blurb as it appears in the authored markup: the opener, five spans and
 * the closer. Non-greedy, so it stops at the closer rather than swallowing later cards.
 */
const COVER_COPY = /            <span class="cover-copy">[\s\S]*?<\/span>\n            <\/span>/g;

/**
 * Appended host integration. The authored renderer is untouched: this listens in the
 * capture phase, so a click on a routed volume never reaches the detail-panel handler.
 * Everything else — volume III included — keeps the authored behaviour exactly.
 */
const HOST_SCRIPT = `  <!-- AquaTrack host integration.
       Kept apart from the authored script above. This only intercepts clicks on the two
       cards that carry data-go, in the capture phase, so the authored detail handler never
       sees them; every other interaction stays exactly as authored. -->
  <script>
    (() => {
      const ROUTES = ${JSON.stringify(Object.values(ROUTES))};
      document.addEventListener(
        "click",
        (event) => {
          const trigger = event.target.closest("[data-go]");
          if (!trigger) return;
          const to = trigger.getAttribute("data-go");
          if (!ROUTES.includes(to)) return;
          event.preventDefault();
          event.stopPropagation();
          if (window.parent !== window) {
            window.parent.postMessage({ type: "aquatrack:open-book", to }, window.location.origin);
          } else {
            window.location.assign(to);
          }
        },
        true
      );
    })();
  </script>
`;

function assertCount(label, text, needle, expected) {
  const found = text.split(needle).length - 1;
  if (found !== expected) {
    throw new Error(`${label}: expected ${expected} × ${JSON.stringify(needle.slice(0, 70))}, found ${found}`);
  }
}

function replaceOnce(label, text, needle, replacement) {
  assertCount(label, text, needle, 1);
  return text.replace(needle, () => replacement);
}

/** Same contract as replaceOnce, for the few spans whose authored text we do not quote. */
function replaceRegexOnce(label, text, pattern, replacement) {
  const found = text.match(pattern) ?? [];
  if (found.length !== 1) throw new Error(`${label}: expected 1 match of ${pattern}, found ${found.length}`);
  return text.replace(pattern, () => replacement);
}

/**
 * The `books` object is replaced whole. A brace counter that understands string literals
 * finds its end, so the renderer code that follows it is never disturbed.
 */
function replaceBooksObject(html, literal) {
  const anchor = '      const books = {';
  assertCount('books anchor', html, anchor, 1);
  const start = html.indexOf(anchor);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let p = html.indexOf('{', start); p < html.length; p += 1) {
    const ch = html[p];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") quote = ch;
    else if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth === 0) {
        const tail = html.slice(p + 1);
        if (!tail.startsWith(';')) throw new Error('books object is not terminated by ";"');
        return html.slice(0, start) + '      const books = ' + authoredNewlines(literal) + tail;
      }
    }
  }
  throw new Error('unterminated books object');
}

/** Serialise the volume data in the authored object's formatting (2-space nesting). */
function booksLiteral() {
  const q = (s) => JSON.stringify(s);
  const entries = Object.entries(BOOKS).map(([key, book]) => {
    const steps = book.steps
      .map((s) => `            {\n              title: ${q(s.title)},\n              body: ${q(s.body)}\n            }`)
      .join(',\n');
    return [
      `        ${key}: {`,
      `          title: ${q(book.title)},`,
      `          year: ${q(book.year)},`,
      `          description:`,
      `            ${q(book.description)},`,
      `          steps: [`,
      steps,
      `          ],`,
      `          prompt:`,
      `            ${q(book.prompt)},`,
      `          review:`,
      `            ${q(book.review)}`,
      `        }`,
    ].join('\n');
  });
  return `{\n${entries.join(',\n')}\n      }`;
}

/** The rendered cover typography: kicker, title, subtitle, spacer, footer. */
function coverBlurb(key) {
  const book = BOOKS[key];
  return (
    `            <span class="cover-copy">\n` +
    `              <span class="cover-kicker">${KICKERS[key]}</span>\n` +
    `              <span class="cover-title">${book.cover.title}</span>\n` +
    `              <span class="cover-subtitle">${book.cover.subtitle}</span>\n` +
    `              <span></span>\n` +
    `              <span class="cover-footer">${book.cover.footer}</span>\n` +
    `            </span>`
  );
}

function derive() {
  const bytes = readFileSync(SOURCE);
  const digest = createHash('sha256').update(bytes).digest('hex');
  if (digest !== SOURCE_SHA256) {
    throw new Error(`authored source changed:\n  expected ${SOURCE_SHA256}\n  actual   ${digest}`);
  }

  const raw = bytes.toString('utf8');
  let html = raw;

  // ---- document head -------------------------------------------------------------------
  html = replaceOnce(
    'meta description',
    html,
    '    content="An earth-toned interactive field library for Codex, Claude Code, and Cursor."',
    '    content="AquaTrack&#39;s three field manuals of the sea: search the waters for a species, record what you see, and keep faith with the sea that feeds you."',
  );
  html = replaceOnce(
    'title',
    html,
    '<title>Field Manuals — Tools for Thought</title>',
    '<title>AquaTrack — Field Manuals of the Sea</title>',
  );

  // ---- topbar, hero, gallery -----------------------------------------------------------
  html = replaceOnce(
    'brand',
    html,
    '<a class="brand" href="#" aria-label="Field Manuals home">Field Manuals</a>',
    '<a class="brand" href="#" aria-label="AquaTrack field manuals home">AquaTrack</a>',
  );
  html = replaceOnce(
    'ticket button',
    html,
    '<button class="ticket-button" type="button" data-toast="The collection is complete.">The Collection</button>',
    '<button class="ticket-button" type="button" data-toast="Three volumes. One sea.">Three Volumes</button>',
  );
  html = replaceOnce(
    'hero word',
    html,
    '<h1 class="hero-word" aria-hidden="true">Agents</h1>',
    '<h1 class="hero-word" aria-hidden="true">Oceans</h1>',
  );
  html = replaceOnce(
    'stage label',
    html,
    '<main class="stage" aria-label="Interactive AI coding field library">',
    '<main class="stage" aria-label="AquaTrack field manuals: search the waters, record your sightings, respect the sea">',
  );
  html = replaceOnce(
    'gallery label',
    html,
    '<section class="gallery" aria-label="AI coding field manuals">',
    '<section class="gallery" aria-label="AquaTrack field manuals of the sea">',
  );

  // ---- menu ----------------------------------------------------------------------------
  html = replaceOnce(
    'menu',
    html,
    authoredNewlines(
      '        <li><a class="menu-link" href="#" data-menu-close>Volumes</a></li>\n' +
        '        <li><a class="menu-link" href="#notes" data-menu-close data-toast="Field notes are coming soon.">Notes</a></li>\n' +
        '        <li><a class="menu-link" href="#index" data-menu-close data-toast="An index of tools for thought.">Index</a></li>',
    ),
    authoredNewlines(
      '        <li><a class="menu-link" href="#" data-menu-close>The Three Volumes</a></li>\n' +
        '        <li><a class="menu-link" href="#notes" data-menu-close data-toast="Field notes are coming soon.">Field Notes</a></li>\n' +
        '        <li><a class="menu-link" href="#index" data-menu-close data-toast="An index of named fishes.">Species Index</a></li>',
    ),
  );

  // ---- renderer keys -------------------------------------------------------------------
  for (const [from, to] of Object.entries(RENAMES)) {
    // Four CSS selectors plus the card attribute.
    assertCount(`card attribute ${from}`, html, `data-book="${from}"`, 5);
    html = html.split(`data-book="${from}"`).join(`data-book="${to}"`);
    assertCount(`books key ${from}`, html, `        ${from}: {`, 1);
    html = html.replace(`        ${from}: {`, `        ${to}: {`);
  }

  // ---- the three cards: route and ARIA label -------------------------------------------
  for (const [key, book] of Object.entries(BOOKS)) {
    const routed = ROUTES[key] ? `        data-go="${ROUTES[key]}"\n` : '';
    html = replaceRegexOnce(
      `card ${key} attributes`,
      html,
      new RegExp(`        data-book="${key}"\n        aria-label="Open [^"]+"\n`),
      authoredNewlines(`        data-book="${key}"\n${routed}        aria-label="Open ${book.title}"\n`),
    );
  }

  // ---- the cover typography ------------------------------------------------------------
  // One global pass, not one replace per book: a per-book `replace` would keep finding the
  // *earlier* blurb it had just written and would rewrite the same cover three times.
  // A global pass walks the original string once, left to right, and never re-scans.
  const volumeOrder = Object.keys(BOOKS);
  let written = 0;
  html = html.replace(COVER_COPY, (match, offset) => {
    const key = volumeOrder[written];
    if (!key) throw new Error('more cover blurbs in the document than volumes');
    // The blurb belongs to the card whose data-book attribute precedes it.
    const owners = [...html.slice(0, offset).matchAll(/data-book="([a-z]+)"/g)];
    const owner = owners.length ? owners[owners.length - 1][1] : null;
    if (owner !== key) throw new Error(`cover blurb ${written + 1}: belongs to ${owner}, expected ${key}`);
    written += 1;
    return authoredNewlines(coverBlurb(key));
  });
  if (written !== volumeOrder.length) {
    throw new Error(`expected ${volumeOrder.length} cover blurbs, rewrote ${written}`);
  }

  // ---- detail panel --------------------------------------------------------------------
  html = replaceOnce('detail scroll label', html, 'aria-label="Getting started guide"', 'aria-label="Field manual"');
  html = replaceOnce(
    'detail title placeholder',
    html,
    '<h2 class="detail-title" id="detailTitle">Claude Code</h2>',
    `<h2 class="detail-title" id="detailTitle">${BOOKS.scroll.title}</h2>`,
  );
  html = replaceOnce(
    'section label 2',
    html,
    '<p class="doc-label" id="firstPromptLabel">Your first prompt</p>',
    '<p class="doc-label" id="firstPromptLabel">In practice</p>',
  );
  html = replaceOnce(
    'section label 3',
    html,
    '<p class="doc-label" id="reviewLabel">Before you ship</p>',
    '<p class="doc-label" id="reviewLabel">Keep in mind</p>',
  );
  html = replaceOnce(
    'pill notes',
    html,
    '<button class="pill" type="button" data-toast="Notes opened.">Read Notes</button>',
    '<button class="pill" type="button" data-toast="Field notes opened.">Field Notes</button>',
  );
  html = replaceOnce(
    'pill guide',
    html,
    '<button class="pill" type="button" data-toast="Guide opened.">View Guide</button>',
    '<button class="pill" type="button" data-toast="Guide opened.">Read the Guide</button>',
  );
  html = replaceOnce('save button label', html, 'aria-label="Save book"', 'aria-label="Save volume"');

  // ---- the renderer's data -------------------------------------------------------------
  html = replaceBooksObject(html, booksLiteral());

  // ---- host integration ----------------------------------------------------------------
  html = replaceOnce('host script', html, '\n</body>', '\n' + authoredNewlines(HOST_SCRIPT) + '</body>');

  // ---- contract checks -----------------------------------------------------------------
  // The `books` object, the `data-book` attributes and the four CSS selectors per key all
  // have to agree. Renaming a key renames all six; a stray one silently dead-ends a card.
  for (const key of Object.keys(BOOKS)) {
    assertCount(`css selectors for ${key}`, html, `[data-book="${key}"]`, 4);
    assertCount(`card attribute for ${key}`, html, `data-book="${key}"`, 5);
  }
  for (const [key, book] of Object.entries(BOOKS)) {
    assertCount(`title for ${key}`, html, JSON.stringify(book.title), 1);
  }

  // No copy from the authored library may survive. The only tolerated `cursor` is a CSS
  // declaration; anything else would be the old book key left behind.
  for (const gone of ['codex', 'claude', 'Codex', 'Claude', 'Cursor', 'agentic', 'repository']) {
    const at = html.indexOf(gone);
    if (at !== -1) {
      throw new Error(
        `authored copy leak: ${gone} survives at ${at}\n  ${JSON.stringify(html.slice(Math.max(0, at - 110), at + 60))}`,
      );
    }
  }
  const strayCursor = html.match(/cursor(?!:)/g) ?? [];
  if (strayCursor.length !== 0) throw new Error(`stray "cursor" occurrences: ${strayCursor.length}`);

  if (!html.includes('aquatrack:open-book')) throw new Error('host integration script missing');

  // The six embedded payloads — three cover plates, three motion loops — must come out
  // byte-identical, or the derivation has silently rewritten authored media.
  const payloads = (text) => text.match(/base64,[A-Za-z0-9+/\r\n=]+/g) ?? [];
  const before = payloads(raw);
  const after = payloads(html);
  if (before.length !== 6) throw new Error(`expected 6 embedded payloads in the source, found ${before.length}`);
  if (after.length !== before.length || after.some((p, i) => p !== before[i])) {
    throw new Error('embedded media changed — the derivation must not rewrite authored assets');
  }

  return { html, sourceBytes: bytes.length };
}

const { html, sourceBytes } = derive();
writeFileSync(TARGET, html, 'utf8');
console.log(`authored source verified  sha256 ${SOURCE_SHA256.slice(0, 12)}… (${sourceBytes} bytes)`);
console.log(`derived landing written  ${TARGET} (${Buffer.byteLength(html)} bytes)`);
console.log(
  `volumes: ${Object.keys(BOOKS).join(', ')} — routed: ${Object.entries(ROUTES)
    .map(([k, v]) => `${k}→${v}`)
    .join(', ')}`,
);
