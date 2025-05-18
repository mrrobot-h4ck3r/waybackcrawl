#!/usr/bin/env python3
"""
WaybackCrawl - Wayback Machine URL fetcher with smart categorization
Usage: python3 waybackcrawl.py <domain> [--output=results.json]
"""
import sys
import json
import re
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

class WaybackCrawl:
    CATEGORIES = {
        'js': [r'\.js(\?|$)', r'application/javascript'],
        'api': [r'/api/v[0-9]/', r'graphql', r'\.json(\?|$)'],
        'admin': [r'admin', r'dashboard', r'login', r'wp-admin'],
        'redirects': [r'url=', r'next=', r'redirect='],
        'configs': [r'\.env', r'config\.', r'\.git/']
    }

    def __init__(self, domain):
        self.domain = domain
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'WaybackCrawl/1.0'}
        self.results = {cat: [] for cat in self.CATEGORIES}
        self.results['other'] = []

    def fetch_urls(self):
        """Get URLs from Wayback Machine"""
        api_url = f"http://web.archive.org/cdx/search/cdx?url={self.domain}/*&output=json&fl=original&collapse=urlkey"
        try:
            response = self.session.get(api_url, timeout=15)
            return list(set(url[0] for url in response.json()[1:]))  # Remove duplicates
        except Exception as e:
            print(f"[-] Wayback API Error: {str(e)}")
            return []

    def categorize_url(self, url):
        """Classify URL into categories"""
        for cat, patterns in self.CATEGORIES.items():
            for pattern in patterns:
                if re.search(pattern, url, re.I):
                    return cat
        return 'other'

    def scan(self):
        """Run full scan"""
        print(f"[*] Fetching URLs for {self.domain} from Wayback Machine...")
        urls = self.fetch_urls()
        
        if not urls:
            print("[-] No URLs found")
            return False

        print(f"[*] Categorizing {len(urls)} URLs...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            for url in urls:
                category = self.categorize_url(url)
                self.results[category].append(url)

        return True

    def save_results(self, filename):
        """Save categorized results"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"[+] Results saved to {filename}")

    def print_summary(self):
        """Show quick stats"""
        print("\n[+] Discovered URLs by Category:")
        for cat, urls in self.results.items():
            if urls:
                print(f"  {cat.upper():<10}: {len(urls)} URLs")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 waybackcrawl.py <domain> [--output=results.json]")
        sys.exit(1)

    domain = sys.argv[1]
    output_file = "wayback_results.json"
    
    # Parse output filename if provided
    if len(sys.argv) > 2 and sys.argv[2].startswith("--output="):
        output_file = sys.argv[2].split("=")[1]

    scanner = WaybackCrawl(domain)
    if scanner.scan():
        scanner.save_results(output_file)
        scanner.print_summary()
