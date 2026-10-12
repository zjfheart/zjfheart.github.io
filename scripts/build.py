#!/usr/bin/env python3
"""Build the dependency-free academic homepage from JSON content files."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from string import Template
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "site.json"
TALKS = ROOT / "content" / "talks.json"
RESEARCH = ROOT / "content" / "research.json"
INDEX_TEMPLATE = ROOT / "templates" / "index.html"
TALKS_TEMPLATE = ROOT / "templates" / "talks.html"
RESEARCH_TEMPLATE = ROOT / "templates" / "research.html"
DIST = ROOT / "dist"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def external_attrs(url: str) -> str:
    return ' target="_blank" rel="noreferrer"' if url.startswith(("http://", "https://")) else ""


def render_links(items: list[dict[str, str]], class_name: str = "item-links") -> str:
    return (
        f'<span class="{class_name}">'
        + " ".join(
            f'<a href="{esc(item["url"])}"{external_attrs(item["url"])}>{esc(item["label"])}</a>'
            for item in items
        )
        + "</span>"
    )


def render_proof(items: list[dict[str, str]]) -> str:
    cards = []
    for item in items:
        cards.append(
            f'''<a class="proof-card" href="{esc(item['url'])}"{external_attrs(item['url'])}>
  <span class="proof-value">{esc(item['value'])}</span>
  <span class="proof-label">{esc(item['label'])}</span>
  <span class="proof-detail">{esc(item['detail'])}</span>
</a>'''
        )
    return "\n".join(cards)


def render_experience(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f'''<a class="experience-item" href="{esc(item['url'])}"{external_attrs(item['url'])}>
  <span>{esc(item['years'])}</span><strong>{esc(item['role'])}</strong><em>{esc(item['place'])}</em><b aria-hidden="true">↗</b>
</a>'''
        for item in items
    )


def render_credentials(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f'''<a class="credential-card" href="{esc(item['url'])}"{external_attrs(item['url'])}>
  <span>{esc(item['kicker'])}</span><strong>{esc(item['title'])}</strong><p>{esc(item['detail'])}</p><b aria-hidden="true">↗</b>
</a>'''
        for item in items
    )


def render_projects(items: list[dict[str, object]]) -> str:
    cards = []
    for item in items:
        topics = "".join(f"<span>{esc(topic)}</span>" for topic in item["topics"])
        cards.append(
            f'''<a class="project-card reveal" href="research/{esc(item['slug'])}.html" aria-label="Explore {esc(item['title'])}">
  <span class="project-number">{esc(item['number'])}</span>
  <h3>{esc(item['title'])}</h3>
  <p class="project-question">{esc(item['question'])}</p>
  <p>{esc(item['description'])}</p>
  <div class="tag-list">{topics}</div>
  <span class="project-link">Explore programme <b aria-hidden="true">→</b></span>
</a>'''
        )
    return "\n".join(cards)


def render_focus_cards(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f'''<article class="research-focus-card">
  <span>{index:02d}</span><h2>{esc(item['title'])}</h2><p>{esc(item['detail'])}</p>
</article>'''
        for index, item in enumerate(items, start=1)
    )


def display_year(paper: dict[str, object]) -> str:
    return str(paper.get("displayYear") or paper["year"]).replace("-earlier", "")


def venue_mark(venue: str) -> str:
    words = venue.replace("Foundations and Trends in Privacy and Security", "FnT Privacy & Security").split()
    return " ".join(words[:3])


def render_research_papers(
    references: list[dict[str, str]],
    publications: dict[str, dict[str, object]],
    highlighted: str,
) -> str:
    cards = []
    for index, reference in enumerate(references, start=1):
        paper = publications[reference["title"]]
        award = f'<span class="award-badge">{esc(paper["award"])}</span>' if paper.get("award") else ""
        links = [{"label": "Primary source", "url": str(paper["url"])}]
        links.extend(item for item in paper.get("links", []) if item["url"] != paper["url"])
        cards.append(
            f'''<article class="research-paper">
  <a class="research-paper-visual visual-{(index - 1) % 4 + 1}" href="{esc(paper['url'])}"{external_attrs(str(paper['url']))} aria-label="Open {esc(paper['title'])}">
    <span>{esc(reference['label'])}</span><strong>{esc(display_year(paper))}</strong><em>{esc(venue_mark(str(paper['venue'])))}</em><i aria-hidden="true"></i>
  </a>
  <div class="research-paper-copy">
    <p class="research-paper-meta">{esc(display_year(paper))} · {esc(paper['venue'])} {award}</p>
    <h3><a href="{esc(paper['url'])}"{external_attrs(str(paper['url']))}>{esc(paper['title'])}</a></h3>
    <p class="research-paper-authors">{render_authors(paper['authors'], highlighted)}</p>
    <p class="research-paper-summary">{esc(reference['summary'])}</p>
    {render_links(links, 'research-paper-links')}
  </div>
</article>'''
        )
    return "\n".join(cards)


def render_research_talks(references: list[dict[str, str]], talks: dict[tuple[str, str], dict[str, str]]) -> str:
    if not references:
        return ""
    cards = []
    for reference in references:
        item = talks[(reference["date"], reference["title"])]
        video = f'<a href="{esc(item["video"])}" target="_blank" rel="noreferrer">Video ↗</a>' if item.get("video") else ""
        cards.append(
            f'''<article class="research-talk-card">
  <time datetime="{esc(item['date'])}">{esc(pretty_date(item['date']))}</time>
  <div><h3><a href="{esc(item['url'])}"{external_attrs(item['url'])}>{esc(item['title'])}</a></h3><p>{esc(item['event'])} · {esc(item['location'])}</p>{video}</div>
</article>'''
        )
    return f'''<section class="research-talks section section-soft" aria-labelledby="related-talks-title">
  <div class="shell research-inner">
    <div class="research-section-heading"><div><p class="eyebrow">Related talks</p><h2 id="related-talks-title">The programme, explained in public.</h2></div><p>Selected talks that develop or communicate this research direction.</p></div>
    <div class="research-talk-list">{''.join(cards)}</div>
    <a class="research-text-link" href="../talks.html">Browse the complete talk archive →</a>
  </div>
</section>'''


def render_research_axis(items: list[dict[str, object]], active_slug: str) -> str:
    links = []
    for item in items:
        current = item["slug"] == active_slug
        links.append(
            f'''<li{' class="is-active"' if current else ''}><a href="{esc(item['slug'])}.html"{' aria-current="page"' if current else ''}><span>{esc(item['number'])}</span><strong>{esc(item['shortTitle'])}</strong></a></li>'''
        )
    return "".join(links)


def render_research_navigation(items: list[dict[str, object]], active_slug: str) -> str:
    cards = []
    for item in items:
        current = item["slug"] == active_slug
        cards.append(
            f'''<a class="research-nav-card{' is-active' if current else ''}" href="{esc(item['slug'])}.html"{' aria-current="page"' if current else ''}>
  <span>{esc(item['number'])}</span><strong>{esc(item['shortTitle'])}</strong><small>{'Current programme' if current else 'Explore programme →'}</small>
</a>'''
        )
    return "\n".join(cards)


def render_recruitment_tracks(items: list[dict[str, str]]) -> str:
    return "\n".join(
        f'''<article class="track-card"><h3>{esc(item['title'])}</h3><p>{esc(item['detail'])}</p></article>'''
        for item in items
    )


def render_list(items: list[str]) -> str:
    return "\n".join(f"<li>{esc(item)}</li>" for item in items)


def render_people(data: dict[str, object], email: str) -> str:
    pi = data["pi"]
    cards = [
        f'''<article class="person-card person-card-pi">
  <img src="{esc(pi['image'])}" alt="Portrait of {esc(pi['name'])}" width="443" height="561" loading="lazy">
  <div><span>{esc(pi['role'])}</span><h3>{esc(pi['name'])}</h3><p>{esc(pi['focus'])}</p></div>
</article>'''
    ]
    for member in data.get("members", []):
        cards.append(
            f'''<article class="person-card">
  <img src="{esc(member['image'])}" alt="Portrait of {esc(member['name'])}" width="360" height="360" loading="lazy">
  <div><span>{esc(member['role'])}</span><h3>{esc(member['name'])}</h3><p>{esc(member['focus'])}</p></div>
</article>'''
        )
    cards.append(
        f'''<article class="person-card join-person-card">
  <span class="join-symbol" aria-hidden="true">+</span>
  <div><span>Prospective member</span><h3>Your work could begin here.</h3><p>Tell us what difficult reliability problem you want to solve.</p><a href="mailto:{esc(email)}">Start a conversation →</a></div>
</article>'''
    )
    return "\n".join(cards)


def render_authors(authors: list[str], highlighted: str) -> str:
    rendered = []
    for author in authors:
        name = esc(author)
        rendered.append(f'<strong class="author-self">{name}</strong>' if author == highlighted else name)
    return ", ".join(rendered)


def render_publications(data: dict[str, object], highlighted: str) -> tuple[str, str]:
    years = data["publicationYears"]
    by_year: dict[str, list[dict[str, object]]] = defaultdict(list)
    for paper in data["publications"]:
        by_year[paper["year"]].append(paper)

    labels = {"2020-earlier": "2020 & Earlier"}
    tabs = []
    panels = []
    for index, year in enumerate(years):
        selected = index == 0
        label = labels.get(year, year)
        tabs.append(
            f'''<button type="button" role="tab" id="tab-{esc(year)}" aria-controls="panel-{esc(year)}" aria-selected="{str(selected).lower()}" tabindex="{'0' if selected else '-1'}" data-year="{esc(year)}">{esc(label)}</button>'''
        )
        publications = []
        for paper in by_year.get(year, []):
            award = f'<span class="award-badge">{esc(paper["award"])}</span>' if paper.get("award") else ""
            display_year = f'<span class="paper-year">{esc(paper["displayYear"])}</span>' if paper.get("displayYear") else ""
            publications.append(
                f'''<article class="publication-item">
  {display_year}<h3><a href="{esc(paper['url'])}"{external_attrs(paper['url'])}>{esc(paper['title'])}</a></h3>
  <p class="publication-venue">{esc(paper['venue'])} {award}</p>
  <p class="publication-authors">{render_authors(paper['authors'], highlighted)}</p>
  {render_links(paper.get('links', []), 'publication-links')}
</article>'''
            )
        empty = '<p class="empty-state">No selected publications are listed for this year yet.</p>'
        panels.append(
            f'''<div class="publication-panel" role="tabpanel" id="panel-{esc(year)}" aria-labelledby="tab-{esc(year)}" data-publication-panel="{esc(year)}"{' hidden' if not selected else ''}>
  {''.join(publications) if publications else empty}
</div>'''
        )
    return "\n".join(tabs), "\n".join(panels)


def pretty_date(value: str) -> str:
    for fmt, out in (("%Y-%m-%d", "%d %b %Y"), ("%Y-%m", "%b %Y")):
        try:
            return dt.datetime.strptime(value, fmt).strftime(out).lstrip("0")
        except ValueError:
            pass
    return value


def render_talks(items: list[dict[str, str]]) -> str:
    cards = []
    for item in items:
        video = f'<a href="{esc(item["video"])}" target="_blank" rel="noreferrer">Video ↗</a>' if item.get("video") else ""
        cards.append(
            f'''<article class="talk-item">
  <time datetime="{esc(item['date'])}">{esc(pretty_date(item['date']))}</time>
  <div><h3><a href="{esc(item['url'])}"{external_attrs(item['url'])}>{esc(item['title'])}</a></h3><p>{esc(item['event'])} · {esc(item['location'])}</p>{video}</div>
</article>'''
        )
    return "\n".join(cards)


def render_teaching(items: list[dict[str, object]]) -> str:
    cards = []
    for item in items:
        cards.append(
            f'''<article class="teaching-card reveal">
  <span class="teaching-years">{esc(item['years'])}</span><p class="teaching-institution">{esc(item['institution'])}</p>
  <h3><a href="{esc(item['url'])}"{external_attrs(item['url'])}>{esc(item['title'])}</a></h3>
  <p>{esc(item['detail'])}</p>{render_links(item.get('links', []))}
</article>'''
        )
    return "\n".join(cards)


def render_talk_archive(items: list[dict[str, str]]) -> str:
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in items:
        by_year[item["date"][:4]].append(item)
    sections = []
    for year in sorted(by_year, reverse=True):
        rows = []
        for item in by_year[year]:
            title = esc(item["title"])
            if item.get("url"):
                title = f'<a href="{esc(item["url"])}"{external_attrs(item["url"])}>{title}</a>'
            video = f'<a class="archive-media" href="{esc(item["video"])}" target="_blank" rel="noreferrer">Video ↗</a>' if item.get("video") else ""
            rows.append(
                f'''<article class="archive-talk">
  <time datetime="{esc(item['date'])}">{esc(pretty_date(item['date']))}</time>
  <div><span>{esc(item.get('type', 'Talk'))}</span><h3>{title}</h3><p>{esc(item['event'])} · {esc(item['location'])}</p>{video}</div>
</article>'''
            )
        sections.append(f'<section class="archive-year"><h2>{year}</h2><div>{"".join(rows)}</div></section>')
    return "\n".join(sections)


def validate(data: dict[str, object], talks: list[dict[str, str]], research: dict[str, object]) -> None:
    required = {"site", "profile", "proof", "experience", "education", "engagements", "recruitment", "people", "publications", "talks", "teaching"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing content keys: {', '.join(sorted(missing))}")
    allowed_years = set(data["publicationYears"])
    unknown = {paper["year"] for paper in data["publications"]} - allowed_years
    if unknown:
        raise ValueError(f"Unknown publication years: {', '.join(sorted(unknown))}")
    if not talks:
        raise ValueError("Talk archive cannot be empty")
    directions = research.get("directions", [])
    if len(directions) != 4:
        raise ValueError("Research content must define exactly four directions")
    slugs = [item["slug"] for item in directions]
    if len(slugs) != len(set(slugs)) or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) for slug in slugs):
        raise ValueError("Research slugs must be unique lowercase URL slugs")
    publication_titles = [paper["title"] for paper in data["publications"]]
    publications = set(publication_titles)
    if len(publication_titles) != len(publications):
        raise ValueError("Publication titles must be unique because research pages reference them by title")
    talk_key_list = [(item["date"], item["title"]) for item in talks]
    talk_keys = set(talk_key_list)
    if len(talk_key_list) != len(talk_keys):
        raise ValueError("Talk date/title pairs must be unique")
    for direction in directions:
        unknown_papers = {item["title"] for item in direction["papers"]} - publications
        unknown_talks = {(item["date"], item["title"]) for item in direction.get("talks", [])} - talk_keys
        if unknown_papers:
            raise ValueError(f"Unknown publications in {direction['slug']}: {', '.join(sorted(unknown_papers))}")
        if unknown_talks:
            raise ValueError(f"Unknown talks in {direction['slug']}: {unknown_talks}")


def main() -> None:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    talk_archive_data = json.loads(TALKS.read_text(encoding="utf-8"))
    research_data = json.loads(RESEARCH.read_text(encoding="utf-8"))
    validate(data, talk_archive_data, research_data)
    site = data["site"]
    profile = data["profile"]
    about = data["about"]
    recruitment = data["recruitment"]
    directions = research_data["directions"]
    publications_by_title = {paper["title"]: paper for paper in data["publications"]}
    talks_by_key = {(item["date"], item["title"]): item for item in talk_archive_data}
    publication_tabs, publication_panels = render_publications(data, profile["name"])

    DIST.mkdir(parents=True, exist_ok=True)
    assets_out = DIST / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)

    application_subject = quote(recruitment["subject"])
    site_root = site["url"].rstrip("/")
    portrait_absolute = site_root + "/" + profile["portrait"]
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": profile["name"],
            "url": site_root + "/",
            "image": portrait_absolute,
            "email": "mailto:" + profile["email"],
            "jobTitle": profile["role"],
            "affiliation": {
                "@type": "CollegeOrUniversity",
                "name": profile["institution"],
                "url": "https://www.fudan.edu.cn/en/",
            },
            "alumniOf": [
                {"@type": "CollegeOrUniversity", "name": "National University of Singapore", "url": "https://www.nus.edu.sg/"},
                {"@type": "CollegeOrUniversity", "name": "Shandong University", "url": "https://www.sdu.edu.cn/"},
            ],
            "sameAs": [profile["scholar"], profile["orcid"], profile["github"]],
            "knowsAbout": ["Trustworthy machine learning", "Embodied intelligence", "Adversarial robustness", "AI safety"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    values = {
        "page_title": esc(site["title"]),
        "description": esc(site["description"]),
        "site_url": esc(site["url"].rstrip("/") + "/"),
        "name": esc(profile["name"]),
        "focus": esc(profile["focus"]),
        "headline": esc(profile["headline"]),
        "role": esc(profile["role"]),
        "institution": esc(profile["institution"]),
        "affiliation": esc(profile["affiliation"]),
        "summary": esc(profile["summary"]),
        "portrait_url": esc(profile["portrait"]),
        "portrait_absolute": esc(portrait_absolute),
        "portrait_alt": esc(profile["portraitAlt"]),
        "email": esc(profile["email"]),
        "address": esc(profile["address"]),
        "scholar_url": esc(profile["scholar"]),
        "orcid_url": esc(profile["orcid"]),
        "github_url": esc(profile["github"]),
        "proof_cards": render_proof(data["proof"]),
        "about_eyebrow": esc(about["eyebrow"]),
        "about_title": esc(about["title"]),
        "about_body": esc(about["body"]),
        "about_bio": esc(about["bio"]),
        "primary_items": render_experience(data["experience"] + data["education"]),
        "engagement_items": render_experience(data["engagements"]),
        "engagement_visible_count": str(min(5, len(data["engagements"]))),
        "engagement_count": str(len(data["engagements"])),
        "credential_cards": render_credentials(data["credentials"]),
        "credential_visible_count": str(min(5, len(data["credentials"]))),
        "credential_count": str(len(data["credentials"])),
        "service_editorial": esc(data["service"]["editorial"]),
        "service_conferences": esc(data["service"]["conferences"]),
        "research_title": esc(research_data["title"]),
        "research_intro": esc(research_data["intro"]),
        "project_cards": render_projects(directions),
        "recruitment_status": esc(recruitment["status"]),
        "recruitment_title": esc(recruitment["title"]),
        "recruitment_intro": esc(recruitment["intro"]),
        "recruitment_quote": esc(recruitment["quote"]),
        "recruitment_tracks": render_recruitment_tracks(recruitment["tracks"]),
        "recruitment_fit": render_list(recruitment["fit"]),
        "recruitment_apply": render_list(recruitment["apply"]),
        "recruitment_subject": esc(recruitment["subject"]),
        "application_mailto": f"mailto:{esc(profile['email'])}?subject={application_subject}",
        "people_title": esc(data["people"]["title"]),
        "people_intro": esc(data["people"]["intro"]),
        "people_cards": render_people(data["people"], profile["email"]),
        "publication_tabs": publication_tabs,
        "publication_panels": publication_panels,
        "talk_cards": render_talks(data["talks"]),
        "talk_archive_count": str(len(talk_archive_data)),
        "teaching_cards": render_teaching(data["teaching"]),
        "structured_data": structured_data,
        "year": str(dt.date.today().year),
    }

    index_output = Template(INDEX_TEMPLATE.read_text(encoding="utf-8")).substitute(values)
    (DIST / "index.html").write_text(index_output, encoding="utf-8")

    talks_values = {
        "site_url": esc(site["url"].rstrip("/")),
        "name": esc(profile["name"]),
        "talk_count": str(len(talk_archive_data)),
        "talk_year_start": min(item["date"][:4] for item in talk_archive_data),
        "talk_year_end": max(item["date"][:4] for item in talk_archive_data),
        "talk_archive": render_talk_archive(talk_archive_data),
        "year": str(dt.date.today().year),
    }
    talks_output = Template(TALKS_TEMPLATE.read_text(encoding="utf-8")).substitute(talks_values)
    (DIST / "talks.html").write_text(talks_output, encoding="utf-8")

    research_out = DIST / "research"
    research_out.mkdir(parents=True, exist_ok=True)
    research_template = Template(RESEARCH_TEMPLATE.read_text(encoding="utf-8"))
    for direction in directions:
        canonical = f"{site_root}/research/{direction['slug']}.html"
        paper_items = [publications_by_title[item["title"]] for item in direction["papers"]]
        research_structured_data = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": direction["title"],
                "description": direction["description"],
                "url": canonical,
                "isPartOf": {"@type": "WebSite", "name": profile["name"], "url": site_root + "/"},
                "breadcrumb": {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": site_root + "/"},
                        {"@type": "ListItem", "position": 2, "name": "Research", "item": site_root + "/#projects"},
                        {"@type": "ListItem", "position": 3, "name": direction["shortTitle"], "item": canonical},
                    ],
                },
                "hasPart": [
                    {"@type": "ScholarlyArticle", "name": paper["title"], "url": paper["url"]}
                    for paper in paper_items
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</", "<\\/")
        research_values = {
            "page_title": esc(f"{direction['title']} | {profile['name']}"),
            "description": esc(direction["description"]),
            "canonical": esc(canonical),
            "name": esc(profile["name"]),
            "email": esc(profile["email"]),
            "scholar_url": esc(profile["scholar"]),
            "number": esc(direction["number"]),
            "short_title": esc(direction["shortTitle"]),
            "title": esc(direction["title"]),
            "question": esc(direction["question"]),
            "overview": esc(direction["description"]),
            "topics": "".join(f"<span>{esc(topic)}</span>" for topic in direction["topics"]),
            "paper_count": str(len(direction["papers"])),
            "talk_count_item": (
                f'<span aria-hidden="true">·</span><strong>{len(direction["talks"])}</strong> directly related talks'
                if direction.get("talks")
                else ""
            ),
            "focus_cards": render_focus_cards(direction["focus"]),
            "paper_cards": render_research_papers(direction["papers"], publications_by_title, profile["name"]),
            "talks_section": render_research_talks(direction.get("talks", []), talks_by_key),
            "research_axis": render_research_axis(directions, direction["slug"]),
            "research_navigation": render_research_navigation(directions, direction["slug"]),
            "structured_data": research_structured_data,
            "year": str(dt.date.today().year),
        }
        (research_out / f"{direction['slug']}.html").write_text(research_template.substitute(research_values), encoding="utf-8")

    shutil.copy2(ROOT / "src" / "styles.css", assets_out / "styles.css")
    shutil.copy2(ROOT / "src" / "app.js", assets_out / "app.js")
    shutil.copy2(ROOT / profile["portrait"], assets_out / "jingfeng-zhang.jpg")
    shutil.copy2(ROOT / "assets" / "favicon.svg", assets_out / "favicon.svg")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "404.html").write_text(index_output, encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site['url'].rstrip('/')}/sitemap.xml\n",
        encoding="utf-8",
    )
    sitemap_research = "\n".join(
        f"  <url><loc>{html.escape(site_root + '/research/' + direction['slug'] + '.html')}</loc></url>"
        for direction in directions
    )
    (DIST / "sitemap.xml").write_text(
        f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{html.escape(site['url'].rstrip('/') + '/')}</loc></url>
  <url><loc>{html.escape(site['url'].rstrip('/') + '/talks.html')}</loc></url>
{sitemap_research}
</urlset>
''',
        encoding="utf-8",
    )
    print(f"Built homepage, talk archive, and {len(directions)} research pages in {DIST}")


if __name__ == "__main__":
    main()
