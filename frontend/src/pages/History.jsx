import React, { useState, useEffect, useRef } from 'react';
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
  HelpCircle,
  UserCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  Eye,
  AlertCircle,
  Award,
  ChevronDown,
  Check,
  RotateCcw,
  RotateCw,
  VolumeX,
  Square,
  Radio,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import { getHistorySessions, getHistorySessionDetail, exportHistoryCSV } from '../services/historyService';


export const History = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [trackFilter, setTrackFilter] = useState('all');

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Custom Glassmorphic Dropdowns State & Refs
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [isDateDropdownOpen, setIsDateDropdownOpen] = useState(false);
  const statusDropdownRef = useRef(null);
  const dateDropdownRef = useRef(null);

  // Audio player state
  const [playingSession, setPlayingSession] = useState(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlayingAudio(false);
    setPlayingSession(null);
  };

  const formatTime = (secs) => {
    if (isNaN(secs) || secs < 0) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Inspection Modal State
  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [inspectingSessionId, setInspectingSessionId] = useState(null);
  const [inspectDetail, setInspectDetail] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [inspectTab, setInspectTab] = useState('questions'); // 'questions' | 'resume' | 'evaluation'

  // Custom date range modal state
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [customMode, setCustomMode] = useState('days'); // 'days' | 'dates'
  const [customDays, setCustomDays] = useState(45);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [appliedCustomOptions, setAppliedCustomOptions] = useState({});

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: 'completed', label: 'Completed Reports' },
    { value: 'pending', label: 'Pending / In-Progress' },
    { value: 'ready', label: 'Ready to Practice' },
  ];

  const dateOptions = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '15d', label: 'Last 15 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '60d', label: 'Last 60 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: 'all', label: 'All Time' },
    { value: 'custom', label: 'Custom Range...' },
  ];

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (statusDropdownRef.current && !statusDropdownRef.current.contains(event.target)) {
        setIsStatusDropdownOpen(false);
      }
      if (dateDropdownRef.current && !dateDropdownRef.current.contains(event.target)) {
        setIsDateDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchHistory = async (overrideDateFilter, overrideStatusFilter, overrideTrackFilter, overrideSearch, customOpts) => {
    setLoading(true);
    try {
      const activeDateFilter = overrideDateFilter !== undefined ? overrideDateFilter : dateFilter;
      const activeStatusFilter = overrideStatusFilter !== undefined ? overrideStatusFilter : statusFilter;
      const activeTrackFilter = overrideTrackFilter !== undefined ? overrideTrackFilter : trackFilter;
      const activeSearch = overrideSearch !== undefined ? overrideSearch : searchTerm;
      const activeCustomOpts = customOpts !== undefined ? customOpts : appliedCustomOptions;

      const data = await getHistorySessions({
        statusFilter: activeStatusFilter,
        search: activeSearch,
        dateFilter: activeDateFilter,
        trackFilter: activeTrackFilter,
      }, activeCustomOpts);
      setSessions(data.sessions || []);
    } catch (err) {
      console.warn('Backend history fetch warning:', err);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFilter !== 'custom') {
      fetchHistory();
    }
  }, [dateFilter, statusFilter, trackFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchHistory();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSelectDateFilter = (newVal) => {
    setDateFilter(newVal);
    if (newVal === 'custom') {
      setShowCustomModal(true);
    } else {
      setShowCustomModal(false);
      fetchHistory(newVal);
    }
  };

  const handleApplyCustom = () => {
    const opts = {};
    if (customMode === 'days') {
      opts.customDays = Number(customDays) || 30;
    } else {
      opts.startDate = startDate;
      opts.endDate = endDate;
    }
    setAppliedCustomOptions(opts);
    setShowCustomModal(false);
    fetchHistory('custom', undefined, undefined, undefined, opts);
  };

  const handleOpenInspectModal = async (sessionId) => {
    setInspectingSessionId(sessionId);
    setInspectModalOpen(true);
    setInspectLoading(true);
    try {
      const detail = await getHistorySessionDetail(sessionId);
      setInspectDetail(detail);
    } catch (err) {
      console.error('Failed to load session details:', err);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleTogglePlay = (session) => {
    if (playingSession?.id === session.id) {
      setIsPlayingAudio((prev) => !prev);
    } else {
      setPlayingSession(session);
      setIsPlayingAudio(true);
    }
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#dcfce7', color: '#15803d', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} /> Completed
          </span>
        );
      case 'ready':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={13} /> Ready to Practice
          </span>
        );
      case 'evaluating':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#fef3c7', color: '#d97706', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={13} /> Evaluating...
          </span>
        );
      default:
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '9999px', background: '#e0f2fe', color: '#0369a1', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={13} /> {status}
          </span>
        );
    }
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)', position: 'relative' }}>
      {/* Shared Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <PageWrapper>

        
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
          className="animate-entrance history-hero-card"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1
              className="history-hero-title"
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
          <p className="history-hero-subtitle" style={{ fontSize: '14px', color: '#6b7280', margin: '8px 0 0 0', lineHeight: '1.5' }}>
            Review past practice sessions, inspect generated 15-question trees, analyze resume skill match, and listen to continuous audio recordings.
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
            position: 'relative',
            zIndex: 50,
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)',
          }}
          className="history-filter-card"
        >
          {/* Left Inputs */}
          <div className="history-filter-inputs" style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', flex: 1, position: 'relative', zIndex: 60 }}>
            {/* Search Input */}
            <div
              className="history-search-box"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: '#f3f4f6',
                borderRadius: '9999px',
                padding: '8px 16px',
                minWidth: '220px',
              }}
            >
              <Search size={15} style={{ color: '#9ca3af', flexShrink: 0 }} />
              <input
                type="text"
                placeholder="Search sessions..."
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


            {/* Custom Glassmorphic Status Filter Dropdown */}
            <div ref={statusDropdownRef} style={{ position: 'relative', zIndex: 70 }}>
              <button
                type="button"
                onClick={() => {
                  setIsStatusDropdownOpen((prev) => !prev);
                  setIsDateDropdownOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#ffffff',
                  border: isStatusDropdownOpen ? '1px solid #65597b' : '1px solid #e5e7eb',
                  padding: '8px 16px',
                  borderRadius: '9999px',
                  fontSize: '13px',
                  fontWeight: '700',
                  color: '#374151',
                  cursor: 'pointer',
                  boxShadow: isStatusDropdownOpen ? '0 0 0 3px rgba(101, 89, 123, 0.12)' : '0 2px 6px rgba(0, 0, 0, 0.03)',
                  transition: 'all 200ms ease',
                }}
              >
                <Filter size={14} style={{ color: '#65597b' }} />
                <span>
                  {statusOptions.find((o) => o.value === statusFilter)?.label || 'All Statuses'}
                </span>
                <ChevronDown
                  size={14}
                  style={{
                    color: '#6b7280',
                    transform: isStatusDropdownOpen ? 'rotate(180deg)' : 'none',
                    transition: 'transform 200ms ease',
                  }}
                />
              </button>

              {/* Glassmorphic Dropdown Menu */}
              {isStatusDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '44px',
                    left: 0,
                    zIndex: 9999,
                    width: '200px',
                    background: 'rgba(255, 255, 255, 0.98)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid rgba(229, 231, 235, 0.8)',
                    borderRadius: '16px',
                    padding: '6px',
                    boxShadow: '0 16px 36px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06)',
                  }}
                  className="animate-entrance"
                >
                  {statusOptions.map((opt) => {
                    const isSelected = statusFilter === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => {
                          setIsStatusDropdownOpen(false);
                          setStatusFilter(opt.value);
                        }}
                        style={{
                          width: '100%',
                          padding: '9px 12px',
                          borderRadius: '10px',
                          border: 'none',
                          background: isSelected ? '#ede6f8' : 'transparent',
                          color: isSelected ? '#65597b' : '#374151',
                          fontSize: '13px',
                          fontWeight: isSelected ? '700' : '600',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          cursor: 'pointer',
                          transition: 'background 150ms ease, color 150ms ease',
                          textAlign: 'left',
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) e.currentTarget.style.background = '#f5f3ff';
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) e.currentTarget.style.background = 'transparent';
                        }}
                      >
                        <span>{opt.label}</span>
                        {isSelected && <Check size={14} style={{ color: '#65597b' }} />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Custom Glassmorphic Date Filter Dropdown */}
            <div ref={dateDropdownRef} style={{ position: 'relative', zIndex: 70 }}>
              <button
                type="button"
                onClick={() => {
                  setIsDateDropdownOpen((prev) => !prev);
                  setIsStatusDropdownOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#ffffff',
                  border: isDateDropdownOpen ? '1px solid #65597b' : '1px solid #e5e7eb',
                  padding: '8px 16px',
                  borderRadius: '9999px',
                  fontSize: '13px',
                  fontWeight: '700',
                  color: '#374151',
                  cursor: 'pointer',
                  boxShadow: isDateDropdownOpen ? '0 0 0 3px rgba(101, 89, 123, 0.12)' : '0 2px 6px rgba(0, 0, 0, 0.03)',
                  transition: 'all 200ms ease',
                }}
              >
                <Calendar size={14} style={{ color: '#65597b' }} />
                <span>
                  {dateOptions.find((o) => o.value === dateFilter)?.label || 'All Time'}
                </span>
                <ChevronDown
                  size={14}
                  style={{
                    color: '#6b7280',
                    transform: isDateDropdownOpen ? 'rotate(180deg)' : 'none',
                    transition: 'transform 200ms ease',
                  }}
                />
              </button>

              {/* Glassmorphic Dropdown Menu */}
              {isDateDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '44px',
                    left: 0,
                    zIndex: 9999,
                    width: '190px',
                    background: 'rgba(255, 255, 255, 0.98)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid rgba(229, 231, 235, 0.8)',
                    borderRadius: '16px',
                    padding: '6px',
                    boxShadow: '0 16px 36px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06)',
                  }}
                  className="animate-entrance"
                >
                  {dateOptions.map((opt) => {
                    const isSelected = dateFilter === opt.value;
                    const isCustom = opt.value === 'custom';
                    return (
                      <React.Fragment key={opt.value}>
                        {isCustom && <div style={{ height: '1px', background: '#f3f4f6', margin: '4px 0' }} />}
                        <button
                          type="button"
                          onClick={() => {
                            setIsDateDropdownOpen(false);
                            handleSelectDateFilter(opt.value);
                          }}
                          style={{
                            width: '100%',
                            padding: '9px 12px',
                            borderRadius: '10px',
                            border: 'none',
                            background: isSelected ? '#ede6f8' : 'transparent',
                            color: isSelected ? '#65597b' : '#374151',
                            fontSize: '13px',
                            fontWeight: isSelected ? '700' : '600',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            transition: 'background 150ms ease, color 150ms ease',
                            textAlign: 'left',
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.background = '#f5f3ff';
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) e.currentTarget.style.background = 'transparent';
                          }}
                        >
                          <span>{opt.label}</span>
                          {isSelected && <Check size={14} style={{ color: '#65597b' }} />}
                        </button>
                      </React.Fragment>
                    );
                  })}
                </div>
              )}

              {/* Custom Range Popover Card */}
              {showCustomModal && (
                <div
                  style={{
                    position: 'absolute',
                    top: '48px',
                    left: 0,
                    zIndex: 9999,
                    width: '320px',
                    background: 'rgba(255, 255, 255, 0.98)',
                    backdropFilter: 'blur(16px)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '20px',
                    padding: '20px',
                    boxShadow: '0 16px 40px rgba(0, 0, 0, 0.12)',
                  }}
                  className="animate-entrance"
                >
                  <h3 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 14px 0', color: '#111827' }}>
                    Select Custom Time Window
                  </h3>

                  {/* Sub-mode Switcher */}
                  <div style={{ display: 'flex', background: '#f3f4f6', padding: '4px', borderRadius: '12px', marginBottom: '16px' }}>
                    <button
                      onClick={() => setCustomMode('days')}
                      style={{
                        flex: 1,
                        padding: '6px',
                        borderRadius: '8px',
                        border: 'none',
                        fontSize: '12px',
                        fontWeight: '700',
                        background: customMode === 'days' ? '#ffffff' : 'transparent',
                        color: customMode === 'days' ? '#111827' : '#6b7280',
                        cursor: 'pointer',
                        boxShadow: customMode === 'days' ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                      }}
                    >
                      Days Count
                    </button>
                    <button
                      onClick={() => setCustomMode('dates')}
                      style={{
                        flex: 1,
                        padding: '6px',
                        borderRadius: '8px',
                        border: 'none',
                        fontSize: '12px',
                        fontWeight: '700',
                        background: customMode === 'dates' ? '#ffffff' : 'transparent',
                        color: customMode === 'dates' ? '#111827' : '#6b7280',
                        cursor: 'pointer',
                        boxShadow: customMode === 'dates' ? '0 2px 4px rgba(0,0,0,0.05)' : 'none',
                      }}
                    >
                      Date Picker
                    </button>
                  </div>

                  {customMode === 'days' ? (
                    <div style={{ marginBottom: '16px' }}>
                      <label style={{ fontSize: '12px', fontWeight: '700', color: '#374151', display: 'block', marginBottom: '6px' }}>
                        Number of Lookback Days
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={customDays}
                        onChange={(e) => setCustomDays(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '10px 14px',
                          borderRadius: '10px',
                          border: '1px solid #d1d5db',
                          fontSize: '14px',
                          outline: 'none',
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                      <div>
                        <label style={{ fontSize: '12px', fontWeight: '700', color: '#374151', display: 'block', marginBottom: '4px' }}>
                          Start Date
                        </label>
                        <input
                          type="date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: '10px',
                            border: '1px solid #d1d5db',
                            fontSize: '13px',
                            boxSizing: 'border-box',
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ fontSize: '12px', fontWeight: '700', color: '#374151', display: 'block', marginBottom: '4px' }}>
                          End Date
                        </label>
                        <input
                          type="date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: '10px',
                            border: '1px solid #d1d5db',
                            fontSize: '13px',
                            boxSizing: 'border-box',
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => setShowCustomModal(false)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        borderRadius: '10px',
                        border: '1px solid #d1d5db',
                        background: '#ffffff',
                        color: '#374151',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleApplyCustom}
                      style={{
                        flex: 1,
                        padding: '8px',
                        borderRadius: '10px',
                        border: 'none',
                        background: '#65597b',
                        color: '#ffffff',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      Apply Filter
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Action Button */}
          <button
            onClick={() => exportHistoryCSV(sessions)}
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
            <span>Export CSV</span>
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
          className="history-table-card"
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #f3f4f6', color: '#6b7280', fontSize: '11px', fontWeight: '800', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px' }}>DATE</th>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px' }}>TRACK / ROLE</th>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px' }}>STATUS</th>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px' }}>SCORE</th>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px' }}>RECORDING</th>
                  <th className="history-table-header-cell" style={{ padding: '12px 16px', textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                      Loading candidate session history archives...
                    </td>
                  </tr>
                ) : sessions.length > 0 ? (
                  sessions.map((session, idx) => (
                    <tr
                      key={session.id || idx}
                      style={{
                        borderBottom: idx === sessions.length - 1 ? 'none' : '1px solid #f9fafb',
                        transition: 'background 150ms ease',
                      }}
                    >
                      {/* DATE */}
                      <td className="history-date-cell" style={{ padding: '18px 16px', fontSize: '14px', fontWeight: '600', color: '#374151' }}>
                        {session.date_text || 'Recent'}
                      </td>

                      {/* TRACK / ROLE */}
                      <td className="history-role-cell" style={{ padding: '18px 16px' }}>
                        <div>
                          <span className="history-role-title" style={{ fontSize: '14px', fontWeight: '700', color: '#111827', display: 'block' }}>
                            {session.role_title}
                          </span>
                          <span className="history-role-company" style={{ fontSize: '12px', color: '#6b7280' }}>
                            {session.company}
                          </span>
                        </div>
                      </td>

                      {/* STATUS */}
                      <td className="history-status-cell" style={{ padding: '18px 16px' }}>
                        {renderStatusBadge(session.status)}
                      </td>

                      {/* SCORE */}
                      <td className="history-score-cell" style={{ padding: '18px 16px', fontSize: '14px', fontWeight: '800', color: '#111827' }}>
                        {session.score !== null && session.score !== undefined ? `${session.score}/100` : '—'}
                      </td>

                      {/* RECORDING LISTEN */}
                      <td className="history-recording-cell" style={{ padding: '18px 16px' }}>
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

                      {/* ACTIONS */}
                      <td className="history-actions-cell" style={{ padding: '18px 16px', textAlign: 'right' }}>

                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                          {/* Inspect Questions & Resume Analysis Button */}
                          <button
                            onClick={() => handleOpenInspectModal(session.id)}
                            title="Inspect generated 15-question tree & candidate profile analysis"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '8px 14px',
                              borderRadius: '9999px',
                              background: '#f3e8ff',
                              color: '#65597b',
                              border: '1px solid #e9d5ff',
                              fontSize: '12px',
                              fontWeight: '700',
                              cursor: 'pointer',
                            }}
                          >
                            <Eye size={14} />
                            <span>Inspect Details</span>
                          </button>

                          {/* View Full Report Button */}
                          {session.has_report && (
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
                          )}

                          {/* Start Practice Button if Ready */}
                          {session.status === 'ready' && (
                            <button
                              onClick={() => navigate(`/interview/${session.id}`)}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '8px 16px',
                                borderRadius: '9999px',
                                background: '#65597b',
                                color: '#ffffff',
                                border: 'none',
                                fontSize: '12px',
                                fontWeight: '700',
                                cursor: 'pointer',
                              }}
                            >
                              <Play size={14} />
                              <span>Start Interview</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ padding: '48px 24px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#f3e8ff', color: '#65597b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Sparkles size={24} />
                        </div>
                        <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: 0 }}>
                          No Session History Found
                        </h3>
                        <p style={{ fontSize: '13px', color: '#6b7280', margin: 0, maxWidth: '360px', lineHeight: '1.5' }}>
                          No practice sessions match your current filter selection. Create your first interview track from the Dashboard.
                        </p>
                        <button
                          onClick={() => navigate('/setup')}
                          style={{
                            marginTop: '8px',
                            padding: '10px 22px',
                            borderRadius: '9999px',
                            background: '#65597b',
                            color: '#ffffff',
                            border: 'none',
                            fontSize: '13px',
                            fontWeight: '700',
                            cursor: 'pointer',
                            boxShadow: '0 4px 12px rgba(101, 89, 123, 0.25)',
                          }}
                        >
                          Configure Practice Track
                        </button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* PAGINATION CONTROLS */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #f3f4f6' }}>
            <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '500' }}>
              Showing {sessions.length} session archives
            </span>
          </div>
        </Card>

        {/* DEEP-DIVE SESSION INSPECTION MODAL */}
        {inspectModalOpen && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(17, 24, 39, 0.4)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '24px',
            }}
          >
            <div
              style={{
                width: '100%',
                maxWidth: '780px',
                maxHeight: '85vh',
                background: '#ffffff',
                borderRadius: '24px',
                boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                border: '1px solid rgba(255, 255, 255, 0.8)',
              }}
              className="animate-entrance"
            >
              {/* Modal Header */}
              <div style={{ padding: '20px 28px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#fafafa' }}>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: 0 }}>
                    {inspectDetail?.role_title || 'Session Inspection'}
                  </h3>
                  <span style={{ fontSize: '12px', color: '#6b7280' }}>
                    {inspectDetail?.company} • {inspectDetail?.seniority_level} Level
                  </span>
                </div>
                <button
                  onClick={() => {
                    setInspectModalOpen(false);
                    setInspectDetail(null);
                  }}
                  style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Modal Navigation Tabs */}
              <div style={{ display: 'flex', borderBottom: '1px solid #f3f4f6', background: '#ffffff', padding: '0 28px' }}>
                <button
                  onClick={() => setInspectTab('questions')}
                  style={{
                    padding: '14px 20px',
                    border: 'none',
                    background: 'transparent',
                    borderBottom: inspectTab === 'questions' ? '2px solid #65597b' : '2px solid transparent',
                    color: inspectTab === 'questions' ? '#65597b' : '#6b7280',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <HelpCircle size={16} />
                  <span>Question Tree ({inspectDetail?.question_tree?.length || 0})</span>
                </button>
                <button
                  onClick={() => setInspectTab('resume')}
                  style={{
                    padding: '14px 20px',
                    border: 'none',
                    background: 'transparent',
                    borderBottom: inspectTab === 'resume' ? '2px solid #65597b' : '2px solid transparent',
                    color: inspectTab === 'resume' ? '#65597b' : '#6b7280',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <UserCheck size={16} />
                  <span>Resume & Profile Analysis</span>
                </button>
              </div>

              {/* Modal Body Content */}
              <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}>
                {inspectLoading ? (
                  <p style={{ textAlign: 'center', color: '#6b7280', padding: '32px' }}>Loading inspection data...</p>
                ) : inspectTab === 'questions' ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    {inspectDetail?.question_tree?.length > 0 ? (
                      inspectDetail.question_tree.map((q, qIdx) => (
                        <div
                          key={qIdx}
                          style={{
                            padding: '16px',
                            borderRadius: '16px',
                            background: '#f9fafb',
                            border: '1px solid #f3f4f6',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <span style={{ fontSize: '11px', fontWeight: '800', color: '#65597b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                              Q{qIdx + 1} • {q.topic || 'Domain Question'}
                            </span>
                            {q.difficulty && (
                              <span style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b' }}>
                                {q.difficulty}
                              </span>
                            )}
                          </div>
                          <p style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: '0 0 8px 0', lineHeight: '1.4' }}>
                            {q.question_text || q.text}
                          </p>
                          {q.expected_keywords && (
                            <div style={{ fontSize: '12px', color: '#6b7280' }}>
                              <strong>Rubric Keywords:</strong> {Array.isArray(q.expected_keywords) ? q.expected_keywords.join(', ') : q.expected_keywords}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <p style={{ color: '#6b7280', fontSize: '13px', textAlign: 'center', padding: '24px' }}>
                        No question tree generated for this session yet.
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    {inspectDetail?.resume_analysis ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div style={{ background: '#f5f0fb', padding: '16px', borderRadius: '16px', border: '1px solid #e9d5ff' }}>
                          <h4 style={{ fontSize: '14px', fontWeight: '800', color: '#65597b', margin: '0 0 6px 0' }}>
                            Candidate Profile Match
                          </h4>
                          <p style={{ fontSize: '13px', color: '#4b5563', margin: 0, lineHeight: '1.5' }}>
                            {inspectDetail.resume_analysis.summary || inspectDetail.resume_analysis.overview || 'Profile analyzed against target job description requirements.'}
                          </p>
                        </div>
                        {inspectDetail.resume_analysis.skills_overlap && (
                          <div>
                            <strong style={{ fontSize: '13px', color: '#111827', display: 'block', marginBottom: '6px' }}>Skill Overlap Highlights:</strong>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                              {(inspectDetail.resume_analysis.skills_overlap || []).map((s, idx) => (
                                <span key={idx} style={{ fontSize: '12px', padding: '4px 10px', background: '#dcfce7', color: '#15803d', borderRadius: '9999px', fontWeight: '600' }}>
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: '#6b7280', fontSize: '13px', textAlign: 'center', padding: '24px' }}>
                        No resume analysis artifact present for this session.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* INTERACTIVE GLASSMORPHIC AUDIO PLAYER MODAL POPUP */}
        {playingSession && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(17, 24, 39, 0.45)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 99999,
              padding: '24px',
            }}
          >
            <div
              style={{
                width: '100%',
                maxWidth: '520px',
                background: '#ffffff',
                borderRadius: '24px',
                padding: '32px',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.2), 0 4px 16px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(229, 231, 235, 0.8)',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
                position: 'relative',
              }}
              className="animate-entrance"
            >
              {/* Hidden HTML5 Audio Element */}
              <audio
                ref={audioRef}
                src={`/api/v1/voice/recording/${playingSession.id}`}
                onTimeUpdate={() => {
                  if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
                }}
                onLoadedMetadata={() => {
                  if (audioRef.current) setDuration(audioRef.current.duration || 0);
                }}
                onEnded={() => setIsPlayingAudio(false)}
                autoPlay
              />

              {/* Modal Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '44px', height: '44px', borderRadius: '16px', background: '#f5f0fb', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b' }}>
                    <Headphones size={22} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: 0, maxWidth: '340px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {playingSession.role_title || playingSession.track}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#6b7280', display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <Radio size={12} style={{ color: isPlayingAudio ? '#22c55e' : '#9ca3af' }} />
                      {playingSession.company || 'Tech Corporation'} • {isPlayingAudio ? 'Live Playing' : 'Paused'}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleStopAudio}
                  style={{ background: '#f3f4f6', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280', cursor: 'pointer' }}
                >
                  <X size={18} />
                </button>
              </div>

              {/* Pulsing Animated Waveform Indicator */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', height: '36px', background: '#faf8ff', borderRadius: '14px', border: '1px solid #ede6f8', padding: '0 16px' }}>
                {[40, 70, 30, 90, 60, 45, 80, 100, 50, 75, 35, 85, 60, 40].map((h, i) => (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      maxWidth: '4px',
                      height: isPlayingAudio ? `${h}%` : '20%',
                      background: isPlayingAudio ? '#65597b' : '#d1d5db',
                      borderRadius: '4px',
                      transition: 'height 180ms ease, background 180ms ease',
                    }}
                  />
                ))}
              </div>

              {/* Interactive Scrubbing Progress Bar */}
              <div>
                <input
                  type="range"
                  min="0"
                  max={duration || 100}
                  step="0.1"
                  value={currentTime}
                  onChange={(e) => {
                    const newTime = parseFloat(e.target.value);
                    setCurrentTime(newTime);
                    if (audioRef.current) audioRef.current.currentTime = newTime;
                  }}
                  style={{
                    width: '100%',
                    accentColor: '#65597b',
                    cursor: 'pointer',
                    height: '6px',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '700', color: '#6b7280', marginTop: '6px' }}>
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>

              {/* Main Playback Controls Row */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '20px' }}>
                {/* Skip Back 10s */}
                <button
                  onClick={() => {
                    if (audioRef.current) {
                      const t = Math.max(0, audioRef.current.currentTime - 10);
                      audioRef.current.currentTime = t;
                      setCurrentTime(t);
                    }
                  }}
                  title="Rewind 10s"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '8px 14px',
                    borderRadius: '9999px',
                    background: '#f3f4f6',
                    border: 'none',
                    color: '#374151',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  <RotateCcw size={15} />
                  <span>-10s</span>
                </button>

                {/* Big Play/Pause Toggle */}
                <button
                  onClick={() => {
                    if (audioRef.current) {
                      if (isPlayingAudio) {
                        audioRef.current.pause();
                        setIsPlayingAudio(false);
                      } else {
                        audioRef.current.play();
                        setIsPlayingAudio(true);
                      }
                    }
                  }}
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    background: '#65597b',
                    color: '#ffffff',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(101, 89, 123, 0.35)',
                    transition: 'transform 150ms ease',
                  }}
                >
                  {isPlayingAudio ? <Pause size={24} /> : <Play size={24} style={{ marginLeft: '3px' }} />}
                </button>

                {/* Forward 10s */}
                <button
                  onClick={() => {
                    if (audioRef.current) {
                      const t = Math.min(duration, audioRef.current.currentTime + 10);
                      audioRef.current.currentTime = t;
                      setCurrentTime(t);
                    }
                  }}
                  title="Fast Forward 10s"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '8px 14px',
                    borderRadius: '9999px',
                    background: '#f3f4f6',
                    border: 'none',
                    color: '#374151',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  <span>+10s</span>
                  <RotateCw size={15} />
                </button>
              </div>

              {/* Bottom Utilities Control Bar (Volume & Speed & Stop) */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '14px', borderTop: '1px solid #f3f4f6' }}>
                {/* Volume Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={() => {
                      if (audioRef.current) {
                        audioRef.current.muted = !isMuted;
                        setIsMuted(!isMuted);
                      }
                    }}
                    style={{ background: 'transparent', border: 'none', color: '#6b7280', cursor: 'pointer', padding: 0 }}
                  >
                    {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setVolume(v);
                      if (audioRef.current) {
                        audioRef.current.volume = v;
                        audioRef.current.muted = v === 0;
                        setIsMuted(v === 0);
                      }
                    }}
                    style={{ width: '80px', accentColor: '#65597b', cursor: 'pointer' }}
                  />
                </div>

                {/* Speed Toggles */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: '#f3f4f6', padding: '3px', borderRadius: '10px' }}>
                  {[1.0, 1.25, 1.5, 2.0].map((rate) => (
                    <button
                      key={rate}
                      onClick={() => {
                        setPlaybackRate(rate);
                        if (audioRef.current) audioRef.current.playbackRate = rate;
                      }}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '7px',
                        border: 'none',
                        fontSize: '11px',
                        fontWeight: '700',
                        background: playbackRate === rate ? '#ffffff' : 'transparent',
                        color: playbackRate === rate ? '#65597b' : '#6b7280',
                        cursor: 'pointer',
                        boxShadow: playbackRate === rate ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                      }}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>

                {/* Stop & Close Button */}
                <button
                  onClick={handleStopAudio}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: '#fee2e2',
                    color: '#dc2626',
                    border: 'none',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  <Square size={12} />
                  <span>Stop & End</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </PageWrapper>
    </div>
  );
};

export default History;


