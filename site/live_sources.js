(() => {
  "use strict";

  const LIVE_SOURCES = [
    {
      name: "Simplify — New Grad Positions",
      repo: "SimplifyJobs/New-Grad-Positions",
      branch: "dev",
      path: "README.md",
      categoryHint: "General New Grad",
      allowUnknownLocation: false,
    },
    {
      name: "SpeedyApply — 2026 SWE New Grad USA",
      repo: "speedyapply/2026-SWE-College-Jobs",
      branch: "main",
      path: "NEW_GRAD_USA.md",
      categoryHint: "Data Engineering / Software",
      allowUnknownLocation: true,
    },
    {
      name: "SpeedyApply — 2026 AI & Data New Grad USA",
      repo: "speedyapply/2026-AI-College-Jobs",
      branch: "main",
      path: "NEW_GRAD_USA.md",
      categoryHint: "Data Analysis / Data Science",
      allowUnknownLocation: true,
    },
    {
      name: "Jobright — Data Analysis New Grad",
      repo: "jobright-ai/2026-Data-Analysis-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Data Analysis / Data Science",
    },
    {
      name: "Jobright — Software Engineering New Grad",
      repo: "jobright-ai/2026-Software-Engineer-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Data Engineering / Software",
    },
    {
      name: "Jobright — Product Management New Grad",
      repo: "jobright-ai/2026-Product-Management-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Product / Program / Operations",
    },
    {
      name: "Jobright — Business Analyst New Grad",
      repo: "jobright-ai/2026-Business-Analyst-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Data Analysis / Data Science",
    },
    {
      name: "Jobright — Engineering New Grad",
      repo: "jobright-ai/2026-Engineering-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Data Engineering / Software",
    },
    {
      name: "Jobright — Consulting & Research New Grad",
      repo: "jobright-ai/2026-Consultant-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "General New Grad",
    },
    {
      name: "Jobright — Education & University New Grad",
      repo: "jobright-ai/2026-Education-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "University / Research",
    },
    {
      name: "Jobright — Public Sector New Grad",
      repo: "jobright-ai/2026-Public-Sector-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "General New Grad",
      orgType: "government",
    },
    {
      name: "Jobright — Management New Grad",
      repo: "jobright-ai/2026-Management-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Product / Program / Operations",
    },
    {
      name: "Jobright — Marketing New Grad",
      repo: "jobright-ai/2026-Marketing-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "Product / Program / Operations",
    },
    {
      name: "Jobright — Human Resources New Grad",
      repo: "jobright-ai/2026-HR-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "General New Grad",
    },
    {
      name: "Jobright — Support New Grad",
      repo: "jobright-ai/2026-Support-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "General New Grad",
    },
    {
      name: "Jobright — Design New Grad",
      repo: "jobright-ai/2026-Design-New-Grad",
      branch: "master",
      path: "README.md",
      categoryHint: "General New Grad",
    },
  ];

  const PROFILE_SKILLS = [
    ["Python", /\bpython\b/i],
    ["R", /(?:^|[^a-z])r(?:$|[^a-z])/i],
    ["SQL", /\bsql\b|mysql/i],
    ["Snakemake", /snakemake/i],
    ["Nextflow", /nextflow/i],
    ["Linux", /\blinux\b/i],
    ["Bash", /\bbash\b|shell scripting/i],
    ["Git/GitHub", /\bgit(?:hub)?\b/i],
    ["Pandas", /\bpandas\b/i],
    ["NumPy", /\bnumpy\b/i],
    ["TensorFlow", /tensorflow/i],
    ["scikit-learn", /scikit[- ]?learn|sklearn/i],
    ["JavaScript", /javascript|node\.js|typescript/i],
    ["Django", /django/i],
    ["Selenium", /selenium/i],
    ["Bioinformatics", /bioinformatics?/i],
    ["Genomics", /genomic|sequencing|rna[- ]?seq|variant|vcf\b/i],
    ["Data pipelines", /data pipeline|etl\b|workflow|orchestrat/i],
    ["Machine learning", /machine learning|\bai\b|deep learning|neural network/i],
    ["Data analysis", /data analy|analytics|statistical/i],
  ];

  const US_STATE_NAMES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma",
    "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee",
    "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia",
  ];
  const US_STATE_ABBR = /(?:^|[\s,/(\-])(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)(?=$|[\s,/)\-])/i;
  const US_MARKERS = [
    "united states", "usa", "u.s.", "remote in us", "remote - us", "remote, us", "us remote",
    "nationwide", "new york", "nyc", "brooklyn", "manhattan", "queens", "bronx",
    "san francisco", "south san francisco", "sf", "bay area", "palo alto", "menlo park",
    "mountain view", "sunnyvale", "san mateo", "redwood city", "oakland", "berkeley",
    "boston", "cambridge", "somerville", "brookline", "waltham", "watertown", "seattle",
    "bellevue", "san diego", "la jolla", "los angeles", "washington, dc", "washington, d.c.",
    "philadelphia", "chicago", "raleigh", "durham", "chapel hill", "austin", "dallas",
    "houston", "atlanta", "denver", "phoenix", "portland", "miami", "minneapolis",
    "detroit", "baltimore", "pittsburgh", "columbus", "cleveland", "salt lake city",
  ];
  const NON_US_MARKERS = [
    "canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "waterloo", "quebec",
    "united kingdom", "england", "scotland", "wales", "london", "edinburgh", "glasgow",
    "manchester", "cardiff", "ireland", "dublin", "india", "bengaluru", "bangalore", "chennai",
    "hyderabad", "singapore", "australia", "sydney", "melbourne", "germany", "berlin", "munich",
    "france", "paris", "spain", "italy", "poland", "netherlands", "amsterdam", "israel",
    "japan", "tokyo", "china", "hong kong", "taiwan", "mexico", "brazil", "argentina",
    "buenos aires", "europe", "emea", "apac", "philippines", "malaysia", "indonesia",
  ];

  const SENIOR_RE = /\b(senior|sr\.?|staff|principal|director|vice president|vp\b|head of|chief|distinguished|architect)\b/i;
  const ENTRY_RE = /\b(new grad(?:uate)?|university grad|college grad|early career|entry[- ]level|junior|associate|assistant|analyst i\b|engineer i\b|engineer 1\b|scientist i\b|scientist 1\b|0[-– ]?2 years?|graduate program|rotational)\b/i;
  const EXCLUDE_RE = /\b(intern(?:ship)?|co[- ]?op|post[- ]?doc(?:toral)?|resident physician|medical doctor|pharmacist|registered nurse|attorney|counsel)\b/i;
  const RESTRICTED_RE = /\b(firearm|ammunition|munition|weapons?|missile|ordnance|explosive|sportsbook|sports betting|casino|poker|lottery|gambling|draftkings|fanduel|betmgm|bet365|betrivers|caesars entertainment|penn entertainment|hard rock bet|pointsbet|ts\/sci|polygraph required|active security clearance)\b/i;
  const RESTRICTED_ORG_RE = /\b(anduril|aerovironment|agile defense|amentum|bae systems|belay technologies|caci|captivation software|constellation technologies|general dynamics mission systems|kbr|l3harris|leidos|lockheed martin|northrop grumman|peraton|raytheon|saalex|simventions|light & wonder|draftkings|fanduel|betmgm|caesars entertainment|penn entertainment|hard rock digital|flutter entertainment|kalshi)\b/i;
  const RESEARCH_RE = /bioinform|computational biology|genomic|sequencing|omics\b|research (assistant|associate|analyst|coordinator|technician|specialist)|clinical research|laboratory|\blab\b|scientific programmer|biostat|transcriptom|proteom|cancer research|precision medicine/i;
  const RESEARCH_ORG_RE = /university|college|school of medicine|medical school|hospital|health system|cancer (center|centre|institute)|research institute|national laborator|academy of sciences|fred hutch|dana[- ]farber|memorial sloan|mass general|brigham|nyu langone|mount sinai|rockefeller|broad institute/i;

  const HEADER_ALIASES = {
    company: ["company", "employer", "organization", "organisation"],
    title: ["role", "job title", "position", "title", "job"],
    location: ["location", "city", "office"],
    application: ["application", "apply", "link", "posting"],
    date: ["date posted", "posted", "posting age", "age", "date"],
    workplace: ["work model", "workplace", "work type", "remote"],
    salary: ["salary", "compensation", "pay"],
  };

  function clean(value) {
    return String(value ?? "")
      .replace(/<br\s*\/?\s*>/gi, " / ")
      .replace(/<[^>]*>/g, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&nbsp;/gi, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function stripMarkdown(value) {
    return clean(
      String(value ?? "")
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
        .replace(/\[([^\]]*)\]\([^)]+\)/g, "$1")
        .replace(/\*\*|__|`/g, "")
    );
  }

  function urlsIn(value) {
    const text = String(value ?? "");
    const urls = [];
    for (const match of text.matchAll(/https?:\/\/[^\s)<>'\"]+/gi)) {
      urls.push(match[0].replace(/[.,;]+$/, ""));
    }
    for (const match of text.matchAll(/href=["']([^"']+)["']/gi)) {
      urls.push(match[1]);
    }
    return [...new Set(urls)];
  }

  function normalizeUrl(value) {
    try {
      const url = new URL(String(value || ""), window.location.href);
      if (!/^https?:$/.test(url.protocol)) return "";
      [
        "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
        "gh_src", "source", "ref", "referrer",
      ].forEach((key) => url.searchParams.delete(key));
      url.hash = "";
      return url.toString();
    } catch {
      return "";
    }
  }

  function urlScore(url, applicationCell = false) {
    const value = String(url || "").toLowerCase();
    if (!value || value.startsWith("mailto:") || value.startsWith("javascript:")) return -1000;
    if (/\.(svg|png|jpg|jpeg|webp)(?:\?|$)/.test(value) || value.includes("raw.githubusercontent.com")) return -500;
    let score = applicationCell ? 10 : 0;
    if (/simplify\.jobs\/p\/|jobright\.ai\/jobs|myworkdayjobs\.com|greenhouse\.io|lever\.co|ashbyhq\.com|smartrecruiters\.com|icims\.com|workable\.com|careers\.|\/jobs?\//.test(value)) score += 55;
    if (/linkedin\.com\/company|\/about(?:\/|$)|wikipedia\.org|github\.com\/(?:simplifyjobs|jobright-ai|speedyapply)/.test(value)) score -= 35;
    return score;
  }

  function chooseUrl(values, source, applicationCell = false) {
    const candidates = [...new Set(values.map(normalizeUrl).filter(Boolean))];
    if (!candidates.length) return source.pageUrl;
    return candidates.sort((a, b) => urlScore(b, applicationCell) - urlScore(a, applicationCell))[0];
  }

  function sourceUrls(source, cacheBust = false) {
    const suffix = cacheBust ? `?refresh=${Date.now()}` : "";
    return [
      `https://raw.githubusercontent.com/${source.repo}/${source.branch}/${source.path}${suffix}`,
      `https://cdn.jsdelivr.net/gh/${source.repo}@${source.branch}/${source.path}${suffix}`,
    ];
  }

  function sourcePageUrl(source) {
    return `https://github.com/${source.repo}/blob/${source.branch}/${source.path}`;
  }

  function headerIndex(headers, field) {
    const aliases = HEADER_ALIASES[field];
    return headers.findIndex((header) => aliases.some((alias) => clean(header).toLowerCase().includes(alias)));
  }

  function splitMarkdownRow(line) {
    return String(line || "")
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split(/(?<!\\)\|/)
      .map((cell) => cell.trim());
  }

  function looksLikeSeparator(line) {
    const cells = splitMarkdownRow(line);
    return cells.length >= 2 && cells.every((cell) => /^:?-{2,}:?$/.test(cell.replace(/\s/g, "")));
  }

  function cellData(raw) {
    return { text: stripMarkdown(raw), urls: urlsIn(raw) };
  }

  function parseMarkdownTables(text, source) {
    const lines = String(text || "").replace(/\r/g, "").split("\n");
    const jobs = [];
    let previousCompany = "";
    let section = source.categoryHint;

    for (let i = 0; i < lines.length; i += 1) {
      const heading = lines[i].match(/^\s*#{2,4}\s+(.+?)\s*$/);
      if (heading) section = stripMarkdown(heading[1]);
      if (!lines[i].includes("|") || i + 1 >= lines.length || !looksLikeSeparator(lines[i + 1])) continue;

      const headers = splitMarkdownRow(lines[i]).map(stripMarkdown);
      const companyIndex = headerIndex(headers, "company");
      const titleIndex = headerIndex(headers, "title");
      if (companyIndex < 0 || titleIndex < 0) continue;
      const locationIndex = headerIndex(headers, "location");
      const applicationIndex = headerIndex(headers, "application");
      const dateIndex = headerIndex(headers, "date");
      const workplaceIndex = headerIndex(headers, "workplace");
      const salaryIndex = headerIndex(headers, "salary");

      i += 2;
      while (i < lines.length && lines[i].includes("|")) {
        const cells = splitMarkdownRow(lines[i]);
        const rawAt = (index) => (index >= 0 && index < cells.length ? cells[index] : "");
        const companyCell = cellData(rawAt(companyIndex));
        const titleCell = cellData(rawAt(titleIndex));
        const locationCell = cellData(rawAt(locationIndex));
        const applicationCell = cellData(rawAt(applicationIndex));
        const dateCell = cellData(rawAt(dateIndex));
        const workplaceCell = cellData(rawAt(workplaceIndex));
        const salaryCell = cellData(rawAt(salaryIndex));

        let company = companyCell.text.replace(/^[↳↪→]\s*/, "").trim();
        if (!company || /^[↳↪→]$/.test(companyCell.text)) company = previousCompany;
        else previousCompany = company;

        const row = makeJob(source, {
          company,
          title: titleCell.text,
          location: locationCell.text,
          workplace: workplaceCell.text,
          salary: salaryCell.text,
          postedText: dateCell.text,
          url: chooseUrl(
            applicationCell.urls.length ? applicationCell.urls : [...titleCell.urls, ...locationCell.urls, ...companyCell.urls],
            source,
            applicationCell.urls.length > 0,
          ),
          section,
        });
        if (row) jobs.push(row);
        i += 1;
      }
      i -= 1;
    }
    return jobs;
  }

  function parseHtmlTables(text, source) {
    if (!/<table[\s>]/i.test(text)) return [];
    const doc = new DOMParser().parseFromString(text, "text/html");
    const jobs = [];
    let previousCompany = "";
    doc.querySelectorAll("table").forEach((table) => {
      const rows = [...table.querySelectorAll("tr")];
      if (rows.length < 2) return;
      const headers = [...rows[0].querySelectorAll("th,td")].map((cell) => clean(cell.textContent));
      const companyIndex = headerIndex(headers, "company");
      const titleIndex = headerIndex(headers, "title");
      if (companyIndex < 0 || titleIndex < 0) return;
      const locationIndex = headerIndex(headers, "location");
      const applicationIndex = headerIndex(headers, "application");
      const dateIndex = headerIndex(headers, "date");
      const workplaceIndex = headerIndex(headers, "workplace");
      const salaryIndex = headerIndex(headers, "salary");

      rows.slice(1).forEach((row) => {
        const cells = [...row.querySelectorAll(":scope > td")];
        if (!cells.length) return;
        const missingCompany = cells.length === headers.length - 1;
        const cellAt = (index) => {
          if (index < 0) return null;
          if (missingCompany && index === companyIndex) return null;
          const adjusted = missingCompany && index > companyIndex ? index - 1 : index;
          return cells[adjusted] || null;
        };
        const info = (index) => {
          const cell = cellAt(index);
          return {
            text: clean(cell?.textContent),
            urls: cell ? [...cell.querySelectorAll("a[href]")].map((a) => a.href) : [],
          };
        };
        const companyCell = info(companyIndex);
        const titleCell = info(titleIndex);
        const locationCell = info(locationIndex);
        const applicationCell = info(applicationIndex);
        const dateCell = info(dateIndex);
        const workplaceCell = info(workplaceIndex);
        const salaryCell = info(salaryIndex);
        let company = companyCell.text.replace(/^[↳↪→]\s*/, "").trim();
        if (!company || /^[↳↪→]$/.test(companyCell.text)) company = previousCompany;
        else previousCompany = company;
        const allUrls = [...row.querySelectorAll("a[href]")].map((a) => a.href);
        const parsed = makeJob(source, {
          company,
          title: titleCell.text,
          location: locationCell.text,
          workplace: workplaceCell.text,
          salary: salaryCell.text,
          postedText: dateCell.text,
          url: chooseUrl(applicationCell.urls.length ? applicationCell.urls : allUrls.slice(1), source, applicationCell.urls.length > 0),
          section: source.categoryHint,
        });
        if (parsed) jobs.push(parsed);
      });
    });
    return jobs;
  }

  // Some repositories periodically minify their README into one long line. This
  // fallback recovers ordinary 5- and 6-column pipe tables in that case.
  function parsePipeStream(text, source) {
    const jobs = [];
    const normalized = String(text || "").replace(/\r?\n/g, " ");
    const patterns = [
      /\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|/g,
      /\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|/g,
    ];
    let previousCompany = "";
    for (const [patternIndex, pattern] of patterns.entries()) {
      for (const match of normalized.matchAll(pattern)) {
        const companyCell = cellData(match[1]);
        const titleCell = cellData(match[2]);
        const locationCell = cellData(match[3]);
        const sixColumns = patternIndex === 0;
        const salaryCell = cellData(sixColumns ? match[4] : "");
        const applicationCell = cellData(sixColumns ? match[5] : match[4]);
        const dateCell = cellData(sixColumns ? match[6] : match[5]);
        if (/^company$/i.test(companyCell.text) || /^[-: ]+$/.test(companyCell.text) || /^position|job title|role$/i.test(titleCell.text)) continue;
        let company = companyCell.text.replace(/^[↳↪→]\s*/, "").trim();
        if (!company || /^[↳↪→]$/.test(companyCell.text)) company = previousCompany;
        else previousCompany = company;
        const parsed = makeJob(source, {
          company,
          title: titleCell.text,
          location: locationCell.text,
          workplace: sixColumns ? "" : applicationCell.text,
          salary: salaryCell.text,
          postedText: dateCell.text,
          url: chooseUrl([...applicationCell.urls, ...titleCell.urls], source, applicationCell.urls.length > 0),
          section: source.categoryHint,
        });
        if (parsed) jobs.push(parsed);
      }
      if (jobs.length) break;
    }
    return jobs;
  }

  function parsePostedDate(value) {
    const text = clean(value).toLowerCase();
    if (!text || /^(n\/a|unknown|—|-)$/.test(text)) return { postedAt: null, ageDays: null };
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    let days = null;
    if (/^(today|new|just posted|0d)$/.test(text)) days = 0;
    else if (/^(yesterday|1 day ago)$/.test(text)) days = 1;
    else {
      const compact = text.replace(/\s+/g, "");
      const relative = compact.match(/^(\d+)(h|hr|hrs|d|day|days|w|wk|wks|mo|mos|month|months)$/);
      if (relative) {
        const amount = Number(relative[1]);
        if (/^h/.test(relative[2])) days = 0;
        else if (/^(d|day)/.test(relative[2])) days = amount;
        else if (/^(w|wk)/.test(relative[2])) days = amount * 7;
        else days = amount * 30;
      }
    }
    if (days !== null) {
      const date = new Date(today);
      date.setDate(date.getDate() - days);
      return { postedAt: date.toISOString().slice(0, 10), ageDays: days };
    }

    const monthDay = text.match(/\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:,?\s+(\d{4}))?/i);
    if (monthDay) {
      const monthNames = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
      const month = monthNames.findIndex((item) => monthDay[1].toLowerCase().startsWith(item));
      let year = monthDay[3] ? Number(monthDay[3]) : today.getFullYear();
      let date = new Date(year, month, Number(monthDay[2]));
      if (!monthDay[3] && date > new Date(today.getTime() + 7 * 86400000)) {
        year -= 1;
        date = new Date(year, month, Number(monthDay[2]));
      }
      days = Math.max(0, Math.floor((today - date) / 86400000));
      return { postedAt: date.toISOString().slice(0, 10), ageDays: days };
    }

    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime())) {
      days = Math.max(0, Math.floor((today - parsed) / 86400000));
      return { postedAt: parsed.toISOString().slice(0, 10), ageDays: days };
    }
    return { postedAt: null, ageDays: null };
  }

  function isUSLocation(location, allowUnknown = false) {
    const text = ` ${clean(location).toLowerCase()} `;
    if (!text.trim()) return allowUnknown;
    const hasUS = US_MARKERS.some((marker) => text.includes(marker))
      || US_STATE_NAMES.some((state) => text.includes(state))
      || US_STATE_ABBR.test(location)
      || /\bus[-\s]/i.test(location);
    if (hasUS) return true;
    if (NON_US_MARKERS.some((marker) => text.includes(marker))) return false;
    if (text.includes("remote")) return /\b(us|usa|united states|north america)\b/i.test(text);
    return allowUnknown;
  }

  function locationGroup(location) {
    const text = clean(location).toLowerCase();
    if (/remote/.test(text) && /\b(us|usa|united states|nationwide|north america)\b/.test(text)) return "Remote - US";
    if (/new york|nyc|brooklyn|manhattan|queens|bronx/.test(text)) return "New York City";
    if (/san francisco|south san francisco|\bsf\b|bay area|palo alto|menlo park|mountain view|sunnyvale|san mateo|redwood city|oakland|berkeley|san jose/.test(text)) return "San Francisco Bay Area";
    if (/boston|cambridge|somerville|brookline|waltham|watertown|burlington,? ma|dedham,? ma|methuen,? ma/.test(text)) return "Boston / Cambridge";
    if (/seattle|bellevue|redmond/.test(text)) return "Seattle";
    if (/washington,? d\.?c\.?|district of columbia|arlington,? va|mclean,? va/.test(text)) return "Washington, DC";
    if (/los angeles|glendale,? ca|santa monica|irvine|orange county/.test(text)) return "Los Angeles / Orange County";
    if (/san diego|la jolla/.test(text)) return "San Diego";
    return "Other U.S.";
  }

  function inferCategory(title, hint) {
    const text = `${title} ${hint}`.toLowerCase();
    if (/bioinform|computational biology|genomic|omics\b|sequencing|biostat|scientific programmer/.test(text)) return "Bioinformatics / Computational Biology";
    if (/research assistant|research associate|research coordinator|research technician|clinical research|laboratory|\blab\b|biology|biological|life science|molecular|cell biology|cancer research/.test(text)) return "Biology / Lab / Research";
    if (/data engineer|analytics engineer|etl\b|database engineer|data platform|business intelligence engineer/.test(text)) return "Data Engineering / Software";
    if (/data analy|data scien|business analy|bi analyst|analytics|statistic|quantitative research|machine learning|\bai\b/.test(text)) return "Data Analysis / Data Science";
    if (/software|developer|programmer|full[- ]?stack|backend|front[- ]?end|cloud engineer|qa engineer|automation engineer|systems engineer|devops|site reliability|application engineer/.test(text)) return "Data Engineering / Software";
    if (/product manager|product analy|program manager|project coordinator|operations|implementation|customer success|marketing|human resources|recruit|people operations|supply chain/.test(text)) return "Product / Program / Operations";
    if (/university|research|education/.test(String(hint).toLowerCase())) return "University / Research";
    return "General New Grad";
  }

  function isResearchRole(title, company, category) {
    const text = `${title} ${company}`;
    return RESEARCH_RE.test(text) || (RESEARCH_ORG_RE.test(company) && /research|data|bio|science|lab|clinical|programmer|analyst/i.test(title))
      || ["Bioinformatics / Computational Biology", "Biology / Lab / Research"].includes(category);
  }

  function focusFor(job) {
    const text = `${job.title} ${job.category}`.toLowerCase();
    if (/bioinform|genomic|sequencing|omics|variant/.test(text)) return "reproducible genomic analysis and translating biological data into useful findings";
    if (/cancer|oncology/.test(text)) return "data-driven cancer research and the connection between computational analysis and patient impact";
    if (/clinical research|research coordinator/.test(text)) return "careful research coordination, data quality, and clinically meaningful study outcomes";
    if (/data scien|data analy|statistic|biostat/.test(text)) return "using rigorous analysis to answer scientific and operational questions";
    if (/laboratory|\blab\b|research assistant|research technician/.test(text)) return "combining hands-on biological research with organized, reproducible data work";
    return "the team’s research questions and the way computational and biological methods support them";
  }

  function createColdEmail(job) {
    if (!job.research) return null;
    const labMatch = job.title.match(/(?:-|–|—)\s*([^,;]+\bLab)\b/i) || job.title.match(/\b([A-Z][A-Za-z'’-]+ Lab)\b/);
    const lab = labMatch ? labMatch[1].trim() : "your lab or research team";
    const recipient = labMatch ? "Dr. [Last Name]" : "[PI or Hiring Manager Name]";
    const focus = focusFor(job);
    const subject = `Interest in the ${job.title} opportunity at ${job.company}`;
    const body = [
      `Hello ${recipient},`,
      "",
      `My name is Celina Lin, and I recently completed a bachelor’s degree in Biology with a specialization in Bioinformatics at the University of Waterloo. I am reaching out about the ${job.title} opportunity at ${job.company}.`,
      "",
      `I am particularly interested in this position because it appears closely connected to ${focus}. Through my BRCA1/BRCA2 population-genomics project, I built a reproducible Python and Snakemake workflow using BCFtools and ANNOVAR to extract, annotate, and analyze variants across global populations. During two bioinformatics internships at the Ontario Institute for Cancer Research, I also developed data-driven training resources and an LLM-assisted competency-mapping pipeline.`,
      "",
      `Those experiences strengthened my interest in contributing to ${lab}, especially in a role where I could bring both biological context and practical experience with Python, R, SQL, Linux, workflow automation, and clear technical communication.`,
      "",
      "Would you be open to a 15–20 minute conversation about the lab’s current work, the priorities for this position, and what would make someone successful on the team? I would be grateful for the opportunity to learn more.",
      "",
      "Thank you for your time and consideration.",
      "",
      "Best,",
      "Celina Lin",
      "linkedin.com/in/celina-g-lin",
    ].join("\n");
    return { subject, body };
  }

  function makeId(parts) {
    const value = parts.join("|").toLowerCase();
    let hash = 2166136261;
    for (let i = 0; i < value.length; i += 1) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return `live-${(hash >>> 0).toString(36)}`;
  }

  function makeJob(source, raw) {
    const company = clean(raw.company).replace(/^[↳↪→]\s*/, "");
    const title = clean(raw.title).replace(/^[↳↪→]\s*/, "");
    const location = clean(raw.location);
    if (!company || !title || title.length < 3) return null;
    if (/^company$/i.test(company) || /^(position|job title|role)$/i.test(title)) return null;
    if (EXCLUDE_RE.test(title) || RESTRICTED_RE.test(`${title} ${company}`) || RESTRICTED_ORG_RE.test(company)) return null;
    if (/\b2027\b/.test(title) && !/2026/.test(title)) return null;
    if (SENIOR_RE.test(title) && !ENTRY_RE.test(title) && !/associate|assistant/i.test(title)) return null;
    if (!isUSLocation(location, Boolean(source.allowUnknownLocation))) return null;

    const url = normalizeUrl(raw.url || source.pageUrl);
    const { postedAt, ageDays } = parsePostedDate(raw.postedText);
    if (ageDays !== null && ageDays > 120) return null;
    const category = inferCategory(title, raw.section || source.categoryHint);
    const research = isResearchRole(title, company, category);
    const entryLevel = true;
    const text = `${title} ${raw.section || ""} ${source.categoryHint || ""}`;
    const matchedSkills = PROFILE_SKILLS.filter(([, pattern]) => pattern.test(text)).map(([name]) => name);

    let score = {
      "Bioinformatics / Computational Biology": 82,
      "Biology / Lab / Research": 72,
      "Data Analysis / Data Science": 68,
      "Data Engineering / Software": 61,
      "Product / Program / Operations": 50,
      "University / Research": 66,
      "General New Grad": 42,
    }[category] || 42;
    score += Math.min(16, matchedSkills.length * 3);
    if (ENTRY_RE.test(title)) score += 7;
    if (research) score += 5;
    const group = locationGroup(location);
    if (["San Francisco Bay Area", "New York City", "Boston / Cambridge"].includes(group)) score += 7;
    else if (group === "Remote - US") score += 4;
    if (/experienced|3\+? years?|clearance|ts\/sci|polygraph/i.test(title)) score -= 12;
    score = Math.max(20, Math.min(98, score));
    const fitTier = score >= 75 ? "Strong" : score >= 55 ? "Good" : "Stretch";
    const warnings = [];
    if (/clearance|ts\/sci|polygraph/i.test(title)) warnings.push("May require an existing U.S. security clearance");
    if (/citizen/i.test(title)) warnings.push("May have a U.S.-citizenship requirement");
    if (!postedAt) warnings.push("Posting date was not available in the source feed");
    if (url.includes("jobright.ai")) warnings.push("Aggregator link — confirm the current employer posting before applying");

    const description = `New-graduate or early-career listing collected from ${source.name}. ${title} at ${company}, located in ${location || "the United States"}.`;
    const job = {
      id: makeId([url || source.pageUrl, company, title, location]),
      title,
      company,
      location: location || "United States",
      location_group: group,
      workplace: clean(raw.workplace),
      employment_type: "Full-time",
      salary: clean(raw.salary),
      url: url || source.pageUrl,
      apply_url: url || source.pageUrl,
      source: source.name,
      source_type: "live_curated_feed",
      source_feed_url: source.pageUrl,
      org_type: source.orgType || (research ? "research" : "company"),
      research,
      curated_new_grad: true,
      entry_level: entryLevel,
      posted_at: postedAt,
      age_days: ageDays,
      posted_text: clean(raw.postedText),
      date_label: "Posted",
      category,
      secondary_categories: [],
      match_score: score,
      fit_tier: fitTier,
      matched_skills: matchedSkills,
      warnings,
      description,
      summary: description,
      fetched_at: new Date().toISOString(),
      verification_status: "Collected from a daily-maintained new-grad source; verify on the employer site",
    };
    job.cold_email = createColdEmail(job);
    return job;
  }

  function dedupeJobs(jobs) {
    const byKey = new Map();
    for (const job of jobs) {
      if (!job || !job.title || !job.company) continue;
      const normalized = normalizeUrl(job.url || job.apply_url || "");
      const key = normalized
        ? `url:${normalized.toLowerCase()}`
        : `job:${clean(job.company).toLowerCase()}|${clean(job.title).toLowerCase()}|${clean(job.location).toLowerCase()}`;
      const existing = byKey.get(key);
      if (!existing) {
        byKey.set(key, job);
        continue;
      }
      const merged = { ...existing };
      for (const field of ["salary", "workplace", "employment_type", "posted_at", "cold_email", "description", "summary"]) {
        if (!merged[field] && job[field]) merged[field] = job[field];
      }
      merged.research = Boolean(existing.research || job.research);
      merged.entry_level = Boolean(existing.entry_level || job.entry_level);
      merged.match_score = Math.max(existing.match_score || 0, job.match_score || 0);
      merged.fit_tier = merged.match_score >= 75 ? "Strong" : merged.match_score >= 55 ? "Good" : "Stretch";
      merged.matched_skills = [...new Set([...(existing.matched_skills || []), ...(job.matched_skills || [])])];
      merged.warnings = [...new Set([...(existing.warnings || []), ...(job.warnings || [])])];
      byKey.set(key, merged);
    }
    return [...byKey.values()];
  }

  async function fetchText(source, force) {
    let lastError = null;
    for (const url of sourceUrls(source, force)) {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 18000);
      try {
        const response = await fetch(url, {
          cache: "no-store",
          mode: "cors",
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        if (text.length < 100) throw new Error("Source returned too little content");
        return { text, url };
      } catch (error) {
        lastError = error?.name === "AbortError"
          ? new Error("Source timed out after 18 seconds")
          : error;
      } finally {
        window.clearTimeout(timeout);
      }
    }
    throw lastError || new Error("Source could not be fetched");
  }

  async function fetchOne(source, force = false) {
    const pageUrl = sourcePageUrl(source);
    const enrichedSource = { ...source, pageUrl };
    const started = performance.now();
    const { text, url } = await fetchText(enrichedSource, force);
    let jobs = [
      ...parseHtmlTables(text, enrichedSource),
      ...parseMarkdownTables(text, enrichedSource),
    ];
    if (!jobs.length) jobs = parsePipeStream(text, enrichedSource);
    jobs = dedupeJobs(jobs);
    return {
      jobs,
      stat: {
        source: source.name,
        status: "ok",
        fetched: jobs.length,
        endpoint: url,
        duration_ms: Math.round(performance.now() - started),
      },
    };
  }

  function historyKeys(jobs) {
    return jobs.map((job) => job.id).filter(Boolean);
  }

  function applyBrowserHistory(jobs) {
    const storageKey = "celina-job-board-known-ids-v2";
    let previous = [];
    try {
      previous = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!Array.isArray(previous)) previous = [];
    } catch {
      previous = [];
    }
    const previousSet = new Set(previous);
    const hasBaseline = previousSet.size > 0;
    let newCount = 0;
    for (const job of jobs) {
      const isNew = hasBaseline ? !previousSet.has(job.id) : (job.is_new || (Number.isFinite(job.age_days) && job.age_days <= 1));
      job.is_new = Boolean(isNew);
      if (job.is_new) newCount += 1;
    }
    try {
      localStorage.setItem(storageKey, JSON.stringify(historyKeys(jobs).slice(0, 12000)));
      localStorage.setItem("celina-job-board-last-live-sync-v2", new Date().toISOString());
    } catch {
      // Local storage can be disabled; the board still functions.
    }
    return { newCount, hadBaseline: hasBaseline };
  }

  async function fetchLiveJobFeeds(seedBoard, options = {}) {
    const seedJobs = Array.isArray(seedBoard?.jobs) ? seedBoard.jobs : [];
    const force = Boolean(options.force);
    const onProgress = typeof options.onProgress === "function" ? options.onProgress : () => {};
    const stats = [];
    const liveJobs = [];
    let completed = 0;

    const results = await Promise.allSettled(LIVE_SOURCES.map(async (source) => {
      const result = await fetchOne(source, force);
      completed += 1;
      onProgress({ completed, total: LIVE_SOURCES.length, source: source.name, fetched: result.jobs.length });
      return result;
    }));

    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        liveJobs.push(...result.value.jobs);
        stats.push(result.value.stat);
      } else {
        completed += 1;
        stats.push({
          source: LIVE_SOURCES[index].name,
          status: "error",
          fetched: 0,
          error: clean(result.reason?.message || result.reason || "Unknown fetch error"),
        });
        onProgress({ completed, total: LIVE_SOURCES.length, source: LIVE_SOURCES[index].name, fetched: 0, error: true });
      }
    });

    const jobs = dedupeJobs([...seedJobs, ...liveJobs]).filter((job) => {
      if (!job?.title || !job?.company) return false;
      if (RESTRICTED_RE.test(`${job.title} ${job.company}`) || RESTRICTED_ORG_RE.test(job.company || "")) return false;
      return true;
    });
    const history = applyBrowserHistory(jobs);
    jobs.sort((a, b) => {
      const newDelta = Number(Boolean(b.is_new)) - Number(Boolean(a.is_new));
      if (newDelta) return newDelta;
      const scoreDelta = Number(b.match_score || 0) - Number(a.match_score || 0);
      if (scoreDelta) return scoreDelta;
      return String(b.posted_at || "").localeCompare(String(a.posted_at || ""));
    });

    const okSources = stats.filter((row) => row.status === "ok");
    return {
      jobs,
      sourceStats: stats.sort((a, b) => a.source.localeCompare(b.source)),
      generatedAt: new Date().toISOString(),
      newCount: history.newCount,
      hadHistoryBaseline: history.hadBaseline,
      grossFetched: liveJobs.length,
      successfulSources: okSources.length,
      failedSources: stats.length - okSources.length,
      totalSources: stats.length,
    };
  }

  window.LIVE_JOB_SOURCES = LIVE_SOURCES;
  window.fetchLiveJobFeeds = fetchLiveJobFeeds;
})();
