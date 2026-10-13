# Jingfeng Zhang — Academic Homepage

A fast, mobile-first, English academic homepage for Jingfeng Zhang and RISE-AI Lab. The site is deliberately dependency-free: one Python script turns the content configuration into plain HTML, CSS, and JavaScript that can be hosted directly on GitHub Pages.

## What is included

- Responsive top navigation with no fixed sidebar
- Evidence-led hero and verified recognition links
- Five-row vertical experience window and touch-friendly horizontal recognition carousel
- Four linked research programmes, each with an independent evidence-led detail page
- Detailed recruitment section and lab culture
- Extensible people directory
- Accessible, URL-aware publication filters by year
- Selected talks plus an automatically counted, legacy-compatible `/talks.html` archive
- Teaching and mentoring at Fudan, the University of Auckland, the University of Tokyo, and Ochanomizu University
- Search-engine metadata, sitemap, robots file, favicon, and custom 404 page
- GitHub Pages deployment workflow

## Project structure

```text
.
├── content/
│   ├── site.json          # Profile, recruitment, people, publications, and teaching
│   ├── research.json      # Four directions, focus areas, and selected output references
│   └── talks.json         # Complete talks archive
├── assets/
│   ├── favicon.svg
│   └── jingfeng-zhang.jpg
├── templates/
│   ├── index.html
│   ├── research.html      # Shared template for all four research pages
│   └── talks.html
├── src/
│   ├── styles.css
│   └── app.js
├── scripts/
│   └── build.py
├── dist/                  # Generated, deployable website
└── .github/workflows/pages.yml
```

## Edit content

Most updates require editing only [`content/site.json`](content/site.json):

- `profile`: identity, hero badges, affiliation, portrait, and academic profiles
- `experience` and `education`: primary appointments and degrees
- `engagements`: exchanges, visits, internships, and part-time roles
- `proof` and `credentials`: evidence shown near the top of the page
- `recruitment`: open-call copy, lab fit, and application steps
- `people.pi` and `people.members`: lab directory
- `publications`: selected publication records
- `talks`: homepage highlights
- `teaching`: teaching and mentoring cards

The build highlights the exact author name `Jingfeng Zhang` in every publication. Use the configured year keys, including `2020-earlier`, when adding papers.

The four research directions live in [`content/research.json`](content/research.json). Each direction defines its title, URL slug, research question, focus areas, and an ordered list of publication and talk references. The build resolves those references against the single publication list in `site.json` and the single archive in `talks.json`, so paper metadata is never copied into four separate places.

### Edit a research direction

Update the direction object in `content/research.json`. To feature an existing paper, add its exact title plus a short, plain-language research summary:

```json
{
  "title": "Exact title already stored in site.json",
  "label": "Short theme label",
  "summary": "One concise sentence describing why the work belongs in this direction."
}
```

To feature a talk, reference the exact `date` and `title` already stored in `content/talks.json`. Leave the `talks` array empty when there is no strong match; the entire section will then be omitted. The four generated URLs are under `dist/research/` and are added to the sitemap automatically.

### Add a lab member

Add an object to `people.members`:

```json
{
  "name": "Student Name",
  "role": "PhD Student",
  "focus": "Safe robot learning",
  "image": "assets/student-name.jpg"
}
```

Copy the image into `assets/`, then run the build.

### Add a publication

```json
{
  "year": "2026",
  "title": "Paper title",
  "authors": ["First Author", "Jingfeng Zhang", "Coauthor"],
  "venue": "Conference or Journal 2026",
  "award": "Oral",
  "url": "https://official-paper-page.example",
  "links": [
    {"label": "Paper", "url": "https://official-paper-page.example"},
    {"label": "Code", "url": "https://github.com/example/repository"}
  ]
}
```

`award` and extra links are optional. Prefer official proceedings or publisher pages over automatically merged author feeds.

## Build and preview

Python 3.9 or later is sufficient; there are no packages to install.

```bash
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 4173 --directory dist
```

Open `http://localhost:4173`. Re-run the build after each content or template change, then refresh the browser.

## Publish to `zjfheart.github.io`

1. Put this package at the root of the GitHub repository named `zjfheart.github.io`.
2. In the repository, open **Settings → Pages** and choose **GitHub Actions** as the source.
3. Push to the `main` or `master` branch. The included workflow builds and deploys `dist/` automatically.
4. Confirm the live homepage and `https://zjfheart.github.io/talks.html` after the workflow completes.

The generated `dist/` directory is included so the site can also be uploaded to any static host without running the workflow.

## Design notes

- All typography uses system fonts, avoiding blocked font services and improving loading inside WeChat.
- The visual system uses the official Fudan Blue (`#0E419C`) and Fudan Red (`#CC1A1A`) from the [Fudan University Charter](https://www.fudan.edu.cn/452/list.psp). Blue carries the structure; red is reserved for small identity and emphasis details.
- The publication colours intentionally echo the Zuxuan Wu reference: blue paper titles, green resource links, Fudan-red hover/award accents, and a compact year tab bar.
- Publication tabs support arrow keys, Home/End, and shareable URLs such as `?year=2024#publications`.
- Motion respects `prefers-reduced-motion`.

## Content review before launch

- Add verified student names and photos to `people.members` when ready.
- Confirm the current recruitment status and application instructions each admission cycle.
- Review newly added publications manually; common author databases currently merge several researchers named Jingfeng Zhang.
- When replacing the portrait, keep the filename `assets/jingfeng-zhang.jpg`. The hero preserves the image's natural aspect ratio, so use an uncropped vertical portrait with enough space around the face; at least 1024 px wide is recommended for Retina displays.

## License

Code is available under the MIT License. Portraits, biographies, publication metadata, and other personal content remain the property of their respective owners.
