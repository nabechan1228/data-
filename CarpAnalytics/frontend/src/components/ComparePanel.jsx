import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const ComparePanel = ({ playerA, playerB, onClose }) => {
  if (!playerA || !playerB) return null;

  const isPitcherA = playerA.position?.includes('投手');
  const isPitcherB = playerB.position?.includes('投手');

  // 両者を同じ軸で比較するため、軸は混合（投手がいる場合は投手軸を優先）
  const bothPitchers = isPitcherA && isPitcherB;
  const bothBatters = !isPitcherA && !isPitcherB;

  const getRadarData = () => {
    if (bothPitchers) {
      return [
        { subject: '球威',
          A: playerA.era ? Math.max(0, 100 - playerA.era * 15) : 50,
          B: playerB.era ? Math.max(0, 100 - playerB.era * 15) : 50 },
        { subject: 'コントロール', 
          A: Math.max(0, 100 - (playerA.era || 4.0) * 12), 
          B: Math.max(0, 100 - (playerB.era || 4.0) * 12) },
        { subject: 'スタミナ',    
          A: playerA.current_performance * 0.8 + 10, 
          B: playerB.current_performance * 0.8 + 10 },
        { subject: '変化球',      
          A: 70 + (playerA.years_in_pro > 5 ? 5 : 0), 
          B: 70 + (playerB.years_in_pro > 5 ? 5 : 0) },
        { subject: '安定感',
          A: playerA.current_performance,
          B: playerB.current_performance },
      ];
    }
    if (bothBatters) {
      return [
        { subject: 'パワー',
          A: Math.min(100, (playerA.home_runs || 0) * 5 + 30),
          B: Math.min(100, (playerB.home_runs || 0) * 5 + 30) },
        { subject: 'ミート力',
          A: playerA.batting_avg ? playerA.batting_avg * 300 : 40,
          B: playerB.batting_avg ? playerB.batting_avg * 300 : 40 },
        { subject: 'スピード',
          A: playerA.speed || 50,
          B: playerB.speed || 50 },
        { subject: '守備力',
          A: playerA.defense || 60,
          B: playerB.defense || 60 },
        { subject: '安定感',
          A: playerA.current_performance,
          B: playerB.current_performance },
      ];
    }
    // 混合（投手 vs 野手）
    return [
      { subject: 'ポテンシャル',
        A: playerA.potential_score,
        B: playerB.potential_score },
      { subject: '現在実績',
        A: playerA.current_performance,
        B: playerB.current_performance },
      { subject: '守備力',
        A: playerA.defense || 60,
        B: playerB.defense || 60 },
      { subject: 'スタミナ / スピード',
        A: playerA.speed || 55,
        B: playerB.speed || 55 },
      { subject: 'ポジション力',
        A: isPitcherA ? Math.max(0, 100 - (playerA.era || 3.5) * 15) : (playerA.batting_avg || 0.25) * 300,
        B: isPitcherB ? Math.max(0, 100 - (playerB.era || 3.5) * 15) : (playerB.batting_avg || 0.25) * 300 },
    ];
  };

  const radarData = getRadarData();

  return (
    <div className="compare-panel">
      <div className="compare-header">
        <h2 className="panel-title" style={{ margin: 0 }}>⚔️ 選手比較</h2>
        <button className="compare-close-btn" onClick={onClose}>✕ 閉じる</button>
      </div>

      <div className="compare-names">
        <span className="compare-name-a">🔴 {playerA.name}</span>
        <span className="compare-vs">VS</span>
        <span className="compare-name-b">🔵 {playerB.name}</span>
      </div>

      <div className="compare-chart">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F8FAFC' }}
            />
            <Legend wrapperStyle={{ color: '#94A3B8', fontSize: '12px' }} />
            <Radar name={playerA.name} dataKey="A" stroke="#E50012" fill="#E50012" fillOpacity={0.35} strokeWidth={2} />
            <Radar name={playerB.name} dataKey="B" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.35} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="compare-stats">
        {[
          { label: 'ポテンシャル', a: Math.round(playerA.potential_score), b: Math.round(playerB.potential_score) },
          { label: '現在実績', a: Math.round(playerA.current_performance), b: Math.round(playerB.current_performance) },
          { label: '年齢', a: `${playerA.age}歳`, b: `${playerB.age}歳` },
          { label: 'プロ年数', a: `${playerA.years_in_pro}年`, b: `${playerB.years_in_pro}年` },
        ].map(row => (
          <div key={row.label} className="compare-stat-row">
            <span className={`compare-val-a ${typeof row.a === 'number' && typeof row.b === 'number' && row.a > row.b ? 'winner' : ''}`}>{row.a}</span>
            <span className="compare-label">{row.label}</span>
            <span className={`compare-val-b ${typeof row.b === 'number' && typeof row.a === 'number' && row.b > row.a ? 'winner' : ''}`}>{row.b}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ComparePanel;
