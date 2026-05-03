import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const PotentialMatrix = ({ players, onSelectPlayer, selectedPlayerId }) => {
  // 散布図用のデータ整形
  const data = players.map(p => ({
    id: p.id,
    name: p.name,
    x: p.current_performance, // X軸: 現在の実績
    y: p.potential_score,     // Y軸: 潜在能力
    position: p.position
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', padding: '10px', borderRadius: '4px' }}>
          <p style={{ margin: 0, fontWeight: 'bold', color: '#F8FAFC' }}>{data.name}</p>
          <p style={{ margin: '5px 0 0', fontSize: '12px', color: '#94A3B8' }}>実績: {Math.round(data.x)}</p>
          <p style={{ margin: '5px 0 0', fontSize: '12px', color: '#F59E0B' }}>ポテンシャル: {Math.round(data.y)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="実績" 
            domain={[0, 100]} 
            stroke="#94A3B8"
            label={{ value: "Current Performance (実績)", position: "insideBottom", offset: -10, fill: '#94A3B8' }}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="ポテンシャル" 
            domain={[0, 100]} 
            stroke="#94A3B8"
            label={{ value: "Potential (将来性)", angle: -90, position: "insideLeft", fill: '#94A3B8' }}
          />
          
          <ReferenceLine x={50} stroke="#334155" strokeWidth={2} />
          <ReferenceLine y={50} stroke="#334155" strokeWidth={2} />
          
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          
          <Scatter 
            name="Players" 
            data={data} 
            onClick={(e) => {
              const player = players.find(p => p.id === e.id);
              if (player) onSelectPlayer(player);
            }}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.id === selectedPlayerId ? "#F59E0B" : "#E50012"} 
                stroke="#FFFFFF"
                strokeWidth={entry.id === selectedPlayerId ? 2 : 0}
                r={entry.id === selectedPlayerId ? 8 : 6}
                style={{ cursor: 'pointer', transition: 'all 0.3s' }}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '0.8rem', marginTop: '10px' }}>
        <span>← 発展途上</span>
        <span>実績トップクラス →</span>
      </div>
    </div>
  );
};

export default PotentialMatrix;
