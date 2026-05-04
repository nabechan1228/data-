import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const PlayerCard = ({ player }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [seasonStats, setSeasonStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [situationalMode, setSituationalMode] = useState(false);
  const [showGhost, setShowGhost] = useState(false);

  useEffect(() => {
    if (!player) return;
    setActiveTab('profile');
    setSeasonStats(null);
  }, [player?.id]);

  const fetchSeasonStats = () => {
    if (seasonStats !== null || statsLoading) return;
    setStatsLoading(true);
    const nameEncoded = encodeURIComponent(player.name?.trim() || '');
    axios.get(`${API_URL}/api/season-stats/player/${nameEncoded}`)
      .then(res => {
        if (res.data.status === 'success') {
          setSeasonStats(res.data.data);
        }
      })
      .catch(() => setSeasonStats([]))
      .finally(() => setStatsLoading(false));
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'stats') fetchSeasonStats();
  };
  if (!player) {
    return (
      <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
        <p>左のリストから選手を選択して詳細を表示</p>
      </div>
    );
  }

  const isPitcher = player.position?.includes('投手');

  const radarData = useMemo(() => {
    if (!player) return [];
    const bonus = situationalMode ? 10 : 0;
    
    // バックエンドで計算済みの軸データがある場合はそれを使用する（面積計算と同期させるため）
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

    // フォールバック（旧データ用）
    const baseData = isPitcher ? [
      { subject: '球威', reality: (player.era ? Math.max(0, 100 - player.era * 15) : 50) + bonus, vision: player.potential_score * 0.9 },
      { subject: '制球', reality: 60, vision: player.potential_score * 0.85 },
      { subject: 'スタミナ', reality: 50, vision: 65 },
      { subject: '守備/変化', reality: 70 + bonus, vision: 75 },
      { subject: '安定感', reality: (player.current_performance || 50) + bonus, vision: 80 }
    ] : [
      { subject: 'パワー', reality: (player.home_runs ? Math.min(100, player.home_runs * 5 + 30) : 30) + bonus, vision: player.potential_score * 0.9 },
      { subject: 'ミート', reality: (player.batting_avg ? Math.min(100, player.batting_avg * 300) : 40) + bonus, vision: player.potential_score * 0.85 },
      { subject: 'スピード', reality: (player.speed || 50), vision: 70 },
      { subject: '守備', reality: (player.defense || 60), vision: 75 },
      { subject: '安定感', reality: (player.current_performance || 50) + bonus, vision: 80 }
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
    <div className="player-card">
      <div className="player-image-container">
        <img src={player.image_url} alt={player.name} className="player-image" />
      </div>

      <h2 className="player-name">
        {player.name}
        {hasStats && (
          <span style={{
            marginLeft: '8px',
            fontSize: '0.65rem',
            background: 'rgba(229,0,18,0.15)',
            border: '1px solid var(--accent-red)',
            color: 'var(--accent-red)',
            padding: '2px 6px',
            borderRadius: '4px',
            verticalAlign: 'middle',
          }}>1軍</span>
        )}
      </h2>
      <p className="player-meta">
        {player.team} | {player.position} | {player.age}歳 | プロ{player.years_in_pro}年目
      </p>

      {/* タブ切り替え */}
      <div style={{ display: 'flex', gap: '8px', margin: '12px 0 0' }}>
        <button
          onClick={() => handleTabChange('profile')}
          style={{
            padding: '5px 14px',
            borderRadius: '6px',
            border: activeTab === 'profile' ? '1px solid var(--accent-red)' : '1px solid var(--border-color)',
            background: activeTab === 'profile' ? 'rgba(229,0,18,0.15)' : 'transparent',
            color: activeTab === 'profile' ? 'var(--accent-red)' : 'var(--text-muted)',
            cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600',
          }}
        >📊 プロフィール</button>
        <button
          onClick={() => handleTabChange('stats')}
          style={{
            padding: '5px 14px',
            borderRadius: '6px',
            border: activeTab === 'stats' ? '1px solid #10B981' : '1px solid var(--border-color)',
            background: activeTab === 'stats' ? 'rgba(16,185,129,0.15)' : 'transparent',
            color: activeTab === 'stats' ? '#10B981' : 'var(--text-muted)',
            cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600',
          }}
        >🏆 今季成績</button>
      </div>

      {activeTab === 'profile' && (
        <>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginBottom: '10px' }}>
            <label className="toggle-label">
              <input type="checkbox" checked={situationalMode} onChange={() => setSituationalMode(!situationalMode)} />
              🔥 得点圏モード
            </label>
            <label className="toggle-label">
              <input type="checkbox" checked={showGhost} onChange={() => setShowGhost(!showGhost)} />
              👻 ロールモデル比較
            </label>
          </div>

          <div className="radar-container" style={{ position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F8FAFC' }}
                  itemStyle={{ color: '#F8FAFC' }}
                />
                {showGhost && (
                  <Radar name="League Avg (Ghost)" dataKey="ghost" stroke="#475569" strokeWidth={1} fill="#475569" fillOpacity={0.1} strokeDasharray="4 4" />
                )}
                <Radar name="Vision (Potential)" dataKey="vision" stroke="#F59E0B" strokeWidth={3} fill="#F59E0B" fillOpacity={0.05} />
                <Radar name="Reality (Current)" dataKey="reality" stroke="#E50012" strokeWidth={2} fill="#E50012" fillOpacity={0.55} />
              </RadarChart>
            </ResponsiveContainer>
            
            {player.is_unbalanced && (
              <div style={{
                position: 'absolute', top: '10px', right: '10px',
                background: 'rgba(59,130,246,0.2)', border: '1px solid #3B82F6',
                color: '#60A5FA', fontSize: '0.7rem', padding: '2px 8px', borderRadius: '20px'
              }}>一芸特化型</div>
            )}
          </div>

          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-label">CURRENT PERF</div>
              <div className="stat-value red">{Math.round(player.current_performance || 0)}</div>
              <div className="stat-sub">面積: {player.perf_area || '-'}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">POTENTIAL CEILING</div>
              <div className="stat-value gold">{Math.round(player.potential_score || 0)}</div>
              <div className="stat-sub">充足率: {player.convergence_rate || '0'}%</div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'stats' && (
        <div style={{ marginTop: '16px' }}>
          {statsLoading && (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
              <div className="loading-spinner" style={{ margin: '0 auto 8px' }} />
              <p>成績を読み込み中…</p>
            </div>
          )}

          {!statsLoading && !hasStats && (
            <div style={{
              textAlign: 'center', color: 'var(--text-muted)', padding: '24px',
              border: '1px dashed var(--border-color)', borderRadius: '8px',
            }}>
              <p style={{ fontSize: '1.5rem', marginBottom: '8px' }}>📋</p>
              <p>今季の1軍成績データがありません</p>
              <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>規定打席/登板未満の可能性があります</p>
            </div>
          )}

          {!statsLoading && batting && (
            <SeasonStatsTable title="🏏 打撃成績 (2026)" stats={batting} type="batting" />
          )}
          {!statsLoading && pitching && (
            <SeasonStatsTable title="⚾ 投手成績 (2026)" stats={pitching} type="pitching" />
          )}
        </div>
      )}
    </div>
  );
};

const StatRow = ({ label, value, highlight = false }) => (
  <div style={{
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '7px 12px',
    background: highlight ? 'rgba(245,158,11,0.1)' : 'rgba(15,23,42,0.5)',
    borderRadius: '6px',
    borderLeft: highlight ? '3px solid #F59E0B' : '3px solid transparent',
  }}>
    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{label}</span>
    <span style={{
      fontWeight: '700', fontSize: '0.95rem',
      color: highlight ? '#F59E0B' : 'var(--text-light)',
    }}>{value ?? '-'}</span>
  </div>
);

const SeasonStatsTable = ({ title, stats, type }) => (
  <div style={{ marginBottom: '16px' }}>
    <h4 style={{ color: '#10B981', fontSize: '0.9rem', marginBottom: '10px', fontWeight: '700' }}>{title}</h4>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {type === 'batting' ? (
        <>
          <StatRow label="試合" value={stats.games} />
          <StatRow label="打席" value={stats.plate_appearances} />
          <StatRow label="打率" value={stats.batting_avg?.toFixed(3)} highlight={stats.batting_avg >= 0.300} />
          <StatRow label="安打" value={stats.hits} />
          <StatRow label="本塁打" value={stats.home_runs} highlight={stats.home_runs >= 10} />
          <StatRow label="打点" value={stats.rbi} />
          <StatRow label="盗塁" value={stats.stolen_bases} />
          <StatRow label="出塁率" value={stats.on_base_pct?.toFixed(3)} />
          <StatRow label="長打率" value={stats.slg_pct?.toFixed(3)} />
          <StatRow label="OPS" value={stats.ops?.toFixed(3)} highlight={stats.ops >= 0.850} />
        </>
      ) : (
        <>
          <StatRow label="登板" value={stats.games} />
          <StatRow label="投球回" value={stats.innings_pitched?.toFixed(1)} />
          <StatRow label="防御率" value={stats.era?.toFixed(2)} highlight={stats.era !== null && stats.era <= 2.50} />
          <StatRow label="勝利" value={stats.wins} />
          <StatRow label="敗北" value={stats.losses} />
          <StatRow label="セーブ" value={stats.saves} highlight={stats.saves >= 10} />
          <StatRow label="ホールド" value={stats.holds} />
          <StatRow label="奪三振" value={stats.strikeouts} />
        </>
      )}
    </div>
  </div>
);

export default PlayerCard;
