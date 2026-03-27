# Replication Analysis Pipeline - Full Funnel

## 📊 Complete Overview

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Initial Scholar Extraction (2016)                  │
│ ════════════════════════════════════════════════════════════│
│ Papers extracted from Scholar: ~15,176                      │
│ (Original manual dataset had ~13,010)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─► Filtered/processed
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: High-Priority Subset for Deep Analysis             │
│ ════════════════════════════════════════════════════════════│
│ Papers selected: 2,356                                      │
│ Criteria: Unknown (84% reduction)                           │
│                                                              │
│ 📝 Manual labels added:                                     │
│    • 106 papers manually reviewed                           │
│    • 89 confirmed as replications (ground truth)            │
│    • 17 confirmed as NOT replications                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─► Full text extraction attempted
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Full Text Extraction (Multi-Source)                │
│ ════════════════════════════════════════════════════════════│
│ Extraction attempted for: 2,356 papers                      │
│                                                              │
│ Sources tried (in order of success):                        │
│   ✅ OpenAlex:          420/421  (99.8% success)            │
│   ✅ Original URL:      383/399  (96.0% success)            │
│   ✅ Semantic Scholar:   21/21   (100% success)             │
│   ✅ Unpaywall:          21/21   (100% success)             │
│   ❌ Sci-Hub:             5/1489 (0.3% success)             │
│   ⚠️  Other:              3/5    (60% success)              │
│                                                              │
│ Real full text obtained: 853 papers (36.2%)                 │
│ Boilerplate/failed:      1,503 papers (63.8%)               │
│                                                              │
│ 📁 Output: replication_analysis_scihub_enhanced.csv         │
│    (Misleading name - mostly NOT Sci-Hub!)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─► Two parallel classification paths
                            │
            ┌───────────────┴────────────────┐
            ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ PATH A: GPT              │    │ PATH B: Claude (Cowork)  │
│ Classification           │    │ Classification           │
│ ════════════════════════ │    │ ════════════════════════ │
│ Date: March 24-25, 2026  │    │ Date: March 27, 2026     │
│                          │    │                          │
│ Classified: 904 papers   │    │ Classified: 2,356 papers │
│  (38% of total)          │    │  (100% of total)         │
│                          │    │                          │
│ Flagged as replications: │    │ Flagged as replications: │
│   25 papers (2.8%)       │    │   1,544 papers (65.5%)   │
│                          │    │                          │
│ Confidence levels:       │    │ Confidence breakdown:    │
│   • High: ?              │    │   • High: 1,111 (72%)    │
│   • Medium: ?            │    │   • Medium: 273 (18%)    │
│   • Low: ?               │    │   • Low: 160 (10%)       │
│                          │    │                          │
│ 📁 Output:               │    │ 📁 Outputs:              │
│ replication_analysis_    │    │ • classifications.csv    │
│ gpt_classified.csv       │    │ • enriched.csv (1,544)   │
│                          │    │ • full.csv               │
│                          │    │ • results.xlsx           │
│                          │    │                          │
│ 📍 Location: Local only  │    │ 📍 Location: GitHub      │
│ (scholar/data/)          │    │ (branch: replication-    │
│                          │    │  data-update)            │
└──────────────────────────┘    └──────────────────────────┘
```

## 🔍 Key Insights

### Big Drop-off Points:
1. **15k → 2.4k papers** (-84%): Major filtering step (criteria unclear)
2. **2.4k → 853 with text** (-64%): Text extraction failure, mostly Sci-Hub
3. **2.4k → 904 GPT classified** (-62%): GPT only ran on subset
4. **Classification disagreement**: GPT found 25 replications (2.8%), Claude found 1,544 (65.5%)

### Data Quality:
- **Ground truth**: 89 confirmed replications (manually labeled)
- **Real full text**: Only 36% of papers have usable text
- **Best text sources**: OpenAlex (420), Original URLs (383)
- **Worst text source**: Sci-Hub (5 real papers out of 1,489 attempts)

### The Two Classifications:
| Metric | GPT (Path A) | Claude/Cowork (Path B) |
|--------|--------------|------------------------|
| Papers classified | 904 (38%) | 2,356 (100%) |
| Flagged as replications | 25 (2.8%) | 1,544 (65.5%) |
| Confidence levels | Unknown | High: 72%, Med: 18%, Low: 10% |
| Status | Local only | On GitHub, ready to merge |
| Output format | Single CSV (30 cols) | 4 files (clean + enriched) |

### Critical Questions:
1. **Why the huge disagreement?** GPT: 25 replications, Claude: 1,544
2. **What was the 15k→2.4k filter criteria?**
3. **Why did GPT only classify 904/2356 papers?**
4. **Which classification is more accurate?** (Need validation against 89 ground truth)

## 📝 Files & Locations

**Base dataset (identical everywhere):**
- `scholar/data/analysis_results/replication_analysis_scihub_enhanced.csv` (local)
- `Bahvioural_AI/replication_analysis/replication_analysis_scihub_enhanced.csv` (GitHub)

**GPT classification (local only):**
- `scholar/data/analysis_results/replication_analysis_gpt_classified.csv`

**Claude/Cowork classification (GitHub):**
- `Bahvioural_AI/replication_analysis/outputs/` (4 files)
- Branch: `replication-data-update`
- PR link: https://github.com/chris-kremer/Bahvioural_AI/pull/new/replication-data-update

## 🎯 Next Steps

1. **Validation**: Check both classifiers against 89 ground truth replications
2. **Investigation**: Why such different results? (25 vs 1,544)
3. **Text extraction**: Improve Sci-Hub extraction or replace with better sources
4. **Documentation**: Document the 15k→2.4k filtering criteria
5. **Decision**: Which classification to use as canonical?
