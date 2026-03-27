# Replication Analysis Project

**Status:** Work in Progress (2026-03-27)

## Quick Overview

This project analyzes 2,356 academic papers from economics/social science to identify replication studies.

### Current State

- ✅ **Dataset:** 2,356 papers with metadata
- ⚠️ **Text extraction:** 36% have full text (853 papers) - needs improvement
- ⚠️ **Classification:** Two parallel approaches with massive disagreement
- 🚧 **New scraper:** Built but needs fixes (15k char limit, missing sources)

### Key Files

#### Data
- `replication_analysis_scihub_enhanced.csv` - Main dataset (2,356 papers, 30 columns)
- `outputs/replication_full.csv` - Claude classification results (all papers)
- `outputs/replication_enriched.csv` - 1,544 flagged replications
- `outputs/replication_results.xlsx` - Excel export for review

#### Scripts
- `scripts/proper_text_scraper.py` - Industrial-scale text extraction (NEW)

#### Documentation
- `docs/EXTRACTION_PIPELINE_WIP.md` - **START HERE** - Full analysis of current state
- `docs/ANALYSIS_TIMELINE.md` - Complete funnel from 15k papers → 2.4k → extraction → classification
- `docs/SCRAPING_OPTIONS.md` - Industrial scraping approaches evaluated

## Critical Issues Found

1. **Sci-Hub extraction was broken** (0.3% success vs expected 60-70%)
2. **15k character limit** truncates 52% of successfully extracted papers
3. **Classification disagreement:** GPT found 25 replications, Claude found 1,544
4. **Missing sources:** CORE.ac.uk, proper Sci-Hub, Archive.org not working yet

## Next Steps

1. Fix scraper (remove char limit, debug missing sources)
2. Re-extract all 1,503 papers missing text
3. Validate sample extractions
4. Re-run classifications with proper full text
5. Investigate classification disagreement

## For Reviewers

**Read first:** `docs/EXTRACTION_PIPELINE_WIP.md`

Key questions:
- Remove 15k char limit or increase to 100k?
- Should we register for CORE.ac.uk API key?
- Ethics of using Sci-Hub for research?
- Re-classify after fixing text, or proceed with current data?

---

**Contact:** Check session transcript or `~/.openclaw/workspace/memory/2026-03-27.md`
