import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, List, Thermometer, Shield, User } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

// M-4: エラーサニタイズ（詳細情報をユーザーに表示しない）
const sanitizeError = (err) => {
  if (err?.response?.status === 429) return 'リクエストが多すぎます。しばらく待ってから再試行してください。'
  if (err?.response?.status >= 500) return 'サーバーエラーが発生しました。しばらく待ってから再試行してください。'
  if (err?.response?.status === 404) return '指定したチームのデータが見つかりません。成績更新を実行してください。'
  return '最適編成の取得に失敗しました。バックエンドが起動しているか確認してください。'
}

const TEAMS = [
  '広島東洋カープ', '阪神タイガース', '横浜DeNAベイスターズ', '読売ジャイアンツ', '東京ヤクルトスワローズ', '中日ドラゴンズ',
  'オリックス・バファローズ', '千葉ロッテマリーンズ', '福岡ソフトバンクホークス', '東北楽天ゴールデンイーグルス', '埼玉西武ライオンズ', '北海道日本ハムファイターズ'
];

const LineupOptimizer = ({ teamName, onSelectTeam }) => {
  const [lineupData, setLineupData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('field');

  useEffect(() => {
    if (teamName && teamName !== '全球団') {
      fetchLineup();
    }
  }, [teamName]);

  const fetchLineup = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/api/teams/${encodeURIComponent(teamName)}/optimized-lineup`);
      if (res.data.status === 'success') {
        setLineupData(res.data.data);
      }
    } catch (err) {
      // M-4: console.errorは残しつつ、ユーザー向けにはサニタイズしたメッセージを表示
      console.error('Failed to fetch optimized lineup:', err?.response?.status);
      setError(sanitizeError(err));
    } finally {
      setLoading(false);
    }
  };

  if (!teamName || teamName === '全球団') {
    return (
      <div className="team-selection-panel panel">
        <h3 className="panel-title"><Shield size={20} /> 分析対象の球団を選択</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>最適化エンジンが各選手のポテンシャルと今季のパフォーマンスを分析し、最高の布陣を提案します。</p>
        
        <div className="team-selection-grid">
          {TEAMS.map(team => (
            <div 
              key={team} 
              className="team-selection-card"
              onClick={() => onSelectTeam(team)}
            >
              <div className="team-card-icon">
                <Shield size={32} />
              </div>
              <div className="team-card-info">
                <div className="team-card-name">{team}</div>
                <div className="team-card-action">分析を表示 →</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="loading-spinner-container"><div className="loading-spinner" /></div>;
  }

  if (error) {
    return <div className="error-msg">{error}</div>;
  }

  if (!lineupData) return null;

  const { defensive_lineup, batting_order, pitching_staff } = lineupData;

  // 守備位置の座標定義 (0-100%) - より広範囲に分散
  const positionCoords = {
    '投手': { top: '65%', left: '50%' },
    '捕手': { top: '92%', left: '50%' },
    '一塁手': { top: '56%', left: '80%' },
    '二塁手': { top: '40%', left: '65%' },
    '三塁手': { top: '56%', left: '20%' },
    '遊撃手': { top: '40%', left: '35%' },
    '左翼手': { top: '22%', left: '15%' },
    '中堅手': { top: '10%', left: '50%' },
    '右翼手': { top: '22%', left: '85%' },
    '外野手1': { top: '22%', left: '15%' },
    '外野手2': { top: '10%', left: '50%' },
    '外野手3': { top: '22%', left: '85%' },
  };

  return (
    <div className="lineup-optimizer-container">
      <div className="lineup-optimizer-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="tab-switcher" style={{ display: 'inline-flex' }}>
          <button 
            className={`tab-btn ${activeTab === 'field' ? 'active' : ''}`}
            onClick={() => setActiveTab('field')}
          >
            <Shield size={16} /> 野手編成
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pitchers' ? 'active' : ''}`}
            onClick={() => setActiveTab('pitchers')}
          >
            <Target size={16} /> 投手編成
          </button>
        </div>
        
        <button 
          className="filter-btn" 
          onClick={() => onSelectTeam('全球団')}
          style={{ fontSize: '0.8rem' }}
        >
          ← 球団選択に戻る
        </button>
      </div>

      {activeTab === 'field' && (
        <div className="lineup-grid">
          {/* 左側: フィールドビュー */}
        <div className="field-panel panel">
          <h3 className="panel-title"><Shield size={18} /> Optimized Defense</h3>
          <div className="baseball-field">
            <div className="infield-dirt" />
            <div className="infield-grass" />
            <div className="pitchers-mound">
              <div className="pitchers-plate" />
            </div>
            <div className="home-plate" />
            <div className="base first" style={{ top: '50%', left: '72%', transform: 'rotate(45deg)' }} />
            <div className="base second" style={{ top: '28%', left: '50%', transform: 'rotate(45deg)' }} />
            <div className="base third" style={{ top: '50%', left: '28%', transform: 'rotate(45deg)' }} />
            
            {Object.entries(defensive_lineup).map(([pos, player]) => {
              const coords = positionCoords[pos] || { top: '50%', left: '50%' };
              return (
                <div 
                  key={pos} 
                  className="field-player-marker"
                  style={{ top: coords.top, left: coords.left }}
                >
                  <div className="marker-image-wrapper">
                    {player.image_url ? (
                      <img src={player.image_url} alt={player.name} className="marker-image" />
                    ) : (
                      <User size={20} />
                    )}
                  </div>
                  <div className="marker-badge">{pos.replace(/[0-9]/, '')}</div>
                  <div className="marker-name">{player.name}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 右側: 打順リスト */}
        <div className="order-panel panel">
          <h3 className="panel-title"><List size={18} /> Batting Order</h3>
          <div className="order-list">
            <table className="lineup-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>選手名</th>
                  <th>位置</th>
                  <th>打率</th>
                  <th>OPS</th>
                </tr>
              </thead>
              <tbody>
                {batting_order.map((item) => (
                  <tr key={item.order}>
                    <td className="order-num">{item.order}</td>
                    <td className="order-name">{item.name}</td>
                    <td className="order-pos">{item.position.replace(/[0-9]/, '')}</td>
                    <td>{item.avg.toFixed(3)}</td>
                    <td className="highlight">{item.ops.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        </div>
      )}

      {/* 投手陣タブ */}
      {activeTab === 'pitchers' && (
        <div className="pitcher-panel panel">
          <h3 className="panel-title"><Target size={18} /> Pitching Staff</h3>
          <div className="pitcher-groups">
            <div className="pitcher-group">
              <h4>先発ローテーション</h4>
              <div className="pitcher-cards">
                {pitching_staff.starters.map((p, i) => (
                  <div key={i} className="premium-pitcher-card starter">
                    <div className="pitcher-image-wrapper">
                      {p.image_url ? (
                        <img src={p.image_url} alt={p.name} className="pitcher-image" />
                      ) : (
                        <User size={40} className="pitcher-placeholder" />
                      )}
                      <div className="pitcher-rank">{i + 1}</div>
                    </div>
                    <div className="pitcher-info">
                      <div className="pitcher-name">{p.name}</div>
                      <div className="pitcher-stats-grid">
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">ERA</span>
                          <span className={`pitcher-stat-value ${p.era < 3.0 ? 'excellent' : ''}`}>{p.era === 9.99 ? '-' : p.era?.toFixed(2)}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">WINS</span>
                          <span className={`pitcher-stat-value ${p.wins >= 10 ? 'excellent' : ''}`}>{p.wins}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">IP</span>
                          <span className="pitcher-stat-value">{p.ip}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">GAMES</span>
                          <span className="pitcher-stat-value">{p.games}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="pitcher-group">
              <h4>リリーフ・中継ぎ</h4>
              <div className="pitcher-cards">
                {pitching_staff.relievers.map((p, i) => (
                  <div key={i} className="premium-pitcher-card reliever">
                    <div className="pitcher-image-wrapper">
                      {p.image_url ? (
                        <img src={p.image_url} alt={p.name} className="pitcher-image" />
                      ) : (
                        <User size={40} className="pitcher-placeholder" />
                      )}
                    </div>
                    <div className="pitcher-info">
                      <div className="pitcher-name">{p.name}</div>
                      <div className="pitcher-stats-grid">
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">ERA</span>
                          <span className={`pitcher-stat-value ${p.era < 3.0 ? 'excellent' : ''}`}>{p.era === 9.99 ? '-' : p.era?.toFixed(2)}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">HOLDS</span>
                          <span className={`pitcher-stat-value ${p.holds >= 20 ? 'excellent' : ''}`}>{p.holds}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">GAMES</span>
                          <span className="pitcher-stat-value">{p.games}</span>
                        </div>
                        <div className="pitcher-stat-item">
                          <span className="pitcher-stat-label">IP</span>
                          <span className="pitcher-stat-value">{p.ip}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {pitching_staff.closer && pitching_staff.closer.length > 0 && (
              <div className="pitcher-group">
                <h4>守護神・抑え</h4>
                <div className="pitcher-cards">
                  {pitching_staff.closer.map((p, i) => (
                    <div key={i} className="premium-pitcher-card closer">
                      <div className="pitcher-badge">CLOSER</div>
                      <div className="pitcher-image-wrapper">
                        {p.image_url ? (
                          <img src={p.image_url} alt={p.name} className="pitcher-image" />
                        ) : (
                          <User size={40} className="pitcher-placeholder" />
                        )}
                      </div>
                      <div className="pitcher-info">
                        <div className="pitcher-name">{p.name}</div>
                        <div className="pitcher-stats-grid">
                          <div className="pitcher-stat-item">
                            <span className="pitcher-stat-label">ERA</span>
                            <span className={`pitcher-stat-value ${p.era < 3.0 ? 'excellent' : ''}`}>{p.era === 9.99 ? '-' : p.era?.toFixed(2)}</span>
                          </div>
                          <div className="pitcher-stat-item">
                            <span className="pitcher-stat-label">SAVES</span>
                            <span className={`pitcher-stat-value ${p.saves >= 20 ? 'excellent' : ''}`}>{p.saves}</span>
                          </div>
                          <div className="pitcher-stat-item">
                            <span className="pitcher-stat-label">GAMES</span>
                            <span className="pitcher-stat-value">{p.games}</span>
                          </div>
                          <div className="pitcher-stat-item">
                            <span className="pitcher-stat-label">IP</span>
                            <span className="pitcher-stat-value">{p.ip}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LineupOptimizer;
