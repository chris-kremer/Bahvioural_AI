#!/usr/bin/env python3
"""
proper_text_scraper.py - Industrial-scale paper text extraction

Strategy (in order):
1. Direct PDF download (if URL ends in .pdf)
2. CORE.ac.uk API (210M+ papers, generous limits)
3. Sci-Hub proper (direct DOI links, not web scraping)
4. Internet Archive Scholar
5. OpenAlex (fallback)
6. Semantic Scholar (fallback)

Usage:
    python3 proper_text_scraper.py --input data.csv --output output.csv --parallel 10
"""

import os
import sys
import time
import logging
import argparse
import re
import io
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any
from urllib.parse import quote, urlparse

import requests
import pandas as pd
from bs4 import BeautifulSoup

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:
    import pymupdf as fitz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('text_scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH = 15000
REQUEST_TIMEOUT = 20
RETRY_DELAY = 2
MAX_RETRIES = 3

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Sci-Hub mirrors (rotate if one fails)
SCIHUB_MIRRORS = [
    'https://sci-hub.se',
    'https://sci-hub.st', 
    'https://sci-hub.ru',
]

# CORE.ac.uk API (register at https://core.ac.uk/services/api for key)
CORE_API_KEY = os.getenv('CORE_API_KEY', '')  # Set this if you have one

class TextExtractor:
    """Extract text from PDFs and HTML"""
    
    @staticmethod
    def from_pdf(content: bytes) -> Optional[str]:
        """Extract text from PDF bytes"""
        try:
            doc = fitz.open(stream=io.BytesIO(content), filetype='pdf')
            text = ' '.join(page.get_text() for page in doc)
            doc.close()
            return TextExtractor.clean_text(text)
        except Exception as e:
            logger.debug(f"PDF extraction failed: {e}")
            return None
    
    @staticmethod
    def from_html(html: str) -> Optional[str]:
        """Extract text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove noise
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                tag.decompose()
            
            # Try to find article body
            for selector in ['.article-body', '.paper-content', '.full-text', 'article', 'main']:
                el = soup.select_one(selector)
                if el:
                    text = el.get_text(separator=' ', strip=True)
                    if len(text) > 500:
                        return TextExtractor.clean_text(text)
            
            # Fallback: get all text
            text = soup.get_text(separator=' ', strip=True)
            return TextExtractor.clean_text(text)
        except Exception as e:
            logger.debug(f"HTML extraction failed: {e}")
            return None
    
    @staticmethod
    def clean_text(text: str) -> Optional[str]:
        """Clean and truncate text"""
        if not text:
            return None
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common boilerplate patterns
        noise_patterns = [
            r'Cookie.*?Accept',
            r'JavaScript.*?enable',
            r'sci-hub[^\n]{0,100}(open|knowledge|Elbakyan)',
            r'Downloaded from.*?\d{4}',
            r'Copyright.*?reserved',
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.I | re.S)
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Must have at least 500 chars to be useful
        if len(text) < 500:
            return None
        
        return text[:MAX_TEXT_LENGTH]


class PaperScraper:
    """Main scraper coordinating all sources"""
    
    def __init__(self, session: requests.Session = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.stats = {
            'direct_pdf': 0,
            'core': 0,
            'scihub': 0,
            'archive': 0,
            'openalex': 0,
            'semantic': 0,
            'failed': 0,
        }
    
    def extract_doi(self, url: str) -> Optional[str]:
        """Extract DOI from URL"""
        if not url:
            return None
        match = re.search(r'10\.\d{4,9}/[^\s&?#"<>]+', url)
        return match.group(0).rstrip('.,;)') if match else None
    
    def fetch_url(self, url: str, is_pdf: bool = False) -> Optional[str]:
        """Fetch URL and extract text"""
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if not resp.ok:
                return None
            
            content_type = resp.headers.get('Content-Type', '').lower()
            
            if is_pdf or 'pdf' in content_type or resp.content[:5] == b'%PDF-':
                return TextExtractor.from_pdf(resp.content)
            else:
                return TextExtractor.from_html(resp.text)
        except Exception as e:
            logger.debug(f"Fetch failed for {url[:60]}: {e}")
            return None
    
    def try_direct_pdf(self, url: str) -> Optional[str]:
        """Try direct PDF download"""
        if not url or not url.lower().endswith('.pdf'):
            return None
        
        logger.debug(f"Trying direct PDF: {url[:60]}")
        text = self.fetch_url(url, is_pdf=True)
        if text:
            self.stats['direct_pdf'] += 1
            logger.info(f"✅ Direct PDF: {url[:60]}")
        return text
    
    def try_core(self, title: str) -> Optional[str]:
        """Try CORE.ac.uk API"""
        if not title:
            return None
        
        logger.debug(f"Trying CORE: {title[:60]}")
        
        try:
            # Search API
            params = {
                'q': title[:200],
                'apiKey': CORE_API_KEY or 'demo',  # Demo key for testing
                'limit': 1,
            }
            resp = self.session.get(
                'https://api.core.ac.uk/v3/search/works',
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            time.sleep(0.5)  # Rate limiting
            
            if resp.ok:
                data = resp.json()
                results = data.get('results', [])
                if results and results[0].get('downloadUrl'):
                    pdf_url = results[0]['downloadUrl']
                    text = self.fetch_url(pdf_url, is_pdf=True)
                    if text:
                        self.stats['core'] += 1
                        logger.info(f"✅ CORE: {title[:60]}")
                        return text
        except Exception as e:
            logger.debug(f"CORE API failed: {e}")
        
        return None
    
    def try_scihub(self, doi: str, url: str) -> Optional[str]:
        """Try Sci-Hub with DOI or URL (direct approach)"""
        identifier = doi or url
        if not identifier:
            return None
        
        logger.debug(f"Trying Sci-Hub: {identifier[:60]}")
        
        for mirror in SCIHUB_MIRRORS:
            try:
                # Direct DOI/URL approach
                scihub_url = f"{mirror}/{identifier}"
                
                resp = self.session.get(scihub_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                time.sleep(1)  # Be nice to Sci-Hub
                
                if resp.ok and resp.content[:5] == b'%PDF-':
                    # Got PDF directly
                    text = TextExtractor.from_pdf(resp.content)
                    if text:
                        self.stats['scihub'] += 1
                        logger.info(f"✅ Sci-Hub: {identifier[:60]}")
                        return text
                
                elif resp.ok:
                    # Parse HTML to find PDF link
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    pdf_link = soup.select_one('#pdf')
                    if pdf_link and pdf_link.get('src'):
                        pdf_url = pdf_link['src']
                        if not pdf_url.startswith('http'):
                            pdf_url = 'https:' + pdf_url if pdf_url.startswith('//') else mirror + pdf_url
                        
                        text = self.fetch_url(pdf_url, is_pdf=True)
                        if text:
                            self.stats['scihub'] += 1
                            logger.info(f"✅ Sci-Hub (embed): {identifier[:60]}")
                            return text
            except Exception as e:
                logger.debug(f"Sci-Hub {mirror} failed: {e}")
                continue
        
        return None
    
    def try_archive_org(self, title: str) -> Optional[str]:
        """Try Internet Archive Scholar"""
        if not title:
            return None
        
        logger.debug(f"Trying Archive.org: {title[:60]}")
        
        try:
            query = quote(title[:150])
            search_url = f"https://scholar.archive.org/search?q={query}"
            
            resp = self.session.get(search_url, timeout=REQUEST_TIMEOUT)
            time.sleep(0.5)
            
            if resp.ok:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Look for PDF download link
                pdf_links = soup.select('a[href*="/download/"]')
                for link in pdf_links:
                    pdf_url = link.get('href')
                    if pdf_url:
                        if not pdf_url.startswith('http'):
                            pdf_url = 'https://archive.org' + pdf_url
                        
                        text = self.fetch_url(pdf_url, is_pdf=True)
                        if text:
                            self.stats['archive'] += 1
                            logger.info(f"✅ Archive.org: {title[:60]}")
                            return text
                        break
        except Exception as e:
            logger.debug(f"Archive.org failed: {e}")
        
        return None
    
    def try_openalex(self, title: str) -> Optional[str]:
        """Try OpenAlex (fallback)"""
        if not title:
            return None
        
        logger.debug(f"Trying OpenAlex: {title[:60]}")
        
        try:
            query = quote(title[:150])
            resp = self.session.get(
                f'https://api.openalex.org/works?search={query}&per_page=1',
                timeout=REQUEST_TIMEOUT
            )
            time.sleep(1)
            
            if resp.ok:
                results = resp.json().get('results', [])
                if results:
                    work = results[0]
                    # Try all OA locations
                    for loc in work.get('locations', []):
                        if loc.get('is_oa'):
                            for url_key in ['pdf_url', 'landing_page_url']:
                                url = loc.get(url_key)
                                if url:
                                    text = self.fetch_url(url, is_pdf=url_key == 'pdf_url')
                                    if text:
                                        self.stats['openalex'] += 1
                                        logger.info(f"✅ OpenAlex: {title[:60]}")
                                        return text
        except Exception as e:
            logger.debug(f"OpenAlex failed: {e}")
        
        return None
    
    def try_semantic_scholar(self, title: str) -> Optional[str]:
        """Try Semantic Scholar (fallback)"""
        if not title:
            return None
        
        logger.debug(f"Trying Semantic Scholar: {title[:60]}")
        
        try:
            query = quote(title[:150])
            resp = self.session.get(
                f'https://api.semanticscholar.org/graph/v1/paper/search?query={query}&fields=openAccessPdf&limit=1',
                timeout=REQUEST_TIMEOUT
            )
            time.sleep(1)
            
            if resp.ok:
                data = resp.json().get('data', [])
                if data and data[0].get('openAccessPdf'):
                    pdf_url = data[0]['openAccessPdf'].get('url')
                    if pdf_url:
                        text = self.fetch_url(pdf_url, is_pdf=True)
                        if text:
                            self.stats['semantic'] += 1
                            logger.info(f"✅ Semantic Scholar: {title[:60]}")
                            return text
        except Exception as e:
            logger.debug(f"Semantic Scholar failed: {e}")
        
        return None
    
    def scrape_paper(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Try all sources in order to get text for one paper"""
        title = row.get('original_title', '')
        url = row.get('original_link', '')
        doi = self.extract_doi(url)
        
        logger.info(f"\n🔍 Processing: {title[:60]}...")
        
        # Try sources in priority order
        strategies = [
            ('Direct PDF', lambda: self.try_direct_pdf(url)),
            ('CORE', lambda: self.try_core(title)),
            ('Sci-Hub', lambda: self.try_scihub(doi, url)),
            ('Archive.org', lambda: self.try_archive_org(title)),
            ('OpenAlex', lambda: self.try_openalex(title)),
            ('Semantic Scholar', lambda: self.try_semantic_scholar(title)),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                text = strategy_func()
                if text:
                    row['extracted_full_text'] = text
                    row['text_extraction_method'] = strategy_name
                    row['text_extraction_success'] = True
                    row['full_text_length'] = len(text)
                    return row
            except Exception as e:
                logger.debug(f"{strategy_name} error: {e}")
                continue
        
        # All strategies failed
        logger.warning(f"❌ All sources failed for: {title[:60]}")
        self.stats['failed'] += 1
        row['text_extraction_success'] = False
        row['text_extraction_method'] = 'All sources failed'
        return row


def process_batch(input_file: str, output_file: str, parallel: int = 10, skip_existing: bool = True):
    """Process papers in parallel"""
    
    logger.info(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    logger.info(f"Total papers: {len(df)}")
    
    # Filter to papers needing text
    if skip_existing:
        def needs_text(text):
            if pd.isna(text) or not isinstance(text, str):
                return True
            if len(text) < 500:
                return True
            if 'sci-hub open emancipation' in text or 'sci hub to open science' in text:
                return True
            return False
        
        to_process = df[df['extracted_full_text'].apply(needs_text)].copy()
        logger.info(f"Papers needing text: {len(to_process)}")
    else:
        to_process = df.copy()
    
    if len(to_process) == 0:
        logger.info("No papers need processing!")
        return
    
    # Process in parallel
    scraper = PaperScraper()
    results = []
    
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(scraper.scrape_paper, row.to_dict()): idx 
                   for idx, row in to_process.iterrows()}
        
        completed = 0
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                if completed % 10 == 0:
                    logger.info(f"\n📊 Progress: {completed}/{len(to_process)}")
                    logger.info(f"Stats: {json.dumps(scraper.stats, indent=2)}")
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    # Merge results back
    results_df = pd.DataFrame(results)
    for idx, row in results_df.iterrows():
        orig_idx = to_process[to_process['original_title'] == row['original_title']].index[0]
        for col in ['extracted_full_text', 'text_extraction_method', 'text_extraction_success', 'full_text_length']:
            if col in row:
                df.loc[orig_idx, col] = row[col]
    
    # Save
    logger.info(f"\n💾 Saving to {output_file}...")
    df.to_csv(output_file, index=False)
    
    # Final stats
    logger.info(f"\n✅ COMPLETE!")
    logger.info(f"Final stats: {json.dumps(scraper.stats, indent=2)}")
    
    success_rate = (len(to_process) - scraper.stats['failed']) / len(to_process) * 100
    logger.info(f"Success rate: {success_rate:.1f}%")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Industrial-scale paper text extraction')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--parallel', type=int, default=10, help='Parallel workers')
    parser.add_argument('--no-skip', action='store_true', help='Process all papers (don\'t skip existing)')
    
    args = parser.parse_args()
    
    process_batch(
        args.input,
        args.output,
        parallel=args.parallel,
        skip_existing=not args.no_skip
    )
