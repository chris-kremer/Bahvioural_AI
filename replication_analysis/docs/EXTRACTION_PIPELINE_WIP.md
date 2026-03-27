# Replication Analysis - Text Extraction Pipeline (WIP)

**Status:** Work in Progress  
**Date:** 2026-03-27  
**Author:** Clawy (OpenClaw assistant)

---

## Executive Summary

We analyzed the existing replication dataset and discovered major quality issues with text extraction. Built and tested a new industrial-scale scraper. Current results show improvement but reveal fundamental limitations that need addressing.

**Key findings:**
- Original dataset: 2,356 papers, only 36% (853) have real full text
- Sci-Hub extraction was broken (0.3% success vs expected 60-70%)
- New scraper achieved 32% success on previously failed papers
- **Critical issue:** 15k character limit truncates 52% of successfully extracted papers

---

## Background: What We Started With

### The Dataset
- **File:** `replication_analysis_scihub_enhanced.csv`
- **Total papers:** 2,356
- **Rows:** 2,356 (after deduplication from original ~15k Scholar results)
- **Columns:** 30 (metadata + text extraction results)

### Text Extraction Quality Assessment

**Original extraction sources:**
| Source | Papers Attempted | Real Text | Success Rate |
|--------|-----------------|-----------|--------------|
| Sci-Hub | 1,489 | 5 | **0.3%** ❌ |
| OpenAlex | 421 | 420 | **99.8%** ✅ |
| Original URL | 399 | 383 | **96.0%** ✅ |
| Semantic Scholar | 21 | 21 | **100%** ✅ |
| Unpaywall | 21 | 21 | **100%** ✅ |
| Other | 5 | 3 | 60% |
| **Total** | **2,356** | **853** | **36.2%** |

**Problem identified:** The extraction pipeline was hitting Sci-Hub webpage HTML instead of using direct DOI/PDF access, resulting in 1,484 papers with useless boilerplate.

### Classification Analysis (Pre-Extraction Fix)

Two parallel classifications exist:

**1. GPT Classification (Local, March 24-25)**
- Classified: 904 papers (38% of total)
- Flagged as replications: 25 (2.8%)
- Status: Local only, not on GitHub

**2. Claude/Cowork Classification (GitHub, March 27)**
- Classified: 2,356 papers (100%)
- Flagged as replications: 1,544 (65.5%)
- Confidence: High: 72%, Medium: 18%, Low: 10%
- Status: On GitHub branch `replication-data-update`

**Massive disagreement:** 58x difference (25 vs 1,544 replications flagged)

### False Negative Example Found

Paper: "The value of money: on how childhood economic resources influence value assessments later in life"
- **Abstract clearly states:** "we used the chance to replicate the findings"
- **Claude classified as:** NOT a replication (high confidence)
- **Reason:** Abstract was truncated, only had boilerplate HTML in full_text
- **Conclusion:** Poor text quality leads to classification errors

---

## Pipeline Issues Discovered

### Issue 1: Direct PDF Links Wasted
- **204 papers** have direct `.pdf` URLs
- **59 of them (29%)** were sent to Sci-Hub instead of downloaded directly
- **Result:** Lost 58 potential successful extractions
- **Fix needed:** Prioritize direct PDF download first

### Issue 2: Sci-Hub Usage Was Wrong
- **What was done:** Hit Sci-Hub web interface, scraped HTML
- **What should happen:** Use `https://sci-hub.se/{doi}` for direct PDF access
- **Expected success rate:** 60-70% (not 0.3%)
- **Fix needed:** Proper Sci-Hub API usage with DOI/URL resolution

### Issue 3: No Size Limits for Full Papers
- **Current limit:** 15,000 characters
- **Problem:** Academic papers are typically 20k-50k+ characters
- **Result:** Truncated content, incomplete extraction
- **Fix needed:** Remove or substantially increase limit (100k+ chars)

### Issue 4: Metadata vs Full Text
- Many "successful" extractions are just repository landing pages
- Example: OpenAlex often returns metadata page HTML, not PDF content
- **Fix needed:** Better content validation before accepting extraction

---

## New Scraper Implementation

### Design Philosophy

Built `proper_text_scraper.py` with industrial-scale approach:

**Source priority (in order):**
1. **Direct PDF** - If URL ends in `.pdf`, download immediately
2. **CORE.ac.uk** - 210M+ papers, generous API limits, aggregates multiple sources
3. **Sci-Hub (proper)** - Direct DOI/URL access, not webpage scraping
4. **Internet Archive Scholar** - 25M+ papers, no rate limits
5. **OpenAlex** - Fallback for OA papers
6. **Semantic Scholar** - Final fallback

**Features:**
- Parallel processing (10 workers)
- Proper PDF extraction (PyMuPDF)
- Rate limiting & retry logic
- Comprehensive logging
- Boilerplate filtering

### Test Run Results (March 27, 13:10-13:16)

**Target:** 554 papers needing text (those with boilerplate/failed extraction)

**Results:**
| Source | Successes |
|--------|-----------|
| OpenAlex | 169 |
| Semantic Scholar | 5 |
| Direct PDF | 3 |
| **CORE.ac.uk** | 0 ⚠️ |
| **Sci-Hub** | 0 ⚠️ |
| **Archive.org** | 0 ⚠️ |
| Failed | 377 |
| **Total Success** | **177** |
| **Success Rate** | **32%** |

**Time:** 6 minutes for 554 papers (10 workers)

### Quality Assessment of Extracted Text

**Newly extracted:** 176 papers with text ≥500 chars

**Quality breakdown:**
- Likely full papers: 66 (38%)
- Uncertain quality: 49 (28%)
- Too short (<3k chars): 40 (23%)
- Partial content: 21 (12%)
- Empty: 1 (0.6%)

**Critical finding:** 92 papers (52%) hit 15,000 character limit and are truncated

**Length statistics:**
- Min: 0 chars
- Max: 15,000 chars (hard limit)
- Mean: 9,668 chars
- Median: 15,000 chars (indicates widespread truncation)

### Sample Quality Check (5 papers reviewed)

**Papers at 15k limit (truncated):**
1. "Thou shalt be given..." - Real paper content, but cut off mid-sentence
2. "How much should we trust R2..." - Real paper, truncated
3. "Replication and robustness analysis..." - Real paper, truncated

**Metadata-only extractions:**
4. "Not so far east?" - Repository landing page (5k chars), not full paper
5. "Giving according to GARP" - Citation record (1.5k chars), not paper

**Verdict:** Extraction is working but handicapped by 15k limit and metadata confusion.

---

## Critical Issues That Block Progress

### 1. Character Limit Must Be Removed/Increased
- **Current:** 15,000 chars (truncates 52% of papers)
- **Needed:** 50,000-100,000 chars minimum for full papers
- **Impact:** Without this, we can't do proper replication analysis

### 2. CORE, Sci-Hub, Archive.org Not Working
- **CORE.ac.uk:** 0 successes (demo API key might be rate-limited)
- **Sci-Hub:** 0 successes (needs testing/debugging)
- **Archive.org:** 0 successes (needs investigation)
- **Impact:** Missing 3 major sources, limiting coverage

### 3. Metadata vs PDF Confusion
- OpenAlex sometimes returns landing pages instead of PDFs
- Need better validation: check for PDF magic bytes, validate content length
- **Impact:** False positives in "success" count

---

## Next Steps (Recommended Priority)

### Phase 1: Fix Scraper Fundamentals (1-2 hours)
1. **Remove/increase character limit** to 100k
2. **Test CORE.ac.uk** with proper API key (register at core.ac.uk)
3. **Debug Sci-Hub** direct DOI access
4. **Test Archive.org** scholar search
5. **Add PDF validation** (check magic bytes, reject HTML)

### Phase 2: Re-run Extraction (2-3 hours)
1. Re-extract all 554 failed papers with fixed scraper
2. Target coverage: 70-85% (vs current 36%)
3. Save output without truncation

### Phase 3: Quality Validation
1. Random sample 10-20 papers for manual review
2. Verify full text extraction quality
3. Document success rate by source

### Phase 4: Re-Classification
1. Run both GPT and Claude classifiers on full text
2. Compare results to truncated-text classification
3. Validate against 89 ground truth replications
4. Investigate the 58x disagreement (25 vs 1,544)

---

## Files in This Commit

### Scripts
- `scripts/proper_text_scraper.py` - New industrial-scale scraper

### Documentation
- `docs/EXTRACTION_PIPELINE_WIP.md` - This document
- `docs/ANALYSIS_TIMELINE.md` - Full funnel from 15k → 2.4k → extraction → classification

### Data Files (Previous Commit)
- `replication_analysis_scihub_enhanced.csv` - Original dataset (2,356 papers)
- `outputs/replication_classifications.csv` - Claude classification results
- `outputs/replication_enriched.csv` - 1,544 flagged replications with metadata
- `outputs/replication_full.csv` - Full merged dataset
- `outputs/replication_results.xlsx` - Excel export

### Logs (Not Committed - Too Large)
- `text_scraping.log` - Detailed extraction log
- `extraction_run.log` - Console output from test run

---

## Questions for Review

1. **Character limit:** Should we remove it entirely or set to 100k?
2. **CORE.ac.uk API:** Should we register for a proper API key?
3. **Sci-Hub ethics:** Are we okay using Sci-Hub for this research?
4. **Budget/time:** How much time can we invest in improving extraction coverage?
5. **Classification:** Should we re-run classifications after fixing text, or proceed with current data?

---

## Technical Setup

### Dependencies (Python 3.x)
```bash
cd replication_analysis
python3 -m venv venv
source venv/bin/activate
pip install pymupdf requests beautifulsoup4 pandas lxml
```

### Running the Scraper
```bash
python3 scripts/proper_text_scraper.py \
  --input replication_analysis_scihub_enhanced.csv \
  --output replication_analysis_FULL_TEXT.csv \
  --parallel 10
```

### Optional: Set CORE API Key
```bash
export CORE_API_KEY="your-key-here"
```

---

## Contact

Questions or want to continue this work? Check the session transcript or memory files:
- `~/.openclaw/workspace/memory/2026-03-27.md`
- Session with Chris (Telegram), March 27, 2026, 12:00-14:00 CET

---

**Status:** Ready for review and decision on next steps.
