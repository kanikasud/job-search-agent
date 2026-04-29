# Data Sources

## The Muse

The Muse exposes a public JSON REST API (`https://www.themuse.com/api/public/jobs`) that requires no authentication. Each listing includes title, company name, locations, categories, experience levels, and publication date; salary data is not provided. The free tier is rate-limited to approximately 500 requests per day, and pagination is handled via `page` and `per_page` query parameters.

**Endpoint:** `GET https://www.themuse.com/api/public/jobs?page=0&per_page=100`
**Auth:** none
**Key fields:** `id`, `name` (title), `company.name`, `locations`, `categories`, `levels`, `publication_date`, `refs.landing_page`
**Caveats:** no salary field; location granularity is city-level only.

---

## Remote OK

Remote OK publishes a single open JSON dump (`https://remoteok.com/api`) that returns all current listings in one response, typically 200–800 jobs. No authentication is required, but a descriptive `User-Agent` header must be set or the server returns a 403. Salary data is present on roughly 35% of listings as `salary_min`/`salary_max`; all positions are remote-only by definition.

**Endpoint:** `GET https://remoteok.com/api`
**Auth:** none (User-Agent header required)
**Key fields:** `id`, `position`, `company`, `location`, `tags`, `salary_min`, `salary_max`, `date`, `url`
**Caveats:** first element of the array is a legal-notice object, not a job; filter by presence of `slug`. Remote-only listings; no office/hybrid roles.

---

## Adzuna

Adzuna provides a free-tier REST API with broad geographic coverage and solid salary data. Credentials (`ADZUNA_APP_ID` and `ADZUNA_APP_KEY`) must be obtained from the Adzuna developer portal and stored in `.env`; the free tier allows 250 requests per hour. For India coverage use `country=in`; `country=gb` can be used as a fallback during development if the India endpoint is not yet active under the registered key.

**Endpoint:** `GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id=…&app_key=…`
**Auth:** `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` (free registration)
**Key fields:** `id`, `title`, `company.display_name`, `location.display_name`, `salary_min`, `salary_max`, `created`, `description`, `redirect_url`
**Caveats:** salary fields are present only when the original posting included them; description is truncated in search results (full text requires a separate detail call).

---

## Naukri (evaluated, not used)

Naukri was evaluated as a data source for India-focused listings. Automated access — including RSS feeds and direct HTTP requests with browser-like User-Agent headers — is actively blocked by their infrastructure (HTTP 403). It has been dropped from the pipeline; no scraping of Naukri is performed.
