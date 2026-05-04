def scrape_fielding_stats(team_code: str) -> dict:
    year = 2026
    url = f'https://npb.jp/bis/{year}/stats/idf1_{team_code}.html'
    res = _get(url)
    # apparent_encodingを優先的に試す
    enc = res.apparent_encoding if res.apparent_encoding and res.apparent_encoding != 'ISO-8859-1' else 'shift_jis'
    try:
        content = res.content.decode(enc, errors='replace')
    except:
        content = res.content.decode('shift_jis', errors='replace')
    
    soup = BeautifulSoup(content, 'html.parser')
    fielding_data = {}
    
    current_pos = "Unknown"
    # ページ内の要素を順番に走査
    for elem in soup.find_all(['h3', 'h4', 'caption', 'table', 'div']):
        # 見出し系要素ならポジションを更新
        if elem.name in ['h3', 'h4', 'caption'] or 'stats_title' in elem.get('class', []):
            text = elem.text.strip()
            for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]:
                if p in text:
                    current_pos = p
                    break
            continue

        # テーブルなら現在のポジションでデータを解析
        if elem.name == 'table':
            pos_key = current_pos
            all_rows = elem.find_all('tr')
            
            # ヘッダー行の特定
            header_row = None
            for r in all_rows:
                if any(k in r.text for k in ['選手', '守備率', '刺殺']):
                    header_row = r
                    break
            
            if not header_row: continue
            cols = header_row.find_all(['th', 'td'])
            headers = [c.text.strip() for c in cols]
            rows = all_rows[all_rows.index(header_row) + 1:]
            
            for row in rows:
                tds = row.find_all(['td', 'th'])
                if len(tds) < 5: continue
                raw_name = tds[headers.index('選手')].text.strip()
                if not raw_name or raw_name in ('チーム合計', '合計'): continue
                p_name = normalize_name(raw_name)
                
                def col(key):
                    idx = headers.index(key) if key in headers else -1
                    return tds[idx].text.strip() if idx != -1 and idx < len(tds) else ''
                
                if p_name not in fielding_data:
                    fielding_data[p_name] = {'positions': {}}
                
                fielding_data[p_name]['positions'][pos_key] = {
                    'putouts': _safe_int(col('刺殺')) or 0,
                    'assists': _safe_int(col('補殺')) or 0,
                    'errors': _safe_int(col('失策')) or 0,
                    'games': _safe_int(col('試合')) or 0
                }
    return fielding_data
