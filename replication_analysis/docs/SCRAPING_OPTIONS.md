# Proper Paper Scraping Options - Industrial Scale

## The Reality Check
- Incremental API calls won't get us to 90%+ coverage
- Need bulk access or proper scraping infrastructure
- 2,356 papers is actually a **small** dataset in academic terms

---

## Option 1: Sci-Hub Proper Usage (Not What We Did)
**What we did wrong:** Hit Sci-Hub web interface → got HTML boilerplate

**What actually works:**
- **Sci-Hub API/direct links:** `https://sci-hub.se/10.1234/doi` returns PDF directly
- **LibGen/Sci-Hub torrents:** Bulk downloads (80M+ papers, 85TB archive)
- **Anna's Archive:** Sci-Hub successor, better API
- **Success rate should be:** 60-70%, not 0.3%

**Tool:** `scihub.py` library or `libgen-api`

---

## Option 2: CORE.ac.uk - Best Free Bulk Access
- **210M+ open access papers** 
- **Proper API:** https://core.ac.uk/services/api
- **Bulk download:** Can request datasets
- **Already harvests:** OpenAlex, Unpaywall, arXiv, repos
- **Rate limits:** Generous for academic use

**Why better than what we have:** Aggregates everything in one place

---

## Option 3: Internet Archive Scholar
- **25M+ papers** cached
- **Direct PDF links:** archive.org/download/...
- **No API limits** for bulk access
- **Web scraping friendly**

Query: `https://scholar.archive.org/search?q=title:"your paper"`

---

## Option 4: Europe PMC (For Economics/Social Science)
- **39M+ abstracts, many full text**
- **Good for:** Economics, social science, policy papers
- **API:** https://europepmc.org/RestfulWebService
- **Advantage:** Better coverage for non-STEM fields

---

## Option 5: Semantic Scholar Bulk Access
- **200M+ papers**
- **Free bulk datasets:** Download entire corpus
- **Better than API:** Monthly dumps available
- https://www.semanticscholar.org/product/api#Datasets

**We could:** Download their entire economics corpus, match locally

---

## Option 6: Browser Automation (Playwright/Puppeteer)
**For paywalled papers where you have institutional access:**
- Spin up headless browser
- Login once with your university credentials
- Batch download all papers
- **Time:** 2-5 sec/paper with parallelization

**Tools:** Playwright, Puppeteer, Selenium
**Legality:** Check your institution's ToS

---

## Option 7: Paper Scraping Services (Paid)
1. **Dimensions API** ($$$) - 130M+ papers
2. **Web of Science API** ($$$) - institutional access
3. **SerpAPI Scholar** (~$50/month) - wraps Google Scholar
4. **Zotero + Better BibTeX** - can batch fetch if you have access

---

## Option 8: The Nuclear Option - Distributed Scraping
**If we want ALL papers:**

1. **Spin up 10-20 cloud VMs** (AWS/DO)
2. **Rotating IPs/proxies**
3. **Headless browsers** with random user agents
4. **Parallel downloads** from multiple sources
5. **Deduplication** afterward

**Cost:** ~$50-100 for one-time scrape
**Time:** 4-6 hours for 2,356 papers
**Coverage:** 85-95%

---

## Recommended: Hybrid Approach

### Step 1: CORE.ac.uk Bulk API (Free, 30 min setup)
- Register for API key
- Query all 2,356 titles
- Get ~1,200-1,500 PDFs

### Step 2: Sci-Hub Proper (Not webpage scraping)
- Use direct DOI links: `https://sci-hub.se/{doi}`
- Python library: `pip install scihub`
- Get ~600-800 more papers

### Step 3: Internet Archive Scholar
- Scrape remaining ~200-400 papers
- Very permissive, no rate limits

### Expected total coverage: **~85-90%**

---

## The Real Question

**Do you have institutional access?**
- If YES → Browser automation is cleanest (legal, fast, complete)
- If NO → CORE + proper Sci-Hub + Archive.org

**Time investment:**
- Setup: 1-2 hours
- Running: 2-4 hours unattended
- Coverage: 85-90% (vs current 36%)

---

## What I Need to Know

1. **Do you have university/institutional access** to papers?
2. **Are you okay with Sci-Hub** (ethical/legal gray area)?
3. **Want me to set up CORE.ac.uk + proper Sci-Hub approach** right now?
4. **Or go nuclear with distributed scraping** (cloud VMs)?

Pick your poison! 🐾
