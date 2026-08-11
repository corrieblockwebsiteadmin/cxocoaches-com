#!/usr/bin/env python3
"""Static site generator for cxocoaches.com (Coach Index Network).

Quarterly refresh = edit data/edition.json and re-run. No HTML is hand-edited.
"""
import json, os, shutil, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(ROOT, "data", "edition.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "docs")
S = DATA["site"]
BASE = "https://" + S["domain"]

NAV = [("/", "The Ranking"), ("/about.html", "Methodology"),
       ("/curator.html", "Curator"), ("/nominate.html", "Nominate")]


def esc(t):
    return html.escape(t, quote=True)


def initials(name):
    """Monogram from a person's name. Titles stripped so 'Dr Carol Kauffman' -> CK."""
    drop = {"dr", "dr.", "prof", "prof.", "professor", "mr", "mrs", "ms", "sir", "the"}
    words = [w for w in name.replace("-", " ").split() if w.strip(".").lower() not in drop]
    letters = [w[0].upper() for w in words if w[:1].isalpha()]
    if not letters:
        return "?"
    return (letters[0] + letters[-1]) if len(letters) > 1 else letters[0]


def avatar(c, size="md"):
    """Render a coach avatar.

    A real photograph is rendered ONLY when the record carries an explicit
    src, credit and licence. Absent any of the three we fall back to a
    monogram. This keeps the image rights position structural rather than a
    matter of memory: an unlicensed headshot cannot reach the page by
    accident, because the generator will not emit one.
    """
    ph = c.get("photo") or {}
    if ph.get("src") and ph.get("credit") and ph.get("licence"):
        return ('<div class="avatar avatar--%s"><img src="%s" alt="%s" loading="lazy" '
                'width="160" height="160"></div>' % (size, esc(ph["src"]), esc(c["name"])))
    return ('<div class="avatar avatar--%s" role="img" aria-label="%s">%s</div>'
            % (size, esc(c["name"]), esc(initials(c["name"]))))


def page(slug, title, desc, body, schema=None, canonical=None, wide=False):
    nav = "".join('<a href="%s">%s</a>' % (h, l) for h, l in NAV)
    sch = ""
    if schema:
        sch = '<script type="application/ld+json">%s</script>' % json.dumps(
            schema, ensure_ascii=False, indent=None)
    can = canonical or (BASE + ("/" if slug == "index" else "/" + slug + ".html"))
    depth = "../" if "/" in slug else ""
    wrapmod = " wrap--wide" if wide else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{can}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{can}">
<link rel="stylesheet" href="{depth}style.css">
{sch}
</head>
<body>
<div class="wrap{wrapmod}">
<header class="site">
  <div class="masthead"><a href="/">{esc(S['domain'])}</a></div>
  <h1>{esc(S['title'])}</h1>
  <p class="tagline">{esc(S['tagline'])}</p>
  <nav class="site">{nav}</nav>
</header>
<main>
{body}
</main>
<footer class="site">
  <p><strong>Ownership and independence.</strong> This site is owned and curated by {esc(S['curator'])}.
     No coach pays for placement and no coach is charged for inclusion.
     See the <a href="/curator.html">curator page</a> for full disclosure.</p>
  <p><strong>Corrections and removal.</strong> Write to
     <a href="mailto:{S['contact']}">{S['contact']}</a>. Evidenced corrections are made promptly,
     and any listed coach who asks to be removed is removed without argument.</p>
  <p>Edition {esc(S['edition'])} · published {esc(S['published'])} · next review {esc(S['next_review'])}</p>
</footer>
</div>
</body>
</html>
"""


def person_schema(c):
    d = {"@context": "https://schema.org", "@type": "Person", "name": c["name"],
         "jobTitle": "Executive Coach", "description": c["bio"],
         "url": BASE + "/coaches/" + c["slug"] + ".html"}
    same = [l["url"] for l in c["links"]]
    if same:
        d["sameAs"] = same
    return d


def build_index():
    parts = []
    parts.append('<div class="meta"><strong>Edition %s.</strong> Published %s. Next review %s. '
                 'Curated by %s against a <a href="/about.html">published methodology</a>. '
                 'All sources accessed 2026-08-06.</div>'
                 % (esc(S["edition"]), esc(S["published"]), esc(S["next_review"]), esc(S["curator"])))

    parts.append('<section class="note"><h2>How this list differs</h2>')
    for p in DATA["editorial_note"]:
        parts.append("<p>%s</p>" % p)
    parts.append("</section>")

    def _links(c):
        return "".join('<a href="%s" rel="noopener">%s</a>' % (l["url"], esc(l["label"]))
                       for l in c["links"])

    coaches = sorted(DATA["coaches"], key=lambda x: x["rank"])
    top, rest = coaches[:3], coaches[3:]

    # Ranks 1-3 carry the argument of the list, so they get room to make it.
    if top:
        parts.append('<div class="features">')
        for c in top:
            parts.append(f"""<article class="feature">
  <div class="top">
    <div class="rank">{c['rank']}</div>
    {avatar(c, "lg")}
  </div>
  <h3><a href="/coaches/{c['slug']}.html">{esc(c['name'])}</a></h3>
  <p class="where">{esc(c['location'])}</p>
  <p class="role">{c['role']}</p>
  <p class="assess">{c['assessment'][0]}</p>
  <p class="links">{_links(c)}</p>
</article>""")
        parts.append('</div>')

    if rest:
        parts.append('<div class="entries">')
        for c in rest:
            parts.append(f"""<article class="entry">
  <div class="top">
    <div class="rank">{c['rank']}</div>
    {avatar(c, "md")}
    <div>
      <h3><a href="/coaches/{c['slug']}.html">{esc(c['name'])}</a></h3>
      <p class="where">{esc(c['location'])}</p>
    </div>
  </div>
  <p class="role">{c['role']}</p>
  <p class="assess">{c['assessment'][0]}</p>
  <p class="links">{_links(c)}</p>
</article>""")
        parts.append('</div>')

    parts.append('<div class="section-head"><h2>Ones to Watch</h2><span class="line"></span></div>')
    parts.append('<p class="section-lede">Named, not ranked. Practitioners whose work is strong and whose published '
                 'corpus is still building. This is a different question from the ranking above, '
                 'not a lower tier of it.</p>')
    parts.append('<div class="cards">')
    for w in DATA["ones_to_watch"]:
        parts.append(f"""<div class="card">
  <div class="top">
    {avatar(w, "sm")}
    <div>
      <h3><a href="{w['url']}" rel="noopener">{esc(w['name'])}</a></h3>
      <p class="where">{esc(w['location'])}</p>
    </div>
  </div>
  <p>{w['text']}</p>
  <ul class="caveats"><li>{w['note']}</li></ul>
</div>""")
    parts.append('</div>')

    parts.append('<div class="section-head"><h2>Considered and not included</h2><span class="line"></span></div>')
    parts.append('<p class="section-lede">A ranking that quietly omits well-known names invites the assumption that it '
                 'did not know about them. These were assessed and left out for stated reasons.</p>')
    parts.append('<div class="cards">')
    for x in DATA["not_included"]:
        parts.append('<div class="card card--plain"><h3>%s</h3><p>%s</p></div>' % (esc(x["name"]), x["text"]))
    parts.append('</div>')

    parts.append('<div class="section-head"><h2>Verification still outstanding</h2><span class="line"></span></div>')
    parts.append('<p class="section-lede">Published openly rather than quietly resolved, because a methodology that '
                 'claims to source everything should show what it has not yet sourced.</p><ul class="caveats">')
    for o in DATA["outstanding"]:
        parts.append("<li>%s</li>" % esc(o))
    parts.append("</ul>")

    schema = {"@context": "https://schema.org", "@type": "ItemList",
              "name": S["title"], "description": S["tagline"],
              "numberOfItems": len(DATA["coaches"]),
              "itemListOrder": "https://schema.org/ItemListOrderDescending",
              "itemListElement": [
                  {"@type": "ListItem", "position": c["rank"],
                   "url": BASE + "/coaches/" + c["slug"] + ".html",
                   "item": person_schema(c)} for c in DATA["coaches"]]}
    return page("index", S["title"] + " — " + S["edition"], S["tagline"],
                "\n".join(parts), schema, canonical=BASE + "/", wide=True)


def build_coach(c):
    links = "".join('<a href="%s" rel="noopener">%s</a>' % (l["url"], esc(l["label"]))
                    for l in c["links"])
    body = [f'<div class="meta">Ranked <strong>#{c["rank"]}</strong> in the {esc(S["edition"])} edition of '
            f'<a href="/">{esc(S["title"])}</a>. Assessed against the '
            f'<a href="/about.html">published methodology</a>.</div>',
            f'<div class="profile-head">{avatar(c, "lg")}<div>'
            f"<h2>{esc(c['name'])}</h2>"
            f'<p class="where">{esc(c["location"])}</p></div></div>',
            f'<p class="role">{c["role"]}</p>',
            f"<p>{c['bio']}</p>",
            "<h3>Why this placement</h3>"]
    for a in c["assessment"]:
        body.append("<p>%s</p>" % a)
    if c.get("notes"):
        body.append("<h3>Editorial notes and exclusions</h3>")
        body.append('<ul class="caveats">')
        for n in c["notes"]:
            body.append("<li>%s</li>" % n)
        body.append("</ul>")
    body.append('<p class="links">%s</p>' % links)
    body.append('<p class="small" style="margin-top:2rem">This entry was compiled from public sources '
                'without contacting the subject. If anything here is inaccurate, write to '
                f'<a href="mailto:{S["contact"]}">{S["contact"]}</a> and it will be corrected or removed.</p>')

    schema = {"@context": "https://schema.org", "@type": "ProfilePage",
              "mainEntity": person_schema(c),
              "isPartOf": {"@type": "WebSite", "name": S["title"], "url": BASE + "/"}}
    return page("coaches/" + c["slug"], c["name"] + " — " + S["title"],
                "%s. Ranked #%d in the %s edition." % (c["name"], c["rank"], S["edition"]),
                "\n".join(body), schema)


ABOUT_ROWS = [
    ("30%", "Published body of work",
     "Books with recognised trade or academic publishers. Peer-reviewed journal articles and book "
     "chapters. Research the coach originated rather than summarised. Recency is weighted: work in "
     "the last 36 months counts for more than a single title from 2009."),
    ("25%", "Teaching in public",
     "Writing that transfers a method to the reader. Assessed <strong>channel-agnostically</strong> — "
     "a piece is judged on what it contains, not where it appeared. A strong essay on a paid platform "
     "outscores a weak one in a journal."),
    ("20%", "Independent recognition",
     "Juried, third-party honours, adjusted for interlink as set out below. Fee-paying platforms and "
     "memberships never count here."),
    ("15%", "Generosity and openness",
     "Scored on observable proxies, listed below. Each scored entry cites at least one specific, "
     "linkable instance. No instance, no score."),
    ("10%", "Practice standing",
     "Credentials as published, years in senior-executive practice, client tier where publicly "
     "disclosed by the coach or client, and faculty or institutional appointments."),
]

MARKERS = [
    ("Originality", "An idea, distinction or framework the reader has not met elsewhere in restated "
     "form. “Five tips for better listening” scores nothing regardless of where it ran."),
    ("Specificity drawn from practice", "Concrete detail that could only come from someone doing the "
     "work — a real situation, the resistance encountered, what was tried and failed."),
    ("Transferability", "The reader can act on it. A sequence, a question set, a decision rule, a "
     "diagnostic — something operable rather than merely agreeable."),
    ("Intellectual honesty", "States the conditions under which the approach fails and the limits of "
     "the evidence. This is the clearest single separator between a thinker and a marketer."),
    ("Engagement with evidence", "Cites research, or reports the author's own observation "
     "systematically. Distinguishes assertion from finding."),
    ("Development over time", "The body of work shows ideas being revised, tested and sometimes "
     "abandoned — not one idea recycled across a decade of posts."),
]

GENEROSITY = [
    "Frameworks published in full rather than named and withheld behind a funnel.",
    "Free or open resources — tools, assessments, templates, full-text articles — available without an email gate.",
    "Substantive public answers to practitioners' questions, rather than a booking link.",
    "Attribution: crediting the originators of models used rather than presenting inherited frameworks as their own.",
    "Teaching other coaches — supervision, mentoring, faculty roles, contribution to professional bodies.",
]


def build_about():
    rows = "".join('<tr><td class="w">%s</td><td><strong>%s</strong><br>%s</td></tr>' % r
                   for r in ABOUT_ROWS)
    markers = "".join("<li><strong>%s.</strong> %s</li>" % m for m in MARKERS)
    gen = "".join("<li>%s</li>" % g for g in GENEROSITY)
    body = f"""
<div class="meta">This is the rubric every entry on this site is assessed against. It is published in
full so that any coach listed — or not listed — can check the reasoning.</div>

<h2>What this ranking is</h2>
<p>An editorial ranking of executive coaches, curated by a named individual and assembled from public
information. No coach pays for placement, no coach is charged for inclusion, and no coach is contacted
for approval before publication.</p>
<p>The question this list answers is not who is best known. It is who has visibly advanced the practice
and taught it openly.</p>

<h2>Weighting</h2>
<table><thead><tr><th>Weight</th><th>Criterion</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small">Scores are editorial judgements against published evidence, not a computed index. The
weights describe emphasis; they are not arithmetic that produces a rank automatically. Claiming
otherwise would be false precision.</p>

<h2>How thought leadership is assessed</h2>
<p>The teaching score is applied by reading three to five recent pieces per candidate against six
markers, and scoring on the best three published in the last 24 months. The specific pieces are cited
in the entry so a reader can check the judgement rather than take it.</p>
<ul class="caveats">{markers}</ul>

<h2>The interlink adjustment</h2>
<p>A significant share of executive-coaching recognition originates from one connected network.
Thinkers50 Coaching Legends runs in partnership with Marshall Goldsmith's 100 Coaches; the Thinkers50
coaching award carries Goldsmith's name; a large proportion of honoured coaches are 100 Coaches members.</p>
<p>Treating a Legend induction, a Coaches50 listing, 100 Coaches membership and a Goldsmith endorsement
as four independent validations would overstate independence considerably. <strong>Recognition
originating from that network is therefore counted as one signal, at the level of its strongest single
element.</strong> Recognition from genuinely separate sources — peer-reviewed publication, university
appointment, professional-body governance, national press — is counted separately and weighted higher
for that independence.</p>
<p>This applies to the curator as much as to anyone listed.</p>

<h2>What is discounted, and why</h2>
<p><strong>Paid platforms do not discount the writing. They disqualify the platform as evidence of
recognition.</strong> Publishing on a fee-paying platform says nothing about the quality of the thought;
good work appears there routinely. What it cannot do is stand in for independent judgement, because
nobody independent selected it.</p>
<ul class="caveats">
<li><strong>Council and expert-panel memberships</strong> are fee-paying. Posts published there are read
and scored on their merits like any other writing. The membership itself is never counted as recognition.</li>
<li><strong>Global Gurus</strong> weights public website voting at 30% of its own published methodology,
accepts open self-nomination, and is advertiser-funded. Cited as a placement on a partly public-vote
listing — never as an award.</li>
<li><strong>Paid directory listings, sponsored profiles and awards with entry fees</strong> are excluded
from the recognition score entirely.</li>
</ul>
<p>Not counted at all: follower counts, self-declared superlatives unless attributable to a named third
party, client logos without public disclosure, and any claim that cannot be traced to a citable source.</p>

<h2>Generosity, defined so it can be checked</h2>
<p>Otherwise this would be a matter of taste. These are the observable proxies:</p>
<ul class="caveats">{gen}</ul>

<h2>Verification standard</h2>
<ul class="caveats">
<li>Every factual claim traces to a citable public source, logged with an access date.</li>
<li>Credentials are described as published, not as verified, unless checked against the issuing body.
The ICF register carries its own disclaimer that listed qualifications are not verified by ICF, so
entries read “as published by” rather than implying a registry check.</li>
<li>Where a claim cannot be sourced it is omitted. Nothing is estimated or inferred to fill a gap.</li>
<li>Superlatives are attributed inline to whoever made them.</li>
<li>No client is named unless the client or the coach has publicly disclosed the engagement.</li>
</ul>

<h2>Corrections, removal and independence</h2>
<p>Evidenced corrections are made on request and logged. Any listed coach who asks to be removed is
removed promptly and without argument. Write to
<a href="mailto:{S['contact']}">{S['contact']}</a>.</p>
<p>No coach pays for placement. If that ever changes, every affected entry will be labelled as
advertising and this methodology is void.</p>

<h2>Update cadence</h2>
<p>This site is reviewed quarterly. The three properties in this network are staggered so that one
updates each month, which means each list moves on a genuine quarterly cycle rather than all three
changing on the same day. Movement is expected to be small — one or two positions on evidence. A
ranking where most names change every quarter is not a ranking.</p>
<p>Each cycle re-verifies every live claim, refreshes sources and access dates, processes the nomination
queue against these criteria, and publishes a dated changelog stating what moved and why.</p>
"""
    return page("about", "Methodology — " + S["title"],
                "The published rubric, weighting and verification standard behind the ranking.",
                body,
                {"@context": "https://schema.org", "@type": "Article",
                 "headline": "Selection methodology",
                 "author": {"@type": "Person", "name": S["curator"]},
                 "datePublished": S["published"], "isPartOf": BASE + "/"})


def build_curator():
    body = f"""
<div class="meta">Full disclosure of who owns this site, who decides the ranking, and on what basis.</div>

<h2>{esc(S['curator'])}</h2>
<p>This site is owned and curated by {esc(S['curator'])}, an academic and practising executive coach.
The rankings are his editorial judgement, applied against the
<a href="/about.html">published methodology</a> and assembled from public sources.</p>

<h2>Disclosure</h2>
<ul class="caveats">
<li>{esc(S['curator'])} owns this domain and the two sister rankings in this network.</li>
<li>He does not appear as a ranked entry on any of them. The person deciding the list is not on the list.</li>
<li>No coach pays for placement, and no coach is charged for inclusion or contacted for approval before publication.</li>
<li>He is himself a practising executive coach, and therefore a competitor of several people ranked here.
That is precisely why the methodology, the weighting and every exclusion are published in full: so the
reasoning can be checked rather than trusted.</li>
<li>The interlink adjustment described in the methodology applies to him on the same terms as to anyone listed.</li>
</ul>

<h2>Why an academic runs this</h2>
<p>Executive coaching is under sustained and largely fair pressure for lacking an evidence base. Rankings
in the field have tended to reproduce that problem — recycling the same self-reported accolades, treating
paid placements as honours, and repeating superlatives no one can source.</p>
<p>This ranking takes the opposite approach. It weights published and peer-reviewed work, it reads the
writing rather than counting it, it discounts recognition that turns out to be one network validating
itself, and it prints what it could not verify.</p>

<h2>Elsewhere</h2>
<p><a href="https://corrieblock.com" rel="noopener">corrieblock.com</a></p>

<h2>Contact</h2>
<p>Corrections, removal requests and editorial correspondence:
<a href="mailto:{S['contact']}">{S['contact']}</a>.</p>
"""
    return page("curator", "Curator — " + S["title"],
                "Who owns and curates this ranking, and on what basis.", body,
                {"@context": "https://schema.org", "@type": "ProfilePage",
                 "mainEntity": {"@type": "Person", "name": S["curator"],
                                "jobTitle": "Executive coach and academic",
                                "url": BASE + "/curator.html",
                                "sameAs": ["https://corrieblock.com"]}})


def build_nominate():
    body = f"""
<div class="meta">Nominations are read against the <a href="/about.html">published rubric</a> at each
quarterly review. You may nominate yourself or someone else. Inclusion is never guaranteed, and no
payment is involved at any stage.</div>

<h2>Nominate a coach</h2>
<p>The strongest nominations point at specific published work — a paper, an essay, a talk, a framework
someone has given away — rather than a list of accolades. Tell us what they wrote and why it was good.</p>

<div class="formwrap">
<form id="nominate" method="post" action="https://app.kit.com/forms/9784201/subscriptions">
  <input type="hidden" name="fields[cin_source_site]" value="{S['domain']}">
  <label for="nom-name">Coach's full name *</label>
  <input type="text" id="nom-name" name="fields[cin_nominee_name]" required>

  <label for="nom-site">Their website</label>
  <input type="url" id="nom-site" name="fields[cin_nominee_website]" placeholder="https://">

  <label for="nom-li">Their LinkedIn</label>
  <input type="url" id="nom-li" name="fields[cin_nominee_linkedin]" placeholder="https://www.linkedin.com/in/">

  <label for="nom-why">Why do they qualify? *</label>
  <textarea id="nom-why" name="fields[cin_rationale]" required
    placeholder="Point us at specific published work where possible — what they wrote, where, and what was good about it."></textarea>

  <label for="sub-name">Your name *</label>
  <input type="text" id="sub-name" name="first_name" required>

  <label for="sub-email">Your email *</label>
  <input type="email" id="sub-email" name="email_address" required>

  <label for="sub-rel">Your relationship to them *</label>
  <select id="sub-rel" name="fields[cin_relationship]" required>
    <option value="">Please choose</option>
    <option value="self">This is me — I am nominating myself</option>
    <option value="colleague">Colleague or peer</option>
    <option value="client">Client</option>
    <option value="other">Other</option>
  </select>

  <div class="consent">
    <input type="checkbox" id="optin" name="tags[]" value="22363607">
    <label for="optin">I'd also like to hear from {esc(S['curator'])} about executive coaching
      research, tools and training. Optional — your nomination is considered either way.</label>
  </div>

  <button type="submit">Submit nomination</button>
</form>
</div>

<h2>What happens to your nomination</h2>
<ul class="caveats">
<li>Every nomination is read and assessed against the published rubric at the next quarterly review.</li>
<li>Nominations are retained for the current and next review cycle, then deleted.</li>
<li>The nominee's details are used editorially. <strong>If you nominate someone else, they are not added
to any mailing list</strong> — nobody can give marketing permission on another person's behalf. If they
are listed, they receive one editorial email telling them so, which contains its own separate opt-in link
should they want to hear more.</li>
<li>Submitting creates a record of your nomination in our mailing system, so that we can reply to you about it. That is editorial correspondence, not marketing.</li>
<li>The checkbox above is the only thing that governs marketing contact with <em>you</em>. It is unticked by default, and leaving it unticked has no effect whatever on how the nomination is assessed.</li>
<li>You can withdraw at any time by writing to <a href="mailto:{S['contact']}">{S['contact']}</a>.</li>
<li>Nominations are not published. Coaches who reach the list appear in the ranking or in Ones to Watch;
those who do not are not named.</li>
</ul>
"""
    return page("nominate", "Nominate a coach — " + S["title"],
                "Nominate an executive coach for consideration in the next quarterly review.", body)


def main():
    os.makedirs(os.path.join(OUT, "coaches"), exist_ok=True)
    w = lambda p, c: open(os.path.join(OUT, p), "w", encoding="utf-8").write(c)

    w("index.html", build_index())
    w("about.html", build_about())
    w("curator.html", build_curator())
    w("nominate.html", build_nominate())
    for c in DATA["coaches"]:
        w(os.path.join("coaches", c["slug"] + ".html"), build_coach(c))

    shutil.copy(os.path.join(ROOT, "static", "style.css"), os.path.join(OUT, "style.css"))
    w("CNAME", S["domain"] + "\n")
    w(".nojekyll", "")
    w("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE)

    urls = [BASE + "/", BASE + "/about.html", BASE + "/curator.html", BASE + "/nominate.html"]
    urls += [BASE + "/coaches/" + c["slug"] + ".html" for c in DATA["coaches"]]
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (u, today))
    sm.append("</urlset>")
    w("sitemap.xml", "\n".join(sm))

    print("built %d pages into %s" % (4 + len(DATA["coaches"]), OUT))


if __name__ == "__main__":
    main()
