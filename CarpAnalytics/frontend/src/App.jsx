import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import PlayerCard from './components/PlayerCard'
import PotentialMatrix from './components/PotentialMatrix'
import { Activity, Users } from 'lucide-react'

function App() {
  const [players, setPlayers] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 開発サーバーのAPIエンドポイント（FastAPI）からデータを取得
    axios.get('http://localhost:8001/api/players')
      .then(response => {
        if (response.data.status === 'success') {
          setPlayers(response.data.data)
          if (response.data.data.length > 0) {
            setSelectedPlayer(response.data.data[0])
          }
        }
        setLoading(false)
      })
      .catch(error => {
        console.error("Error fetching data:", error)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="dashboard-container"><p>Loading player data...</p></div>
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1 className="title">Carp <span>Insight</span> Pro</h1>
        <div style={{ color: 'var(--text-muted)' }}>
          Reality vs Vision Analysis
        </div>
      </header>

      <div className="grid-layout">
        <div className="main-content" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="panel">
            <h2 className="panel-title"><Activity size={20} color="var(--carp-red)" /> Potential Matrix (実績 vs 潜在能力)</h2>
            <PotentialMatrix players={players} onSelectPlayer={setSelectedPlayer} selectedPlayerId={selectedPlayer?.id} />
          </div>
        </div>

        <div className="sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="panel">
            {selectedPlayer ? (
              <PlayerCard player={selectedPlayer} />
            ) : (
              <p>Select a player</p>
            )}
          </div>
          
          <div className="panel">
            <h2 className="panel-title"><Users size={20} /> Roster Overview</h2>
            <div className="player-list">
              {players.map(p => (
                <div 
                  key={p.id} 
                  className={`list-item ${selectedPlayer?.id === p.id ? 'active' : ''}`}
                  onClick={() => setSelectedPlayer(p)}
                >
                  <span className="list-item-name">{p.name} <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>({p.position})</span></span>
                  <span className="list-item-score">P: {Math.round(p.potential_score)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
