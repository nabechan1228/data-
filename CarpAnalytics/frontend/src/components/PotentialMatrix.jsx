import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const PotentialMatrix = ({ players, onSelectPlayer, selectedPlayerId, comparePlayerId }) => {
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
            {data.map((entry, index) => {
              let dotColor = "#E50012";
              if (entry.position.includes('投手')) dotColor = "#3B82F6";
              else if (entry.position.includes('捕手')) dotColor = "#10B981";
              else if (entry.position.includes('内野手')) dotColor = "#F59E0B";
              else if (entry.position.includes('外野手')) dotColor = "#8B5CF6";

              const isSelected = entry.id === selectedPlayerId;
              const isCompare  = entry.id === comparePlayerId;
              // ドットが多いため、基本のサイズを小さくし、不透明度を下げる
              const size = isSelected || isCompare ? 8 : (players.length > 200 ? 4 : 6);
              const opacity = isSelected || isCompare ? 1 : (players.length > 200 ? 0.6 : 0.8);

              return (
                <Cell
                  key={`cell-${index}`}
                  fill={isSelected ? "#FFFFFF" : isCompare ? "#60A5FA" : dotColor}
                  stroke={isSelected ? "#F59E0B" : isCompare ? "#BFDBFE" : "#FFFFFF"}
                  strokeWidth={isSelected || isCompare ? 3 : 0}
                  r={size}
                  fillOpacity={opacity}
                  style={{ cursor: 'pointer', transition: players.length > 200 ? 'none' : 'all 0.3s' }}
                />
              );
            })}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94A3B8', fontSize: '0.8rem', marginTop: '10px' }}>
        <span>← 発展途上</span>
        <div style={{ display: 'flex', gap: '15px' }}>
          <span style={{color: '#3B82F6'}}>● 投手</span>
          <span style={{color: '#10B981'}}>● 捕手</span>
          <span style={{color: '#F59E0B'}}>● 内野手</span>
          <span style={{color: '#8B5CF6'}}>● 外野手</span>
        </div>
        <span>実績トップクラス →</span>
      </div>
    </div>
  );
};

export default PotentialMatrix;
