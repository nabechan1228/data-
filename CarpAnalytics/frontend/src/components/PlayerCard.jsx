import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const PlayerCard = ({ player }) => {
  if (!player) return null;

  // レーダーチャート用のデータ生成（モックデータ）
  // 実績(Reality)とポテンシャル(Vision)を比較
  const radarData = [
    { subject: 'Power', reality: player.home_runs ? player.home_runs * 5 : 30, vision: player.potential_score * 0.9 },
    { subject: 'Contact', reality: player.batting_avg ? player.batting_avg * 300 : 40, vision: player.potential_score * 0.85 },
    { subject: 'Speed', reality: 50, vision: 65 }, // モック値
    { subject: 'Defense', reality: 60, vision: 70 }, // モック値
    { subject: 'Consistency', reality: player.current_performance, vision: 80 }
  ];

  return (
    <div className="player-card">
      <div className="player-image-container">
        <img src={player.image_url} alt={player.name} className="player-image" />
      </div>
      
      <h2 className="player-name">{player.name}</h2>
      <p className="player-meta">{player.position} | {player.age}歳 | プロ{player.years_in_pro}年目</p>
      
      <div className="radar-container">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F8FAFC' }}
              itemStyle={{ color: '#F8FAFC' }}
            />
            {/* Vision (Potential) - Glowing Outline */}
            <Radar 
              name="Vision (Potential)" 
              dataKey="vision" 
              stroke="#F59E0B" 
              strokeWidth={3} 
              fill="#F59E0B" 
              fillOpacity={0.1} 
            />
            {/* Reality (Current) - Solid Fill */}
            <Radar 
              name="Reality (Current)" 
              dataKey="reality" 
              stroke="#E50012" 
              strokeWidth={2}
              fill="#E50012" 
              fillOpacity={0.6} 
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-label">Current Perf</div>
          <div className="stat-value red">{Math.round(player.current_performance)}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Potential Ceiling</div>
          <div className="stat-value gold">{Math.round(player.potential_score)}</div>
        </div>
      </div>
    </div>
  );
};

export default PlayerCard;
