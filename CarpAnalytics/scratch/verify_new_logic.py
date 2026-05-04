import os
import sys

# バックエンドディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import scraper

if __name__ == '__main__':
    print("Starting partial scrape for Hiroshima Carp...")
    scraper.scrape_real_data('c')
    print("Partial scrape complete.")
