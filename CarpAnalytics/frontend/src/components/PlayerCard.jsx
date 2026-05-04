import React, { useMemo, useState } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

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
    const bonus = situationalMode ? 10 : 0;
    
    // バックエンドで計算済みの軸データがある場合はそれを使用する
    const perfAxes = player.perf_axes_json ? JSON.parse(player.perf_axes_json) : null;
    const potAxes = player.pot_axes_json ? JSON.parse(player.pot_axes_json) : null;

    if (perfAxes && potAxes) {
      const labels = isPitcher ? ['球威', '制球', 'スタミナ', '守備/変化', '安定感'] : ['パワー', 'ミート', 'スピード', '守備', '安定感'];
      return labels.map((label, i) => ({
        subject: label,
        reality: Math.min(100, perfAxes[i] + bonus),
        vision: potAxes[i]
      }));
    }

    // フォールバック
    const baseData = isPitcher ? [
      { subject: '球威', reality: 60 + bonus, vision: 80 },
      { subject: '制球', reality: 60, vision: 80 },
      { subject: 'スタミナ', reality: 50, vision: 70 },
      { subject: '守備/変化', reality: 70, vision: 80 },
      { subject: '安定感', reality: 60, vision: 85 }
    ] : [
      { subject: 'パワー', reality: 60 + bonus, vision: 80 },
      { subject: 'ミート', reality: 60 + bonus, vision: 80 },
      { subject: 'スピード', reality: 60, vision: 75 },
      { subject: '守備', reality: 60, vision: 75 },
      { subject: '安定感', reality: 60, vision: 85 }
    ];

    if (showGhost) {
      const ghostData = [55, 45, 60, 50, 40];
      return baseData.map((d, idx) => ({ ...d, ghost: ghostData[idx] }));
    }
    return baseData;
  }, [player, situationalMode, showGhost, isPitcher]);

  const batting = seasonStats?.find(s => s.stat_type === 'batting');
  const pitching = seasonStats?.find(s => s.stat_type === 'pitching');
  const hasStats = seasonStats && seasonStats.length > 0;

  return (
    <div className={`player-card ${player.is_awakened ? 'awakening-card' : ''}`}>
      <div className="player-card-header">
        <div className="player-info">
          <div className="name-row" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 className="player-name" style={{ margin: 0 }}>{player.name}</h2>
            {player.is_awakened && <span className="awakening-label">Awakening</span>}
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

      <div className="player-image-container" style={{ textAlign: 'center', margin: '15px 0' }}>
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
                {showGhost && <Radar name="Legend" dataKey="ghost" stroke="#64748b" fill="#64748b" fillOpacity={0.1} strokeDasharray="4 4" />}
                <Radar name="Potential" dataKey="vision" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.05} strokeWidth={3} />
                <Radar name="Current" dataKey="reality" stroke="#E50012" fill="#E50012" fillOpacity={0.6} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
            {player.is_unbalanced && <div className="unbalanced-badge">一芸特化</div>}
          </div>

          <div className="metrics-summary" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '15px' }}>
            <div className="metric-item">
              <div className="label">ポテンシャル充足率</div>
              <div className="value highlight">{player.convergence_rate || 0}%</div>
            </div>
            <div className="metric-item">
              <div className="label">類似モデル ({player.similarity_name || 'イチロー'})</div>
              <div className="value">{player.similarity_score || 0}%</div>
            </div>
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
            <div className="stats-list">
              <div className="stat-item"><span>防御率</span> <strong>{player.era || '---'}</strong></div>
              <div className="stat-item"><span>勝利</span> <strong>{pitching?.wins || 0}</strong></div>
              <div className="stat-item"><span>敗戦</span> <strong>{pitching?.losses || 0}</strong></div>
              <div className="stat-item"><span>奪三振</span> <strong>{pitching?.strikeouts || 0}</strong></div>
              <div className="stat-item"><span>投球回</span> <strong>{pitching?.innings_pitched || 0}</strong></div>
            </div>
          ) : (
            <div className="stats-list">
              <div className="stat-item"><span>打率</span> <strong>{player.batting_avg || '.000'}</strong></div>
              <div className="stat-item"><span>本塁打</span> <strong>{player.home_runs || 0}</strong></div>
              <div className="stat-item"><span>OPS</span> <strong>{batting?.ops || '---'}</strong></div>
              <div className="stat-item"><span>打点</span> <strong>{batting?.rbi || 0}</strong></div>
              <div className="stat-item"><span>盗塁</span> <strong>{batting?.stolen_bases || 0}</strong></div>
            </div>
          )}
          {hasStats && seasonStats[0]?.last_updated && (
            <div className="update-time" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '12px' }}>
              最終更新: {new Date(seasonStats[0].last_updated).toLocaleString('ja-JP')}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlayerCard;
