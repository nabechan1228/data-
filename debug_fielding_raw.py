import requests
from bs4 import BeautifulSoup
import sys
import os

def debug_fielding_raw():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    for i, table in enumerate(tables):
        print(f"--- Table {i} ---")
        rows = table.find_all('tr')
        if not rows: continue
        # Find header
        header = None
        for r in rows:
            if '選手' in r.text:
                header = r
                break
        if header:
            h_cols = [th.text.strip() for th in header.find_all(['th', 'td'])]
            print(f"Headers: {h_cols}")
            # Show first data row
            data_row = rows[rows.index(header)+1]
            d_cols = [td.text.strip() for td in data_row.find_all(['th', 'td'])]
            print(f"First Row: {d_cols}")
        else:
            print("No header found with '選手'")

if __name__ == "__main__":
    debug_fielding_raw()
