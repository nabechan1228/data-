import React, { useState, useMemo } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Radar as RechartsRadar, PieChart, Pie, Cell } from 'recharts';
import { Sparkles } from 'lucide-react';

const PlayerCard = ({ player, seasonStats }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [situationalMode, setSituationalMode] = useState(false);
  const [showGhost, setShowGhost] = useState(false);

  if (!player) {
    return (
      <div className="player-card empty">
        <p>選手を選択してください</p>
      </div>
    );
  }

  const handleTabChange = (tab) => setActiveTab(tab);

  const isPitcher = player.position === '投手' || (player.era !== null && player.era !== undefined);

  const radarData = useMemo(() => {
    if (!player) return [];
    // 覚醒（is_awakened）状態の選手は、得点圏モードでのボーナスが通常(+10)より高い(+15)
    const bonus = situationalMode ? (player.is_awakened ? 15 : 10) : 0;
    
    // バックエンドで計算済みの軸データがある場合はそれを使用する
    const perfAxes = player.perf_axes_json ? JSON.parse(player.perf_axes_json) : null;
    const potAxes = player.pot_axes_json ? JSON.parse(player.pot_axes_json) : null;
    const potUpperAxes = player.pot_axes_upper_json ? JSON.parse(player.pot_axes_upper_json) : null;
    const potLowerAxes = player.pot_axes_lower_json ? JSON.parse(player.pot_axes_lower_json) : null;

    if (perfAxes && potAxes) {
      const labels = isPitcher ? ['球威', '制球', 'スタミナ', '守備/変化', '安定感'] : ['パワー', 'ミート', 'スピード', '守備', '安定感'];
      return labels.map((label, i) => ({
        subject: label,
        reality: Math.min(100, perfAxes[i] + bonus),
        vision: potAxes[i],
        visionUpper: potUpperAxes ? potUpperAxes[i] : potAxes[i],
        visionLower: potLowerAxes ? potLowerAxes[i] : potAxes[i]
      }));
    }

    // フォールバック
    const baseData = isPitcher ? [
      { subject: '球威', reality: 60 + bonus, vision: 80, visionUpper: 85, visionLower: 75 },
      { subject: '制球', reality: 60 + bonus, vision: 80, visionUpper: 85, visionLower: 75 },
      { subject: 'スタミナ', reality: 50 + bonus, vision: 70, visionUpper: 75, visionLower: 65 },
      { subject: '守備/変化', reality: 70 + bonus, vision: 80, visionUpper: 85, visionLower: 75 },
      { subject: '安定感', reality: 60 + bonus, vision: 85, visionUpper: 90, visionLower: 80 }
    ] : [
      { subject: 'パワー', reality: 60 + bonus, vision: 80, visionUpper: 85, visionLower: 75 },
      { subject: 'ミート', reality: 60 + bonus, vision: 80, visionUpper: 85, visionLower: 75 },
      { subject: 'スピード', reality: 60 + bonus, vision: 75, visionUpper: 80, visionLower: 70 },
      { subject: '守備', reality: 60 + bonus, vision: 75, visionUpper: 80, visionLower: 70 },
      { subject: '安定感', reality: 60 + bonus, vision: 85, visionUpper: 90, visionLower: 80 }
    ];

    if (showGhost) {
      const ghostAxes = player.ghost_axes_json ? JSON.parse(player.ghost_axes_json) : [50, 50, 50, 50, 50];
      return baseData.map((d, idx) => ({ ...d, ghost: ghostAxes[idx] }));
    }
    return baseData;
  }, [player, situationalMode, showGhost, isPitcher]);

  const batting = seasonStats?.find(s => s.stat_type === 'batting');
  const pitching = seasonStats?.find(s => s.stat_type === 'pitching');
  const hasStats = seasonStats && seasonStats.length > 0;

  // Mock data generators for visualizations
  const strikeZones = useMemo(() => {
    const baseAvg = player.batting_avg || 0.250;
    return [
      baseAvg - 0.050, baseAvg + 0.080, baseAvg - 0.030,
      baseAvg + 0.020, baseAvg + 0.120, baseAvg + 0.010,
      baseAvg - 0.080, baseAvg - 0.010, baseAvg - 0.060
    ];
  }, [player.batting_avg]);

  const getZoneColor = (zoneAvg, baseAvg) => {
    const diff = zoneAvg - (baseAvg || 0.250);
    if (diff > 0.05) return 'rgba(239, 68, 68, 0.7)'; // Hot
    if (diff > 0) return 'rgba(248, 113, 113, 0.4)';
    if (diff > -0.03) return 'rgba(148, 163, 184, 0.2)'; // Neutral
    if (diff > -0.06) return 'rgba(96, 165, 250, 0.4)';
    return 'rgba(59, 130, 246, 0.7)'; // Cold
  };

  const pitchTypes = useMemo(() => {
    const k9 = pitching?.strikeouts ? (pitching.strikeouts * 9 / (pitching.innings_pitched || 1)) : 6.0;
    if (k9 > 8) {
      return [
        { name: 'ストレート', value: 45, count: 450, color: '#EF4444' },
        { name: 'スライダー', value: 30, count: 300, color: '#3B82F6' },
        { name: 'フォーク', value: 20, count: 200, color: '#10B981' },
        { name: 'カーブ', value: 5, count: 50, color: '#F59E0B' },
      ];
    } else {
      return [
        { name: 'ストレート', value: 50, count: 500, color: '#EF4444' },
        { name: 'スライダー', value: 25, count: 250, color: '#3B82F6' },
        { name: 'チェンジアップ', value: 15, count: 150, color: '#8B5CF6' },
        { name: 'ツーシーム', value: 10, count: 100, color: '#F97316' },
      ];
    }
  }, [pitching]);

  return (
    <div className={`player-card ${player.is_awakened ? 'awakening-card' : ''}`}>
      <style>{`
        .premium-stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
          margin-bottom: 20px;
        }
        .premium-stat-box {
          background: rgba(30, 41, 59, 0.7);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 8px 4px;
          text-align: center;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          min-height: 64px;
          transition: all 0.3s ease;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .premium-stat-box:hover {
          transform: translateY(-3px);
          border-color: rgba(245, 158, 11, 0.5);
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 0 15px rgba(245, 158, 11, 0.2);
        }
        .premium-stat-label {
          font-size: 0.65rem;
          color: #94A3B8;
          text-transform: uppercase;
          letter-spacing: 0.02em;
          margin-bottom: 2px;
          white-space: nowrap;
        }
        .premium-stat-value {
          font-size: 1.1rem;
          font-weight: 800;
          white-space: nowrap;
          background: linear-gradient(135deg, #F8FAFC 0%, #CBD5E1 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          font-family: 'Inter', 'Roboto', sans-serif;
        }
        .premium-stat-value.highlight-red {
          background: linear-gradient(135deg, #FCA5A5 0%, #EF4444 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .premium-stat-value.highlight-blue {
          background: linear-gradient(135deg, #93C5FD 0%, #3B82F6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        
        .premium-viz-section {
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 16px;
          box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        }
        .premium-viz-title {
          margin: 0 0 15px 0;
          font-size: 0.95rem;
          color: #F1F5F9;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          padding-bottom: 8px;
          display: flex;
          align-items: center;
          gap: 8px;
          letter-spacing: 0.05em;
        }
        .neon-strike-zone {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          grid-template-rows: repeat(3, 1fr);
          width: 140px;
          height: 180px;
          border: 2px solid rgba(255, 255, 255, 0.2);
          border-radius: 4px;
          background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25'%3E%3Cpath d='M 0 0 L 140 0 L 140 180 L 0 180 Z' fill='rgba(0,0,0,0.3)' stroke='rgba(255,255,255,0.1)' stroke-width='1'/%3E%3C/svg%3E");
          position: relative;
          box-shadow: 0 0 15px rgba(255,255,255,0.05);
        }
        .neon-zone-cell {
          border: 1px dashed rgba(255, 255, 255, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.8rem;
          font-weight: 800;
          color: #FFFFFF;
          text-shadow: 0 2px 4px rgba(0,0,0,0.9);
          transition: all 0.3s ease;
        }
        .neon-zone-cell:hover {
          transform: scale(1.05);
          z-index: 10;
          box-shadow: 0 0 10px currentColor;
          border-color: currentColor;
          border-style: solid;
        }
      `}</style>
      <div className="player-card-header">
        <div className="player-info">
          <div className="name-row" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 className="player-name" style={{ margin: 0 }}>{player.name}</h2>
            {!!player.is_awakened && <span className="awakening-label">Awakening</span>}
            {!!player.is_breaking_out && (
              <span className="breakout-alert">
                📈 急成長中
              </span>
            )}
          </div>
          <div className="style-tag-row" style={{ textAlign: 'left' }}>
            {player.style_tag && <span className="style-tag">{player.style_tag}</span>}
          </div>
          <p className="player-meta">
            {player.team} | {player.position} | {player.age}歳 | プロ{player.years_in_pro}年目
            {(!player.batting_avg || player.batting_avg === 0) && player.farm_stats_json && player.farm_stats_json !== '{}' && (
              <span className="farm-badge" style={{
                marginLeft: '8px', fontSize: '0.65rem', background: 'rgba(16,185,129,0.1)', 
                border: '1px solid #10B981', color: '#10B981', padding: '1px 4px', borderRadius: '3px'
              }}>2軍データ反映中</span>
            )}
          </p>
        </div>
        {hasStats && <span className="league-badge">1軍</span>}
      </div>

      <div className={`player-image-container ${player.is_breaking_out ? 'breaking-out-glow' : ''}`} style={{ textAlign: 'center', margin: '15px 0' }}>
        <img 
          src={player.image_url || 'https://via.placeholder.com/150'} 
          alt={player.name} 
          className="player-image" 
          style={{ width: '120px', height: '120px', borderRadius: '50%', objectFit: 'cover', border: '3px solid var(--accent-red)' }}
        />
      </div>

      <div className="tab-buttons" style={{ display: 'flex', gap: '8px', marginBottom: '15px' }}>
        <button 
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >📊 分析</button>
        <button 
          className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >🏆 成績</button>
      </div>

      {activeTab === 'profile' && (
        <div className="profile-tab">
          <div className="toggles" style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginBottom: '10px' }}>
            <label className="toggle-label">
              <input type="checkbox" checked={situationalMode} onChange={() => setSituationalMode(!situationalMode)} />
              🔥 覚醒(得点圏)
            </label>
            <label className="toggle-label">
              <input type="checkbox" checked={showGhost} onChange={() => setShowGhost(!showGhost)} />
              👻 ロールモデル
            </label>
          </div>

          <div className="radar-chart-area" style={{ height: '240px', width: '100%', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Tooltip />
                {showGhost && <RechartsRadar name="Legend" dataKey="ghost" stroke="#64748b" fill="#64748b" fillOpacity={0.1} strokeDasharray="4 4" />}
                <RechartsRadar name="Potential Upper" dataKey="visionUpper" stroke="none" fill="#F59E0B" fillOpacity={0.15} />
                <RechartsRadar name="Potential Lower" dataKey="visionLower" stroke="none" fill="#F59E0B" fillOpacity={0.25} />
                <RechartsRadar name="Potential" dataKey="vision" stroke="#F59E0B" fill="none" strokeWidth={1} strokeDasharray="3 3" />
                <RechartsRadar name="Current" dataKey="reality" stroke="#E50012" fill="#E50012" fillOpacity={0.6} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
            {!!player.is_unbalanced && <div className="unbalanced-badge">一芸特化</div>}
          </div>

          <div className="metrics-summary" style={{ 
            display: 'grid', 
            gridTemplateColumns: showGhost ? '1fr 1fr' : '1fr', 
            gap: '10px', 
            marginTop: '15px' 
          }}>
            <div className="metric-item">
              <div className="label">ポテンシャル充足率</div>
              <div className="value highlight">{player.convergence_rate || 0}%</div>
            </div>
            {showGhost && (
              <div className="metric-item">
                <div className="label">類似モデル ({player.similarity_name || 'イチロー'})</div>
                <div className="value">{player.similarity_score || 0}%</div>
              </div>
            )}
          </div>
          
          {player.fielding_json && (
            <div className="fielding-breakdown" style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>守備ポジション内訳:</div>
              {Object.entries(JSON.parse(player.fielding_json)).map(([pos, s]) => (
                <span key={pos} style={{ marginRight: '8px', background: 'rgba(255,255,255,0.05)', padding: '1px 5px', borderRadius: '3px' }}>
                  {pos}({s.games}試)
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="stats-tab">
          {isPitcher ? (
            <div className="detailed-stats-container">
              <div className="premium-stats-grid">
                <div className="premium-stat-box"><div className="premium-stat-label">登板</div><div className="premium-stat-value">{pitching?.games || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">勝利</div><div className="premium-stat-value">{pitching?.wins || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">敗戦</div><div className="premium-stat-value">{pitching?.losses || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">防御率</div><div className={`premium-stat-value ${player.era < 3.0 ? 'highlight-blue' : ''}`}>{player.era === 9.99 ? '---' : (player.era || '---')}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">セーブ</div><div className="premium-stat-value">{pitching?.saves || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">ホールド</div><div className="premium-stat-value">{pitching?.holds || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">奪三振</div><div className="premium-stat-value">{pitching?.strikeouts || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">投球回</div><div className="premium-stat-value">{pitching?.innings_pitched || 0}</div></div>
              </div>
              
              <div className="premium-viz-section">
                <h4 className="premium-viz-title"><Sparkles size={16} color="#3B82F6" /> 球種割合（推定）</h4>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div style={{ width: '120px', height: '120px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pitchTypes}
                          cx="50%" cy="50%"
                          innerRadius={25}
                          outerRadius={50}
                          paddingAngle={2}
                          dataKey="value"
                          stroke="none"
                        >
                          {pitchTypes.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: '4px', fontSize: '0.8rem' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ flex: 1, paddingLeft: '10px' }}>
                    {pitchTypes.map((pt, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: pt.color, display: 'inline-block' }}></span>
                          {pt.name}
                        </span>
                        <span style={{ color: '#94A3B8' }}>{pt.value}% <span style={{fontSize:'0.65rem'}}>({pt.count}球)</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="detailed-stats-container">
              <div className="premium-stats-grid">
                <div className="premium-stat-box"><div className="premium-stat-label">試合</div><div className="premium-stat-value">{batting?.games || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">打率</div><div className={`premium-stat-value ${player.batting_avg > 0.3 ? 'highlight-red' : ''}`}>{player.batting_avg || '.000'}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">安打</div><div className="premium-stat-value">{batting?.hits || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">二塁打</div><div className="premium-stat-value">{Math.max(0, (batting?.hits || 0) - (batting?.triples || 0) - (player.home_runs || 0) - Math.floor((batting?.hits || 0) * 0.6))}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">三塁打</div><div className="premium-stat-value">{batting?.triples || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">本塁打</div><div className={`premium-stat-value ${player.home_runs > 20 ? 'highlight-red' : ''}`}>{player.home_runs || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">打点</div><div className="premium-stat-value">{batting?.rbi || 0}</div></div>
                <div className="premium-stat-box"><div className="premium-stat-label">OPS</div><div className={`premium-stat-value ${batting?.ops > 0.85 ? 'highlight-red' : ''}`}>{batting?.ops || '---'}</div></div>
              </div>

              <div className="premium-viz-section">
                <h4 className="premium-viz-title"><Sparkles size={16} color="#EF4444" /> コース別打率（推定）</h4>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <div className="neon-strike-zone">
                    {strikeZones.map((avg, i) => {
                      const color = getZoneColor(avg, player.batting_avg);
                      return (
                        <div key={i} className="neon-zone-cell" style={{ background: color }}>
                          {avg.toFixed(3).replace(/^0+/, '')}
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ marginLeft: '20px', fontSize: '0.7rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <span style={{ width: '12px', height: '12px', background: 'rgba(239, 68, 68, 0.7)' }}></span> Hot
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <span style={{ width: '12px', height: '12px', background: 'rgba(148, 163, 184, 0.2)' }}></span> Avg
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <span style={{ width: '12px', height: '12px', background: 'rgba(59, 130, 246, 0.7)' }}></span> Cold
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {hasStats && seasonStats[0]?.last_updated && (
            <div className="update-time" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '12px', textAlign: 'right' }}>
              データ更新: {new Date(seasonStats[0].last_updated).toLocaleString('ja-JP')}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlayerCard;
