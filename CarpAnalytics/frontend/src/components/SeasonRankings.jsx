import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Trophy, Filter, ChevronDown, Award, Activity } from 'lucide-react';
import { API_URL } from '../apiBase';

const BATTING_CATEGORIES = [
  { id: 'batting_avg', label: '打率', format: (v) => v.toFixed(3), unit: '' },
  { id: 'home_runs', label: '本塁打', format: (v) => v, unit: '本' },
  { id: 'ops', label: 'OPS', format: (v) => v.toFixed(3), unit: '' },
  { id: 'hits', label: '安打', format: (v) => v, unit: '本' },
  { id: 'rbi', label: '打点', format: (v) => v, unit: '点' },
  { id: 'stolen_bases', label: '盗塁', format: (v) => v, unit: '個' },
  { id: 'triples', label: '三塁打', format: (v) => v, unit: '本' },
];

const FIELDING_CATEGORIES = [
  { id: 'putouts', label: '刺殺', format: (v) => v, unit: '' },
  { id: 'assists', label: '補殺', format: (v) => v, unit: '' },
  { id: 'errors', label: '失策', format: (v) => v, unit: '', inverse: true },
];

const PITCHING_CATEGORIES = [
  { id: 'era', label: '防御率', format: (v) => v.toFixed(2), unit: '', inverse: true },
  { id: 'wins', label: '勝利', format: (v) => v, unit: '勝', ignoreQualified: true },
  { id: 'saves', label: 'セーブ', format: (v) => v, unit: 'S', ignoreQualified: true },
  { id: 'holds', label: 'ホールド', format: (v) => v, unit: 'H', ignoreQualified: true },
  { id: 'strikeouts', label: '奪三振', format: (v) => v, unit: '個' },
];

const SeasonRankings = ({ players = [] }) => {
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [league, setLeague] = useState('Central'); // 'Central' or 'Pacific'
  const [onlyQualified, setOnlyQualified] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    fetchStats();
  }, [league]);

  const fetchStats = () => {
    setLoading(true);
    axios.get(`${API_URL}/api/season-stats`, { params: { league } })
      .then(res => {
        if (res.data.status === 'success') {
          setStats(res.data.data);
          if (res.data.last_updated) {
            setLastUpdated(new Date(res.data.last_updated).toLocaleString('ja-JP'));
          }
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  const getRankings = (category, type) => {
    let filtered = stats.filter(s => s.stat_type === type);

    if (onlyQualified && !category.ignoreQualified) {
      if (type === 'batting') {
        filtered = filtered.filter(s => {
          const pa = s.plate_appearances || 0;
          const tg = s.team_games || 0;
          // チーム試合数が取得できていない(0)場合は、安全のため規定未満として扱う
          if (tg <= 0) return false;
          return pa >= tg * 3.1;
        });
      } else {
        filtered = filtered.filter(s => {
          const ip = s.innings_pitched || 0;
          const tg = s.team_games || 0;
          if (tg <= 0) return false;
          return ip >= tg * 1.0;
        });
      }
    }

    // 値がNULLのものを除外
    filtered = filtered.filter(s => s[category.id] !== null);

    // ソート
    filtered.sort((a, b) => {
      const valA = a[category.id];
      const valB = b[category.id];
      return category.inverse ? valA - valB : valB - valA;
    });

    return filtered.slice(0, 10);
  };

  const getAreaRankings = (isPitcherCategory) => {
    let filtered = players.filter(p => {
        const isP = p.position === '投手' || (p.era !== null && p.era !== undefined);
        return isPitcherCategory ? isP : !isP;
    });
    
    // 規定フィルタの適用
    if (onlyQualified) {
      const statsMap = new Map();
      stats.forEach(s => {
        const key = `${s.player_name.replace(/[\s　]/g, '')}_${s.stat_type}`;
        statsMap.set(key, s);
      });

      filtered = filtered.filter(p => {
        const pName = p.name.replace(/[\s　]/g, '');
        const pStat = statsMap.get(`${pName}_${isPitcherCategory ? 'pitching' : 'batting'}`);
        if (!pStat) return false;
        const tg = pStat.team_games || 0;
        if (tg <= 0) return false;
        if (!isPitcherCategory) {
          return (pStat.plate_appearances || 0) >= tg * 3.1;
        } else {
          return (pStat.innings_pitched || 0) >= tg * 1.0;
        }
      });
    }

    // リーグフィルタ
    if (league === 'Central') {
       filtered = filtered.filter(p => ['広島東洋カープ', '読売ジャイアンツ', '阪神タイガース', '横浜DeNAベイスターズ', '中日ドラゴンズ', '東京ヤクルトスワローズ'].includes(p.team));
    } else {
       filtered = filtered.filter(p => ['オリックス・バファローズ', '千葉ロッテマリーンズ', '福岡ソフトバンクホークス', '東北楽天ゴールデンイーグルス', '埼玉西武ライオンズ', '北海道日本ハムファイターズ'].includes(p.team));
    }

    filtered.sort((a, b) => (b.perf_area || 0) - (a.perf_area || 0));
    
    // RankingTableのフォーマットに合わせる
    return filtered.slice(0, 10).map(p => ({
       id: p.id,
       player_name: p.name,
       team: p.team,
       perf_area: p.perf_area
    }));
  };

  if (loading && stats.length === 0) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '40px' }}>
        <div className="loading-spinner" style={{ margin: '0 auto 16px' }} />
        <p>ランキングを読み込み中…</p>
      </div>
    );
  }

  return (
    <div className="season-rankings">
      <div className="ranking-header">
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            className={`filter-btn ${league === 'Central' ? 'active' : ''}`}
            onClick={() => setLeague('Central')}
          >セ・リーグ</button>
          <button 
            className={`filter-btn ${league === 'Pacific' ? 'active' : ''}`}
            onClick={() => setLeague('Pacific')}
          >パ・リーグ</button>
          {lastUpdated && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
              最終更新: {lastUpdated}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>規定{onlyQualified ? 'ON' : 'OFF'}</span>
          <label className="switch">
            <input 
              type="checkbox" 
              checked={onlyQualified} 
              onChange={() => setOnlyQualified(!onlyQualified)} 
            />
            <span className="slider round"></span>
          </label>
        </div>
      </div>

      <div className="ranking-grid">
        <section>
          <h3 className="section-title"><Activity size={18} color="#F59E0B" /> 総合力（チャート面積）ランキング</h3>
          <div className="category-scroll">
            <RankingTable 
              category={{ id: 'perf_area', label: '野手 総合力', format: v => v, unit: '' }} 
              players={getAreaRankings(false)} 
            />
            <RankingTable 
              category={{ id: 'perf_area', label: '投手 総合力', format: v => v, unit: '' }} 
              players={getAreaRankings(true)} 
            />
          </div>
        </section>

        <section style={{ marginTop: '24px' }}>
          <h3 className="section-title"><Award size={18} color="#F59E0B" /> 打撃部門ランキング</h3>
          <div className="category-scroll">
            {BATTING_CATEGORIES.map(cat => (
              <RankingTable key={cat.id} category={cat} players={getRankings(cat, 'batting')} />
            ))}
          </div>
        </section>

        <section style={{ marginTop: '24px' }}>
          <h3 className="section-title"><Award size={18} color="#3B82F6" /> 投手部門ランキング</h3>
          <div className="category-scroll">
            {PITCHING_CATEGORIES.map(cat => (
              <RankingTable key={cat.id} category={cat} players={getRankings(cat, 'pitching')} />
            ))}
          </div>
        </section>

        <section style={{ marginTop: '24px' }}>
          <h3 className="section-title"><Award size={18} color="#10B981" /> 守備部門ランキング</h3>
          <div className="category-scroll">
            {FIELDING_CATEGORIES.map(cat => (
              <RankingTable key={cat.id} category={cat} players={getRankings(cat, 'batting')} />
            ))}
          </div>
        </section>
      </div>
      
      <style>{`
        .ranking-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          background: rgba(30, 41, 59, 0.5);
          padding: 12px 20px;
          border-radius: 12px;
          border: 1px solid var(--border-color);
        }
        .section-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 1.1rem;
          margin-bottom: 16px;
          color: var(--text-light);
        }
        .category-scroll {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
        }
        .ranking-card {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          overflow: hidden;
        }
        .ranking-card-title {
          background: rgba(51, 65, 85, 0.5);
          padding: 8px 12px;
          font-size: 0.9rem;
          font-weight: 700;
          color: var(--text-light);
          border-bottom: 1px solid var(--border-color);
        }
        .ranking-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          font-size: 0.85rem;
          transition: background 0.2s;
        }
        .ranking-item:hover {
          background: rgba(255,255,255,0.03);
        }
        .ranking-pos {
          width: 24px;
          color: var(--text-muted);
          font-weight: 700;
        }
        .ranking-item:nth-child(1) .ranking-pos { color: #F59E0B; }
        .ranking-item:nth-child(2) .ranking-pos { color: #94A3B8; }
        .ranking-item:nth-child(3) .ranking-pos { color: #B45309; }
        
        .ranking-name {
          flex: 1;
          color: var(--text-light);
        }
        .ranking-team {
          font-size: 0.7rem;
          color: var(--text-muted);
          margin-left: 6px;
        }
        .ranking-value {
          font-weight: 700;
          color: var(--accent-red);
        }

        /* Switch UI */
        .switch {
          position: relative;
          display: inline-block;
          width: 34px;
          height: 18px;
        }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider {
          position: absolute;
          cursor: pointer;
          top: 0; left: 0; right: 0; bottom: 0;
          background-color: #334155;
          transition: .4s;
        }
        .slider:before {
          position: absolute;
          content: "";
          height: 14px; width: 14px;
          left: 2px; bottom: 2px;
          background-color: white;
          transition: .4s;
        }
        input:checked + .slider { background-color: var(--accent-red); }
        input:checked + .slider:before { transform: translateX(16px); }
        .slider.round { border-radius: 34px; }
        .slider.round:before { border-radius: 50%; }
      `}</style>
    </div>
  );
};

const RankingTable = ({ category, players }) => (
  <div className="ranking-card">
    <div className="ranking-card-title">{category.label}</div>
    <div className="ranking-list">
      {players.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          該当者なし
        </div>
      ) : players.map((p, i) => (
        <div key={p.id} className="ranking-item">
          <span className="ranking-pos">{i + 1}</span>
          <span className="ranking-name">
            {p.player_name}
            <span className="ranking-team">{p.team.replace('広島東洋カープ', '広島').replace('読売ジャイアンツ', '巨人').replace('阪神タイガース', '阪神').replace('横浜DeNAベイスターズ', 'DeNA').replace('東京ヤクルトスワローズ', 'ヤクルト').replace('中日ドラゴンズ', '中日').replace('オリックス・バファローズ', 'オリ').replace('千葉ロッテマリーンズ', 'ロッテ').replace('福岡ソフトバンクホークス', 'ソフ').replace('東北楽天ゴールデンイーグルス', '楽天').replace('埼玉西武ライオンズ', '西武').replace('北海道日本ハムファイターズ', 'ハム')}</span>
          </span>
          <span className="ranking-value">{category.format(p[category.id])}{category.unit}</span>
        </div>
      ))}
    </div>
  </div>
);

export default SeasonRankings;
