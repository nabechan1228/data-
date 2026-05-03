import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import './App.css'
import PlayerCard from './components/PlayerCard'
import PotentialMatrix from './components/PotentialMatrix'
import ComparePanel from './components/ComparePanel'
import { Activity, Users, RefreshCw, Search, BarChart2 } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
const SCRAPE_TOKEN = import.meta.env.VITE_SCRAPE_SECRET_TOKEN || ''

// エラーサニタイズ（詳細情報を表示しない）
const sanitizeError = (err) => {
  if (err?.response?.status === 429) return 'リクエストが多すぎます。しばらく待ってから再試行してください。'
  if (err?.response?.status === 401) return '認証エラー：シークレットトークンが正しくありません。'
  if (err?.response?.status >= 500) return 'サーバーエラーが発生しました。しばらく待ってから再試行してください。'
  return 'データの取得に失敗しました。バックエンドが起動しているか確認してください。'
}

const POSITIONS = ['全員', '投手', '捕手', '内野手', '外野手']
const POSITION_COLORS = {
  '投手': '#3B82F6',
  '捕手': '#10B981',
  '内野手': '#F59E0B',
  '外野手': '#8B5CF6',
}

const TEAMS = [
  '全球団',
  '広島東洋カープ', '阪神タイガース', '横浜DeNAベイスターズ', '読売ジャイアンツ', '東京ヤクルトスワローズ', '中日ドラゴンズ',
  'オリックス・バファローズ', '千葉ロッテマリーンズ', '福岡ソフトバンクホークス', '東北楽天ゴールデンイーグルス', '埼玉西武ライオンズ', '北海道日本ハムファイターズ'
]

function App() {
  const [players, setPlayers] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [comparePlayer, setComparePlayer] = useState(null)
  const [compareMode, setCompareMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterPosition, setFilterPosition] = useState('全員')
  const [filterTeam, setFilterTeam] = useState('全球団')
  const [sortByPotential, setSortByPotential] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [updating, setUpdating] = useState(false)
  const [updateMsg, setUpdateMsg] = useState(null)

  const fetchPlayers = useCallback(() => {
    setLoading(true)
    setError(null)
    axios.get(`${API_URL}/api/players`)
      .then(res => {
        if (res.data.status === 'success') {
          setPlayers(res.data.data)
          // デフォルトの選択選手をカープの選手か最初の選手にする
          if (res.data.data.length > 0 && !selectedPlayer) {
            const carpPlayer = res.data.data.find(p => p.team === '広島東洋カープ')
            setSelectedPlayer(carpPlayer || res.data.data[0])
          }
        }
        setLoading(false)
      })
      .catch(err => {
        setError(sanitizeError(err))
        setLoading(false)
      })
  }, [])

  useEffect(() => { fetchPlayers() }, [fetchPlayers])

  // フィルタリング & ソート & 検索
  const filteredPlayers = players
    .filter(p => filterTeam === '全球団' || p.team === filterTeam)
    .filter(p => filterPosition === '全員' || p.position.includes(filterPosition))
    .filter(p => p.name.replace(/[\s　]/g, '').includes(searchQuery.replace(/[\s　]/g, '')))
    .sort((a, b) => sortByPotential ? b.potential_score - a.potential_score : 0)

  const handlePlayerClick = (player) => {
    if (compareMode) {
      if (selectedPlayer?.id === player.id) return
      setComparePlayer(player)
    } else {
      setSelectedPlayer(player)
    }
  }

  const handleUpdateData = async () => {
    if (!window.confirm('選手データをNPBサイトから再取得します。数分かかります。よろしいですか？')) return
    setUpdating(true)
    setUpdateMsg(null)
    try {
      const res = await axios.post(
        `${API_URL}/api/update-data`,
        {},
        { headers: { 'X-Request-Token': SCRAPE_TOKEN } }
      )
      setUpdateMsg({ type: 'success', text: res.data.message })
      fetchPlayers()
    } catch (err) {
      setUpdateMsg({ type: 'error', text: sanitizeError(err) })
    } finally {
      setUpdating(false)
    }
  }

  const handleUpdateStats = async () => {
    setUpdating(true)
    setUpdateMsg(null)
    try {
      const res = await axios.post(
        `${API_URL}/api/update-stats`,
        {},
        { headers: { 'X-Request-Token': SCRAPE_TOKEN } }
      )
      const updated = res.data.last_updated
        ? `（最終更新: ${new Date(res.data.last_updated).toLocaleString('ja-JP')}）`
        : ''
      setUpdateMsg({ type: 'success', text: `${res.data.message}${updated}` })
    } catch (err) {
      setUpdateMsg({ type: 'error', text: sanitizeError(err) })
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-screen">
          <div className="loading-spinner" />
          <p>選手データを読み込み中…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error-screen">
          <h2>⚠️ 接続エラー</h2>
          <p>{error}</p>
          <button className="filter-btn active" onClick={fetchPlayers}>再試行</button>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <h1 className="title">NPB <span>Insight</span> Pro</h1>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Reality vs Vision Analysis — {players.length}名のデータ表示中
          </div>
        </div>
        <div className="header-actions">
          <button
            className={`compare-toggle-btn ${compareMode ? 'active' : ''}`}
            onClick={() => { setCompareMode(!compareMode); setComparePlayer(null) }}
            title="比較モード"
          >
            <BarChart2 size={16} />
            {compareMode ? '比較モード ON' : '比較モード'}
          </button>
          <button
            className="update-btn"
            onClick={handleUpdateStats}
            disabled={updating}
            title="今季1軍成績を更新（約10秒）"
            style={{ background: 'rgba(16,185,129,0.1)', borderColor: '#10B981', color: '#10B981' }}
          >
            <RefreshCw size={16} className={updating ? 'spinning' : ''} />
            {updating ? '更新中…' : '成績更新'}
          </button>
          <button
            className="update-btn"
            onClick={handleUpdateData}
            disabled={updating}
            title="選手ロースターをNPBサイトから再取得（数分）"
          >
            <RefreshCw size={16} className={updating ? 'spinning' : ''} />
            {updating ? '更新中…' : 'データ更新'}
          </button>
        </div>
      </header>

      {updateMsg && (
        <div className={`toast ${updateMsg.type}`}>
          {updateMsg.type === 'success' ? '✅' : '❌'} {updateMsg.text}
          <button onClick={() => setUpdateMsg(null)} style={{ marginLeft: '12px', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {compareMode && (
        <div className="compare-hint">
          🔵 比較モード：リストから2人目の選手を選択してください
          {comparePlayer && <strong> → {comparePlayer.name} を選択中</strong>}
        </div>
      )}

      <div className="grid-layout">
        <div className="main-content" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

          {/* フィルター類 */}
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div className="search-bar" style={{ marginBottom: 0, minWidth: '200px' }}>
              <select 
                value={filterTeam} 
                onChange={(e) => setFilterTeam(e.target.value)}
                style={{ background: 'none', border: 'none', color: 'var(--text-light)', width: '100%', outline: 'none', fontSize: '0.9rem' }}
              >
                {TEAMS.map(team => (
                  <option key={team} value={team} style={{ color: '#000' }}>{team}</option>
                ))}
              </select>
            </div>
            
            <div className="filter-bar">
              {POSITIONS.map(pos => (
                <button
                  key={pos}
                  className={`filter-btn ${filterPosition === pos ? 'active' : ''}`}
                  style={filterPosition === pos && pos !== '全員' ? { borderColor: POSITION_COLORS[pos], color: POSITION_COLORS[pos] } : {}}
                  onClick={() => setFilterPosition(pos)}
                >
                  {pos}
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2 className="panel-title">
              <Activity size={20} color="var(--accent-red)" /> Potential Matrix (実績 vs 潜在能力)
            </h2>
            <PotentialMatrix
              players={filteredPlayers}
              onSelectPlayer={handlePlayerClick}
              selectedPlayerId={selectedPlayer?.id}
              comparePlayerId={comparePlayer?.id}
            />
          </div>

          {/* 比較パネル */}
          {compareMode && selectedPlayer && comparePlayer && (
            <ComparePanel
              playerA={selectedPlayer}
              playerB={comparePlayer}
              onClose={() => { setCompareMode(false); setComparePlayer(null) }}
            />
          )}
        </div>

        <div className="sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="panel">
            {selectedPlayer ? (
              <PlayerCard player={selectedPlayer} />
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>選手を選択してください</p>
            )}
          </div>

          <div className="panel">
            <h2 className="panel-title"><Users size={20} /> Roster Overview</h2>

            {/* 検索バー */}
            <div className="search-bar">
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="選手名で検索…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            {/* ソートトグル */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              <button
                className={`filter-btn small ${!sortByPotential ? 'active' : ''}`}
                onClick={() => setSortByPotential(false)}
              >番号順</button>
              <button
                className={`filter-btn small ${sortByPotential ? 'active' : ''}`}
                onClick={() => setSortByPotential(true)}
              >ポテンシャル順 ↓</button>
            </div>

            <div className="player-list">
              {filteredPlayers.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', padding: '10px' }}>選手が見つかりません</p>
              ) : filteredPlayers.map(p => (
                <div
                  key={p.id}
                  className={`list-item ${selectedPlayer?.id === p.id ? 'active' : ''} ${comparePlayer?.id === p.id ? 'compare-active' : ''}`}
                  onClick={() => handlePlayerClick(p)}
                >
                  <span className="list-item-dot" style={{ backgroundColor: POSITION_COLORS[p.position] || '#E50012' }} />
                  <span className="list-item-name">
                    {p.name}
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '4px' }}>({p.position})</span>
                  </span>
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
