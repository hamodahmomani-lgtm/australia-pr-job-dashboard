# Mohammad Almomani — Academic Website

A static, dependency-free academic personal website (plain HTML/CSS/JS — no
build step, no framework). Built for GitHub Pages, Vercel or Netlify.

## Structure

```
academic-website/
├── index.html          Home
├── about.html           About
├── research.html        Research themes
├── publications.html    Publications & working papers (data-driven)
├── teaching.html         Teaching experience (data-driven)
├── conferences.html      Interactive map + Data Geography
├── cv.html               Full CV + PDF download
├── contact.html          Contact links
├── 404.html
├── css/style.css         Design system (colours, type, layout)
├── js/
│   ├── data.js           All publications / teaching / map content lives here
│   ├── main.js            Nav toggle, active-link highlighting
│   ├── publications.js   Renders publications.html from data.js
│   └── map.js             Leaflet map renderer for conferences.html
├── assets/
│   ├── images/            Headshot
│   ├── cv/                 Downloadable CV PDF
│   └── favicon.svg
├── vendor/leaflet/        Leaflet map library (vendored, no CDN dependency)
├── robots.txt, sitemap.xml
├── netlify.toml, vercel.json
```

## Editing content

- **Publications, teaching, and map pins**: edit `js/data.js` only. Each
  page reads from this single file, so adding a paper, a course, or a new
  conference city means editing one array — no HTML changes needed.
- **Bio text** (Home / About): edit the relevant `.html` file directly.
- **Contact links**: `contact.html` has placeholder `href="#"` links for
  Google Scholar, LinkedIn, ORCID, university profile and ResearchGate —
  replace with the real URLs.
- **CV PDF**: replace `assets/cv/Mohammad-Almomani-CV.pdf` with an updated
  export; the download button on `cv.html` points at that fixed filename.
- **Site URL**: replace the placeholder domain `https://mohammadalmomani.com`
  in the `<link rel="canonical">`, Open Graph tags, `robots.txt` and
  `sitemap.xml` once a real domain is chosen.

## Adding a new map pin

In `js/data.js`, add an object to the `locations` array:

```js
{
  id: "unique-id",
  city: "City",
  country: "Country",
  lat: 0.0,
  lng: 0.0,
  category: "academic" | "conference" | "industry" | "dataset",
  activities: [
    { year: "2027", org: "Institution/conference", role: "Presenter", topic: "Paper or activity title" }
  ]
}
```

The map, its legend, and the accessible location table underneath it all
update automatically.

## Local preview

No build step is required. From this directory:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Deployment

**GitHub Pages**: in the repository settings, set Pages to serve from this
folder (`academic-website/`) on the deployed branch, or configure a
workflow that publishes this folder to the `gh-pages` branch / Pages root.

**Netlify**: point the site's base directory / publish directory at
`academic-website`. `netlify.toml` is already configured with `publish = "."`
relative to that base directory.

**Vercel**: set the project's root directory to `academic-website` when
importing the repository. `vercel.json` configures response headers.

No environment variables, database, or server runtime are required — the
whole site is static files. The Leaflet map library is vendored locally
under `vendor/leaflet/` (no CDN dependency); only the map *tile images*
on the Conferences page are fetched at runtime from the CARTO basemap
service, same as any web map.
