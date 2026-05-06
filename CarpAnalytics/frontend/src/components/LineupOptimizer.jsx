import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, List, Thermometer, Shield } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const LineupOptimizer = ({ teamName }) => {
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
      const res = await axios.get(`${API_URL}/api/teams/${teamName}/optimized-lineup`);
      if (res.data.status === 'success') {
        setLineupData(res.data.data);
      }
    } catch (err) {
      console.error('Failed to fetch optimized lineup', err);
      setError('最適編成の取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  if (!teamName || teamName === '全球団') {
    return (
      <div className="lineup-placeholder panel">
        <p>球団を選択して最適編成を表示します</p>
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
      <div className="tab-switcher" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
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
                  <div key={i} className="pitcher-mini-card starter">
                    <div className="p-rank">{i + 1}</div>
                    <div className="p-info">
                      <div className="p-name">{p.name}</div>
                      <div className="p-stats">ERA: {p.era === 9.99 ? '-' : p.era?.toFixed(2)} | W: {p.wins}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="pitcher-group">
              <h4>リリーフ・抑え</h4>
              <div className="pitcher-cards">
                {pitching_staff.relievers.slice(0, 4).map((p, i) => (
                  <div key={i} className="pitcher-mini-card relief">
                    <div className="p-info">
                      <div className="p-name">{p.name}</div>
                      <div className="p-stats">ERA: {p.era === 9.99 ? '-' : p.era?.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
                {pitching_staff.closer.map((p, i) => (
                  <div key={i} className="pitcher-mini-card closer">
                    <div className="p-tag">守護神</div>
                    <div className="p-info">
                      <div className="p-name">{p.name}</div>
                      <div className="p-stats">ERA: {p.era === 9.99 ? '-' : p.era?.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LineupOptimizer;
