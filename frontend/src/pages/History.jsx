import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Download,
  Calendar,
  Filter,
  Headphones,
  FileText,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Volume2,
  X,
  Play,
  Pause,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Card from '../components/ui/Card';
import api from '../services/api';

export const History = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('all');
  const [trackFilter, setTrackFilter] = useState('all');
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Audio player modal state
  const [playingSession, setPlayingSession] = useState(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Default initial sample records matching design specs if backend is empty
  const defaultHistoryRecords = [
    {
      id: 'sess_default_1',
      dateText: 'Aug 09, 2026',
      track: 'Fullstack Dev',
      trackColor: { bg: '#f3e8ff', text: '#65597b' },
      score: 82,
      duration: '18m 42s',
      title: 'Fullstack React & Node.js System Architecture',
    },
    {
      id: 'sess_default_2',
      dateText: 'Aug 05, 2026',
      track: 'System Design',
      trackColor: { bg: '#dcfce7', text: '#15803d' },
      score: 74,
      duration: '22m 10s',
      title: 'Distributed Caching & Microservices Architecture',
    },
    {
      id: 'sess_default_3',
      dateText: 'Jul 28, 2026',
      track: 'Backend Architecture',
      trackColor: { bg: '#e0f2fe', text: '#0369a1' },
      score: 88,
      duration: '20m 15s',
      title: 'High-Concurrency Database Scaling & Consensus',
    },
  ];

  useEffect(() => {
    async function fetchHistory() {
      setLoading(true);
      try {
        const response = await api.get('/setup/sessions');
        if (Array.isArray(response.data) && response.data.length > 0) {
          const formatted = response.data.map((s, idx) => ({
            id: s.id,
            dateText: s.created_at
              ? new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
              : 'Aug 09, 2026',
            track: s.parsed_jd?.role_title || s.title || (idx % 2 === 0 ? 'Fullstack Dev' : 'System Design'),
            trackColor: idx % 2 === 0 ? { bg: '#f3e8ff', text: '#65597b' } : { bg: '#dcfce7', text: '#15803d' },
            score: s.score || 80,
            duration: '18m 42s',
            title: s.parsed_jd?.role_title || 'Technical Practice Track',
          }));
          setSessions(formatted);
        } else {
          setSessions(defaultHistoryRecords);
        }
      } catch (err) {
        console.warn('Backend history fetch error, using default mock archive:', err);
        setSessions(defaultHistoryRecords);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  // Filtered session records
  const filteredSessions = sessions.filter((s) => {
    const matchesSearch =
      s.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.track.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesTrack =
      trackFilter === 'all' || s.track.toLowerCase().includes(trackFilter.toLowerCase());

    return matchesSearch && matchesTrack;
  });

  const handleTogglePlay = (session) => {
    if (playingSession?.id === session.id) {
      setIsPlayingAudio((prev) => !prev);
    } else {
      setPlayingSession(session);
      setIsPlayingAudio(true);
    }
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)' }}>
      {/* Shared Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
        
        {/* HERO BANNER CARD */}
        <Card
          style={{
            marginBottom: '28px',
            padding: '36px 40px',
            background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
            borderRadius: '24px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 24px rgba(101, 89, 123, 0.04)',
          }}
          className="animate-entrance"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1
              style={{
                fontSize: '28px',
                fontWeight: '800',
                color: '#111827',
                letterSpacing: '-0.02em',
                margin: 0,
              }}
            >
              Interview History & Archive
            </h1>
            <span style={{ fontSize: '26px' }}>📜</span>
          </div>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: '8px 0 0 0', lineHeight: '1.5' }}>
            Review your past sessions with Eva, listen to recordings, and track your growth.
          </p>
        </Card>

        {/* FILTER & CONTROLS BAR CONTAINER */}
        <Card
          style={{
            padding: '16px 20px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)',
          }}
        >
          {/* Left Inputs */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', flex: 1 }}>
            {/* Search Input */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#f3f4f6',
                borderRadius: '9999px',
                padding: '8px 16px',
                width: '260px',
              }}
            >
              <Search size={16} style={{ color: '#9ca3af' }} />
              <input
                type="text"
                placeholder="Search by Topic..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  border: 'none',
                  background: 'transparent',
                  outline: 'none',
                  fontSize: '13px',
                  color: '#374151',
                  width: '100%',
                }}
              />
            </div>

            {/* Filter by Date Dropdown */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#f3f4f6',
                borderRadius: '9999px',
                padding: '8px 14px',
                fontSize: '13px',
                fontWeight: '600',
                color: '#374151',
              }}
            >
              <select
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '13px', fontWeight: '600', color: '#374151', cursor: 'pointer' }}
              >
                <option value="all">Filter by Date</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            {/* Filter by Track Dropdown */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#f3f4f6',
                borderRadius: '9999px',
                padding: '8px 14px',
                fontSize: '13px',
                fontWeight: '600',
                color: '#374151',
              }}
            >
              <select
                value={trackFilter}
                onChange={(e) => setTrackFilter(e.target.value)}
                style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '13px', fontWeight: '600', color: '#374151', cursor: 'pointer' }}
              >
                <option value="all">Filter by Track</option>
                <option value="fullstack">Fullstack Dev</option>
                <option value="system">System Design</option>
                <option value="backend">Backend Architecture</option>
              </select>
            </div>
          </div>

          {/* Right Action Button */}
          <button
            onClick={() => alert('Exporting history data as CSV...')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 18px',
              borderRadius: '9999px',
              background: '#bbf7d0',
              color: '#15803d',
              border: 'none',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(34, 197, 94, 0.15)',
            }}
          >
            <Download size={14} />
            <span>Export Data</span>
          </button>
        </Card>

        {/* HISTORY DATA TABLE CARD */}
        <Card
          style={{
            padding: '24px 32px',
            background: '#ffffff',
            borderRadius: '24px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.02)',
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #f3f4f6', color: '#6b7280', fontSize: '11px', fontWeight: '800', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px' }}>DATE</th>
                  <th style={{ padding: '12px 16px' }}>TRACK</th>
                  <th style={{ padding: '12px 16px' }}>SCORE</th>
                  <th style={{ padding: '12px 16px' }}>DURATION</th>
                  <th style={{ padding: '12px 16px' }}>RECORDING</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredSessions.length > 0 ? (
                  filteredSessions.map((session, idx) => (
                    <tr
                      key={session.id || idx}
                      style={{
                        borderBottom: idx === filteredSessions.length - 1 ? 'none' : '1px solid #f9fafb',
                        transition: 'background 150ms ease',
                      }}
                    >
                      {/* DATE */}
                      <td style={{ padding: '18px 16px', fontSize: '14px', fontWeight: '600', color: '#374151' }}>
                        {session.dateText}
                      </td>

                      {/* TRACK */}
                      <td style={{ padding: '18px 16px' }}>
                        <span
                          style={{
                            fontSize: '12px',
                            fontWeight: '700',
                            padding: '4px 12px',
                            borderRadius: '9999px',
                            background: session.trackColor?.bg || '#f3e8ff',
                            color: session.trackColor?.text || '#65597b',
                            display: 'inline-block',
                          }}
                        >
                          {session.track}
                        </span>
                      </td>

                      {/* SCORE */}
                      <td style={{ padding: '18px 16px', fontSize: '14px', fontWeight: '800', color: '#111827' }}>
                        {session.score}/100
                      </td>

                      {/* DURATION */}
                      <td style={{ padding: '18px 16px', fontSize: '13px', fontWeight: '500', color: '#6b7280' }}>
                        {session.duration}
                      </td>

                      {/* RECORDING LISTEN */}
                      <td style={{ padding: '18px 16px' }}>
                        <button
                          onClick={() => handleTogglePlay(session)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            background: 'transparent',
                            border: 'none',
                            color: '#4b5563',
                            fontSize: '13px',
                            fontWeight: '600',
                            cursor: 'pointer',
                          }}
                        >
                          <Headphones size={15} style={{ color: '#65597b' }} />
                          <span>{playingSession?.id === session.id && isPlayingAudio ? 'Pause' : 'Listen'}</span>
                        </button>
                      </td>

                      {/* ACTION VIEW REPORT */}
                      <td style={{ padding: '18px 16px', textAlign: 'right' }}>
                        <button
                          onClick={() => navigate(`/report/${session.id}`)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '8px 16px',
                            borderRadius: '9999px',
                            background: '#f3f4f6',
                            color: '#374151',
                            border: '1px solid #e5e7eb',
                            fontSize: '12px',
                            fontWeight: '700',
                            cursor: 'pointer',
                            transition: 'all 150ms ease',
                          }}
                          onMouseOver={(e) => {
                            e.currentTarget.style.background = '#65597b';
                            e.currentTarget.style.color = '#ffffff';
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.style.background = '#f3f4f6';
                            e.currentTarget.style.color = '#374151';
                          }}
                        >
                          <FileText size={14} />
                          <span>View Report</span>
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                      No history records found matching criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* PAGINATION CONTROLS */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #f3f4f6' }}>
            <button
              disabled
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'not-allowed',
              }}
            >
              <ChevronLeft size={16} />
              <span>Previous</span>
            </button>

            <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '500' }}>
              Showing {filteredSessions.length} sessions
            </span>

            <button
              disabled
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'not-allowed',
              }}
            >
              <span>Next</span>
              <ChevronRight size={16} />
            </button>
          </div>
        </Card>

        {/* AUDIO PLAYER PREVIEW FLOATING MODAL */}
        {playingSession && (
          <div
            style={{
              position: 'fixed',
              bottom: '24px',
              right: '24px',
              background: '#ffffff',
              borderRadius: '20px',
              padding: '16px 20px',
              boxShadow: '0 12px 36px rgba(0, 0, 0, 0.12)',
              border: '1px solid #e5e7eb',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              zIndex: 100,
              maxWidth: '360px',
            }}
            className="animate-entrance"
          >
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#f5f0fb', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b' }}>
              <Volume2 size={20} />
            </div>

            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ margin: 0, fontSize: '13px', fontWeight: '700', color: '#111827', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {playingSession.title}
              </p>
              <p style={{ margin: 0, fontSize: '11px', color: '#6b7280' }}>
                Playing Audio Preview • {playingSession.duration}
              </p>
            </div>

            <button
              onClick={() => setIsPlayingAudio((prev) => !prev)}
              style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#65597b', color: '#ffffff', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            >
              {isPlayingAudio ? <Pause size={15} /> : <Play size={15} />}
            </button>

            <button
              onClick={() => {
                setPlayingSession(null);
                setIsPlayingAudio(false);
              }}
              style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default History;
