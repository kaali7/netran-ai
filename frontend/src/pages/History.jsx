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
  Trash2,
  Cpu,
  Mic,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';
import {
  getHistorySessions,
  getHistorySessionDetail,
  deleteHistorySession,
  triggerEvaluation,
  exportHistoryCSV,
} from '../services/historyService';

export const History = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [trackFilter, setTrackFilter] = useState('all');

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Toast feedback state
  const [toastMessage, setToastMessage] = useState(null);
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Custom Glassmorphic Dropdowns State & Refs
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [isDateDropdownOpen, setIsDateDropdownOpen] = useState(false);
  const statusDropdownRef = useRef(null);
  const dateDropdownRef = useRef(null);

  // Inspection Modal State
  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [inspectingSessionId, setInspectingSessionId] = useState(null);
  const [inspectDetail, setInspectDetail] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [inspectTab, setInspectTab] = useState('questions'); // 'questions' | 'resume' | 'evaluation'

  // Delete Confirmation Modal State
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [isDeletingSession, setIsDeletingSession] = useState(false);

  // Interactive Turn-by-Turn Audio Player Modal State
  const [audioModalOpen, setAudioModalOpen] = useState(false);
  const [audioModalSession, setAudioModalSession] = useState(null);
  const [audioModalDetail, setAudioModalDetail] = useState(null);
  const [audioModalLoading, setAudioModalLoading] = useState(false);
  const [activeTurnIndex, setActiveTurnIndex] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isContinuousPlay, setIsContinuousPlay] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const audioRef = useRef(null);
  const turnCardRefs = useRef([]);

  // Action Button Loading State
  const [actionLoadingId, setActionLoadingId] = useState(null);

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
    { value: 'in_progress', label: 'In-Progress Interviews' },
    { value: 'evaluating', label: 'Evaluating...' },
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

  // Inspect Modal
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

  // Delete Session
  const handleDeleteClick = (session) => {
    setSessionToDelete(session);
  };

  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return;
    setIsDeletingSession(true);
    try {
      await deleteHistorySession(sessionToDelete.id);
      setSessions((prev) => prev.filter((s) => s.id !== sessionToDelete.id));
      showToast('Practice session and associated recordings deleted successfully.');
      setSessionToDelete(null);
    } catch (err) {
      console.error('Failed to delete session:', err);
      showToast('Failed to delete session. Please try again.');
    } finally {
      setIsDeletingSession(false);
    }
  };

  // Contextual Primary Action Click (Resume / Complete / Start / View)
  const handleContextualAction = async (session) => {
    if (session.status === 'in_progress') {
      navigate(`/interview/${session.id}`);
    } else if (session.status === 'ready') {
      navigate(`/interview/${session.id}`);
    } else if (session.status === 'evaluating') {
      if (session.has_report) {
        navigate(`/report/${session.id}`);
      } else {
        setActionLoadingId(session.id);
        try {
          await triggerEvaluation(session.id);
        } catch (e) {
          console.warn('Evaluation trigger note:', e);
        } finally {
          setActionLoadingId(null);
          navigate(`/processing/${session.id}`);
        }
      }
    } else if (session.status === 'completed' || session.has_report) {
      navigate(`/report/${session.id}`);
    } else {
      navigate('/setup');
    }
  };

  // --- Turn-by-Turn Audio Player Logic ---
  const handleOpenAudioModal = async (session) => {
    setAudioModalSession(session);
    setAudioModalOpen(true);
    setAudioModalLoading(true);
    setActiveTurnIndex(0);
    setIsPlayingAudio(false);
    setCurrentTime(0);

    try {
      const detail = await getHistorySessionDetail(session.id);
      setAudioModalDetail(detail);
    } catch (err) {
      console.error('Failed to load session audio details:', err);
    } finally {
      setAudioModalLoading(false);
    }
  };

  const handleCloseAudioModal = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlayingAudio(false);
    setAudioModalOpen(false);
    setAudioModalSession(null);
    setAudioModalDetail(null);
  };

  const getActiveTurnsList = () => {
    if (!audioModalDetail) return [];
    if (Array.isArray(audioModalDetail.turns) && audioModalDetail.turns.length > 0) {
      return audioModalDetail.turns;
    }
    // Fallback: build placeholder turn entries from question_tree if turns not yet populated
    if (Array.isArray(audioModalDetail.question_tree) && audioModalDetail.question_tree.length > 0) {
      return audioModalDetail.question_tree.map((q, idx) => ({
        turn_id: idx + 1,
        question_text: q.question_text || q.text,
        topic: q.topic || `Topic ${idx + 1}`,
        difficulty: q.difficulty || 'Intermediate',
        candidate_transcript: '(No spoken answer recorded for this question)',
        audio_start_sec: 0,
        audio_end_sec: 0,
      }));
    }
    return [];
  };

  const playTurn = (index) => {
    const turns = getActiveTurnsList();
    if (!turns[index]) return;
    setActiveTurnIndex(index);

    const turn = turns[index];
    const startSec = turn.audio_start_sec || 0;

    if (audioRef.current) {
      audioRef.current.currentTime = startSec;
      audioRef.current.play().then(() => {
        setIsPlayingAudio(true);
      }).catch((e) => {
        console.warn('Audio play request error:', e);
      });
    }

    // Scroll turn into view smoothly
    if (turnCardRefs.current[index]) {
      turnCardRefs.current[index].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  const toggleMasterPlayPause = () => {
    if (!audioRef.current) return;
    if (isPlayingAudio) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlayingAudio(true);
      }).catch((e) => console.warn('Audio play error:', e));
    }
  };

  const handleAudioTimeUpdate = () => {
    if (!audioRef.current) return;
    const curTime = audioRef.current.currentTime;
    setCurrentTime(curTime);

    const turns = getActiveTurnsList();
    if (turns.length === 0) return;

    const currentTurn = turns[activeTurnIndex];
    if (currentTurn && currentTurn.audio_end_sec && currentTurn.audio_end_sec > 0) {
      if (curTime >= currentTurn.audio_end_sec) {
        if (isContinuousPlay && activeTurnIndex < turns.length - 1) {
          // Advance to next turn automatically
          const nextIdx = activeTurnIndex + 1;
          const nextTurn = turns[nextIdx];
          setActiveTurnIndex(nextIdx);
          if (nextTurn && nextTurn.audio_start_sec !== undefined) {
            audioRef.current.currentTime = nextTurn.audio_start_sec;
          }
          if (turnCardRefs.current[nextIdx]) {
            turnCardRefs.current[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        } else {
          // Pause at end of turn
          audioRef.current.pause();
          setIsPlayingAudio(false);
        }
      }
    }
  };

  const handlePrevTurn = () => {
    const turns = getActiveTurnsList();
    if (turns.length === 0) return;
    const newIdx = Math.max(0, activeTurnIndex - 1);
    playTurn(newIdx);
  };

  const handleNextTurn = () => {
    const turns = getActiveTurnsList();
    if (turns.length === 0) return;
    const newIdx = Math.min(turns.length - 1, activeTurnIndex + 1);
    playTurn(newIdx);
  };

  const formatTime = (secs) => {
    if (isNaN(secs) || secs < 0) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '9999px', background: '#dcfce7', color: '#15803d', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={13} /> Completed
          </span>
        );
      case 'ready':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Sparkles size={13} /> Ready to Practice
          </span>
        );
      case 'in_progress':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '9999px', background: '#e0f2fe', color: '#0369a1', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <RotateCw size={13} style={{ animation: 'spin 4s linear infinite' }} /> In Progress
          </span>
        );
      case 'evaluating':
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '9999px', background: '#fef3c7', color: '#d97706', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={13} /> Evaluating...
          </span>
        );
      default:
        return (
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 12px', borderRadius: '9999px', background: '#f3e8ff', color: '#7e22ce', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={13} /> Setup Pending
          </span>
        );
    }
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '60px', fontFamily: 'var(--font-family, system-ui)', position: 'relative' }}>
      {/* Scoped CSS for Responsive History Page */}
      <style>{`
        .history-desktop-table {
          display: block;
        }
        .history-mobile-cards {
          display: none;
        }
        .history-filter-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .history-dropdown-wrapper {
          position: relative;
          z-index: 70;
        }
        .page-wrapper-container {
          gap: 14px !important;
        }

        @media (max-width: 768px) {
          .page-wrapper-container {
            padding: 0 14px 48px 14px !important;
            gap: 12px !important;
          }
          .app-header-nav {
            padding: 12px 0 10px 0 !important;
            margin-bottom: 6px !important;
          }
          .history-hero-card {
            padding: 14px 16px !important;
            border-radius: 16px !important;
            margin-bottom: 0 !important;
          }
          .history-hero-icon-box {
            width: 32px !important;
            height: 32px !important;
            border-radius: 9px !important;
          }
          .history-hero-icon-box svg {
            width: 17px !important;
            height: 17px !important;
          }
          .history-hero-title {
            font-size: 16px !important;
          }
          .history-hero-subtitle {
            font-size: 11px !important;
            margin-top: 4px !important;
            line-height: 1.35 !important;
          }
          .history-filter-card {
            padding: 6px 6px !important;
            border-radius: 12px !important;
            margin-bottom: 0 !important;
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
          }
          .history-filter-inputs {
            width: auto !important;
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
          }
          .history-search-box {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            padding: 0 10px !important;
            height: 36px !important;
            border-radius: 10px !important;
          }
          .history-search-box input {
            font-size: 12px !important;
          }
          .history-filter-row {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 6px !important;
            flex-shrink: 0 !important;
          }
          .history-dropdown-wrapper {
            flex: 0 0 auto !important;
            position: relative !important;
          }
          .history-dropdown-btn {
            width: 36px !important;
            height: 36px !important;
            padding: 0 !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
          }
          .history-btn-label,
          .history-btn-chevron {
            display: none !important;
          }
          .history-dropdown-menu {
            right: 0 !important;
            left: auto !important;
            top: 42px !important;
          }
          .history-export-btn {
            width: 36px !important;
            height: 36px !important;
            padding: 0 !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            margin-top: 0 !important;
            box-sizing: border-box !important;
          }
          .history-table-card {
            padding: 10px 10px !important;
            border-radius: 14px !important;
            margin-bottom: 0 !important;
          }
          .history-desktop-table {
            display: none !important;
          }
          .history-mobile-cards {
            display: flex !important;
            flex-direction: column !important;
            gap: 12px !important;
          }
          .history-session-card {
            background: #ffffff;
            border: 1px solid #eef0f4;
            border-radius: 14px;
            padding: 12px 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
            transition: all 150ms ease;
          }
          .history-session-card:active {
            transform: scale(0.99);
          }
          .history-session-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .history-session-date {
            font-size: 11px;
            font-weight: 600;
            color: #6b7280;
            display: flex;
            align-items: center;
            gap: 5px;
          }
          .history-session-main {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 8px;
          }
          .history-session-info {
            flex: 1;
            min-width: 0;
          }
          .history-session-role {
            font-size: 14px;
            font-weight: 800;
            color: #111827;
            line-height: 1.25;
            margin: 0 0 2px 0;
            word-break: break-word;
          }
          .history-session-company {
            font-size: 11.5px;
            color: #6b7280;
            font-weight: 500;
          }
          .history-session-score-pill {
            font-size: 11.5px;
            font-weight: 800;
            padding: 2.5px 8px;
            border-radius: 9999px;
            background: #ede6f8;
            color: #65597b;
            flex-shrink: 0;
            align-self: flex-start;
          }
          .history-session-actions-row {
            display: flex !important;
            align-items: center !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
            padding-top: 8px !important;
            border-top: 1px dashed #f3f4f6 !important;
            width: 100% !important;
            box-sizing: border-box !important;
          }
          .history-session-actions-row button {
            font-size: 10.5px !important;
            padding: 4px 7px !important;
            border-radius: 9999px !important;
            height: 28px !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            gap: 4px !important;
          }
          .history-session-actions-row button svg {
            width: 12px !important;
            height: 12px !important;
            flex-shrink: 0 !important;
          }
          .history-session-actions-row button.action-delete-btn {
            margin-left: auto !important;
            width: 28px !important;
            height: 28px !important;
            min-width: 28px !important;
            padding: 0 !important;
            border-radius: 50% !important;
            flex-shrink: 0 !important;
          }

          /* Inspect Modal Phone Styles */
          .history-modal-backdrop {
            padding: 12px !important;
            align-items: center !important;
            justify-content: center !important;
          }
          .history-inspect-modal {
            width: 100% !important;
            max-width: 100% !important;
            max-height: 90dvh !important;
            border-radius: 20px !important;
          }
          .history-inspect-header {
            padding: 12px 14px !important;
          }
          .history-inspect-title {
            font-size: 15px !important;
            line-height: 1.25 !important;
          }
          .history-inspect-subtitle {
            font-size: 11px !important;
          }
          .history-modal-close-btn {
            width: 30px !important;
            height: 30px !important;
            border-radius: 50% !important;
            background: #f3f4f6 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
          }
          .history-inspect-tabs {
            padding: 0 10px !important;
            display: flex !important;
          }
          .history-inspect-tab-btn {
            flex: 1 1 50% !important;
            padding: 10px 4px !important;
            font-size: 12px !important;
            justify-content: center !important;
            gap: 5px !important;
          }
          .history-tab-desktop-text {
            display: none !important;
          }
          .history-tab-mobile-text {
            display: inline !important;
          }
          .history-inspect-body {
            padding: 12px 12px !important;
            gap: 10px !important;
          }
          .history-inspect-qcard {
            padding: 10px 12px !important;
            border-radius: 12px !important;
          }
          .history-inspect-qhead {
            margin-bottom: 6px !important;
            gap: 4px !important;
          }
          .history-inspect-qtopic {
            font-size: 10px !important;
          }
          .history-inspect-qdiff {
            font-size: 10px !important;
            padding: 1.5px 6px !important;
          }
          .history-inspect-qtext {
            font-size: 13px !important;
            line-height: 1.35 !important;
            margin: 0 0 6px 0 !important;
          }
          .history-inspect-qkeywords {
            font-size: 11px !important;
          }

          /* Audio Modal Phone Styles */
          .history-audio-modal {
            width: 100% !important;
            max-width: 100% !important;
            height: 92dvh !important;
            max-height: 92dvh !important;
            border-radius: 20px !important;
          }
          .history-audio-header {
            padding: 12px 14px !important;
          }
          .history-audio-icon-box {
            width: 32px !important;
            height: 32px !important;
            border-radius: 10px !important;
          }
          .history-audio-icon-box svg {
            width: 16px !important;
            height: 16px !important;
          }
          .history-audio-title {
            font-size: 14.5px !important;
            line-height: 1.25 !important;
          }
          .history-audio-subtitle {
            display: none !important;
          }
          .history-audio-autoadvance-btn {
            padding: 4px 8px !important;
            font-size: 11px !important;
            border-radius: 9999px !important;
          }
          .history-audio-body {
            padding: 12px 12px !important;
            gap: 10px !important;
          }
          .history-audio-turn-card {
            padding: 12px 12px !important;
            border-radius: 14px !important;
          }
          .history-audio-turn-head {
            flex-wrap: wrap !important;
            gap: 6px !important;
            margin-bottom: 8px !important;
          }
          .history-audio-turn-play-btn {
            width: 28px !important;
            height: 28px !important;
            min-width: 28px !important;
            padding: 0 !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0 !important;
          }
          .history-audio-dock {
            padding: 8px 12px 12px 12px !important;
            gap: 6px !important;
          }
          .history-audio-volume-slider {
            display: none !important;
          }
          .history-audio-nav-btn {
            width: 30px !important;
            height: 30px !important;
            min-width: 30px !important;
            padding: 0 !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0 !important;
          }
          .history-audio-playbtn {
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
          }
          .history-audio-playbtn svg {
            width: 15px !important;
            height: 15px !important;
          }
          .history-audio-speed-group {
            gap: 2px !important;
            padding: 2px !important;
          }
          .history-audio-speed-btn {
            padding: 2px 5px !important;
            font-size: 10px !important;
          }
        }

        .history-tab-desktop-text {
          display: inline;
        }
        .history-tab-mobile-text {
          display: none;
        }
      `}</style>

      {/* Shared Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <PageWrapper>

        {/* Toast Notification Banner */}
        {toastMessage && (
          <div
            style={{
              position: 'fixed',
              top: '80px',
              right: '24px',
              zIndex: 999999,
              background: '#111827',
              color: '#ffffff',
              padding: '12px 20px',
              borderRadius: '16px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
              fontSize: '13px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
            className="animate-entrance"
          >
            <CheckCircle2 size={16} style={{ color: '#4ade80' }} />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* HERO BANNER CARD */}
        <Card
          style={{
            padding: '36px 40px',
            background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
            borderRadius: '24px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 24px rgba(101, 89, 123, 0.04)',
          }}
          className="animate-entrance history-hero-card"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="history-hero-icon-box" style={{ width: '42px', height: '42px', borderRadius: '14px', background: '#ede6f8', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b' }}>
              <FileText size={22} />
            </div>
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
          </div>
          <p className="history-hero-subtitle" style={{ fontSize: '14px', color: '#6b7280', margin: '10px 0 0 0', lineHeight: '1.5' }}>
            Review past practice sessions, resume incomplete interviews, trigger pending evaluations, inspect 15-question trees, and listen to turn-by-turn question & answer audio recordings.
          </p>
        </Card>

        {/* FILTER & CONTROLS BAR CONTAINER */}
        <Card
          style={{
            padding: '16px 20px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
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
                placeholder="Search sessions or roles..."
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

            {/* Filter Dropdown Row on Mobile / Inline on Desktop */}
            <div className="history-filter-row">
              {/* Custom Glassmorphic Status Filter Dropdown */}
              <div className="history-dropdown-wrapper" ref={statusDropdownRef}>
                <button
                  type="button"
                  className="history-dropdown-btn"
                  onClick={() => {
                    setIsStatusDropdownOpen((prev) => !prev);
                    setIsDateDropdownOpen(false);
                  }}
                  title={statusOptions.find((o) => o.value === statusFilter)?.label || 'All Statuses'}
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
                  <Filter size={15} style={{ color: '#65597b', flexShrink: 0 }} />
                  <span className="history-btn-label">
                    {statusOptions.find((o) => o.value === statusFilter)?.label || 'All Statuses'}
                  </span>
                  <span className="history-btn-chevron">
                    <ChevronDown
                      size={14}
                      style={{
                        color: '#6b7280',
                        transform: isStatusDropdownOpen ? 'rotate(180deg)' : 'none',
                        transition: 'transform 200ms ease',
                      }}
                    />
                  </span>
                </button>

                {/* Glassmorphic Dropdown Menu */}
                {isStatusDropdownOpen && (
                  <div
                    className="history-dropdown-menu animate-entrance"
                    style={{
                      position: 'absolute',
                      top: '44px',
                      left: 0,
                      zIndex: 9999,
                      width: '210px',
                      background: 'rgba(255, 255, 255, 0.98)',
                      backdropFilter: 'blur(16px)',
                      border: '1px solid rgba(229, 231, 235, 0.8)',
                      borderRadius: '16px',
                      padding: '6px',
                      boxShadow: '0 16px 36px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06)',
                    }}
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
              <div className="history-dropdown-wrapper" ref={dateDropdownRef}>
                <button
                  type="button"
                  className="history-dropdown-btn"
                  onClick={() => {
                    setIsDateDropdownOpen((prev) => !prev);
                    setIsStatusDropdownOpen(false);
                  }}
                  title={dateOptions.find((o) => o.value === dateFilter)?.label || 'All Time'}
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
                  <Calendar size={15} style={{ color: '#65597b', flexShrink: 0 }} />
                  <span className="history-btn-label">
                    {dateOptions.find((o) => o.value === dateFilter)?.label || 'All Time'}
                  </span>
                  <span className="history-btn-chevron">
                    <ChevronDown
                      size={14}
                      style={{
                        color: '#6b7280',
                        transform: isDateDropdownOpen ? 'rotate(180deg)' : 'none',
                        transition: 'transform 200ms ease',
                      }}
                    />
                  </span>
                </button>

                {/* Glassmorphic Dropdown Menu */}
                {isDateDropdownOpen && (
                  <div
                    className="history-dropdown-menu animate-entrance"
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
                    className="history-dropdown-menu animate-entrance"
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
                  >
                    <h3 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 14px 0', color: '#111827' }}>
                      Select Custom Time Window
                    </h3>

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
          </div>

          {/* Right Action Button */}
          <button
            className="history-export-btn"
            onClick={() => exportHistoryCSV(sessions)}
            title="Export session archives to CSV"
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
            <Download size={15} style={{ flexShrink: 0 }} />
            <span className="history-btn-label">Export CSV</span>
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
          {/* Desktop Table View (>= 769px) */}
          <div className="history-desktop-table" style={{ overflowX: 'auto' }}>
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
                          onClick={() => handleOpenAudioModal(session)}
                          title="Open turn-by-turn question & candidate audio player"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            background: '#f8f5fc',
                            border: '1px solid #ede6f8',
                            color: '#65597b',
                            fontSize: '12px',
                            fontWeight: '700',
                            padding: '6px 12px',
                            borderRadius: '9999px',
                            cursor: 'pointer',
                            transition: 'all 150ms ease',
                          }}
                          onMouseOver={(e) => {
                            e.currentTarget.style.background = '#65597b';
                            e.currentTarget.style.color = '#ffffff';
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.style.background = '#f8f5fc';
                            e.currentTarget.style.color = '#65597b';
                          }}
                        >
                          <Headphones size={14} />
                          <span>Listen Q&A</span>
                        </button>
                      </td>

                      {/* ACTIONS */}
                      <td className="history-actions-cell" style={{ padding: '18px 16px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
                          
                          {/* PRIMARY CONTEXTUAL RESUME / COMPLETE / REPORT BUTTON */}
                          {session.status === 'in_progress' && (
                            <button
                              onClick={() => handleContextualAction(session)}
                              title="Resume interview from current step"
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
                                boxShadow: '0 2px 8px rgba(101, 89, 123, 0.25)',
                              }}
                            >
                              <RotateCw size={13} />
                              <span>Resume Interview</span>
                            </button>
                          )}

                          {session.status === 'ready' && (
                            <button
                              onClick={() => handleContextualAction(session)}
                              title="Start practice interview"
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
                                boxShadow: '0 2px 8px rgba(101, 89, 123, 0.25)',
                              }}
                            >
                              <Play size={13} />
                              <span>Start Interview</span>
                            </button>
                          )}

                          {session.status === 'evaluating' && !session.has_report && (
                            <button
                              onClick={() => handleContextualAction(session)}
                              disabled={actionLoadingId === session.id}
                              title="Trigger AI multimodal evaluation to view report"
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '8px 16px',
                                borderRadius: '9999px',
                                background: '#d97706',
                                color: '#ffffff',
                                border: 'none',
                                fontSize: '12px',
                                fontWeight: '700',
                                cursor: 'pointer',
                                boxShadow: '0 2px 8px rgba(217, 119, 6, 0.25)',
                              }}
                            >
                              {actionLoadingId === session.id ? <Clock size={13} style={{ animation: 'spin 2s linear infinite' }} /> : <Sparkles size={13} />}
                              <span>Complete Evaluation</span>
                            </button>
                          )}

                          {(session.status === 'completed' || session.has_report) && (
                            <button
                              onClick={() => handleContextualAction(session)}
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
                              <FileText size={13} />
                              <span>View Report</span>
                            </button>
                          )}

                          {/* Secondary Inspect Details Button */}
                          <button
                            onClick={() => handleOpenInspectModal(session.id)}
                            title="Inspect generated question bank & resume profile analysis"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '8px 12px',
                              borderRadius: '9999px',
                              background: '#f3e8ff',
                              color: '#65597b',
                              border: '1px solid #e9d5ff',
                              fontSize: '12px',
                              fontWeight: '700',
                              cursor: 'pointer',
                            }}
                          >
                            <Eye size={13} />
                            <span>Details</span>
                          </button>

                          {/* Delete Session Button */}
                          <button
                            onClick={() => handleDeleteClick(session)}
                            title="Delete this practice session"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              width: '32px',
                              height: '32px',
                              borderRadius: '50%',
                              background: '#fff1f2',
                              color: '#e11d48',
                              border: '1px solid #ffe4e6',
                              cursor: 'pointer',
                              transition: 'all 150ms ease',
                            }}
                            onMouseOver={(e) => {
                              e.currentTarget.style.background = '#e11d48';
                              e.currentTarget.style.color = '#ffffff';
                            }}
                            onMouseOut={(e) => {
                              e.currentTarget.style.background = '#fff1f2';
                              e.currentTarget.style.color = '#e11d48';
                            }}
                          >
                            <Trash2 size={14} />
                          </button>
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

          {/* Mobile Card List View (< 769px) */}
          <div className="history-mobile-cards">
            {loading ? (
              <div style={{ padding: '30px 10px', textAlign: 'center', color: '#6b7280', fontSize: '13px' }}>
                Loading candidate session history archives...
              </div>
            ) : sessions.length > 0 ? (
              sessions.map((session, idx) => (
                <div key={session.id || idx} className="history-session-card">
                  {/* Top Row: Date & Status Badge */}
                  <div className="history-session-card-top">
                    <div className="history-session-date">
                      <Calendar size={13} style={{ color: '#65597b' }} />
                      <span>{session.date_text || 'Recent'}</span>
                    </div>
                    {renderStatusBadge(session.status)}
                  </div>

                  {/* Middle Row: Role Title, Company & Score */}
                  <div className="history-session-main">
                    <div className="history-session-info">
                      <h4 className="history-session-role">
                        {session.role_title}
                      </h4>
                      <div className="history-session-company">
                        {session.company}
                      </div>
                    </div>
                    {session.score !== null && session.score !== undefined && (
                      <div className="history-session-score-pill">
                        {session.score}/100
                      </div>
                    )}
                  </div>

                  {/* Bottom Actions Row */}
                  <div className="history-session-actions-row">
                    {/* Listen Q&A */}
                    <button
                      onClick={() => handleOpenAudioModal(session)}
                      title="Open turn-by-turn question & candidate audio player"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: '#f8f5fc',
                        border: '1px solid #ede6f8',
                        color: '#65597b',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      <Headphones size={12} />
                      <span>Listen</span>
                    </button>

                    {/* Contextual Action Button */}
                    {session.status === 'in_progress' && (
                      <button
                        onClick={() => handleContextualAction(session)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: '#65597b',
                          color: '#ffffff',
                          border: 'none',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        <RotateCw size={12} />
                        <span>Resume</span>
                      </button>
                    )}

                    {session.status === 'ready' && (
                      <button
                        onClick={() => handleContextualAction(session)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: '#65597b',
                          color: '#ffffff',
                          border: 'none',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        <Play size={12} />
                        <span>Start</span>
                      </button>
                    )}

                    {session.status === 'evaluating' && !session.has_report && (
                      <button
                        onClick={() => handleContextualAction(session)}
                        disabled={actionLoadingId === session.id}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: '#d97706',
                          color: '#ffffff',
                          border: 'none',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        <Sparkles size={12} />
                        <span>Evaluate</span>
                      </button>
                    )}

                    {(session.status === 'completed' || session.has_report) && (
                      <button
                        onClick={() => handleContextualAction(session)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: '#ede6f8',
                          color: '#65597b',
                          border: '1px solid #d8b4fe',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        <FileText size={12} />
                        <span>Report</span>
                      </button>
                    )}

                    {/* Details button */}
                    <button
                      onClick={() => handleOpenInspectModal(session.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        background: '#f3f4f6',
                        color: '#374151',
                        border: '1px solid #e5e7eb',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      <Eye size={12} />
                      <span>Details</span>
                    </button>

                    {/* Delete button */}
                    <button
                      className="action-delete-btn"
                      onClick={() => handleDeleteClick(session)}
                      title="Delete this session"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: '#fff1f2',
                        color: '#e11d48',
                        border: '1px solid #ffe4e6',
                        cursor: 'pointer',
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '30px 10px', textAlign: 'center' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#f3f4f6', color: '#65597b', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px auto' }}>
                  <Sparkles size={20} />
                </div>
                <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#111827', margin: '0 0 6px 0' }}>
                  No Session History Found
                </h4>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 12px 0' }}>
                  No practice sessions match your filter.
                </p>
                <button
                  onClick={() => navigate('/setup')}
                  style={{
                    padding: '8px 18px',
                    borderRadius: '9999px',
                    background: '#65597b',
                    color: '#ffffff',
                    border: 'none',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  Configure Practice Track
                </button>
              </div>
            )}
          </div>

          {/* PAGINATION / FOOTER INFO */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f3f4f6' }}>
            <span style={{ fontSize: '12px', color: '#9ca3af', fontWeight: '500' }}>
              Showing {sessions.length} session archives
            </span>
          </div>
        </Card>

        {/* DELETE SESSION CONFIRMATION MODAL */}
        {sessionToDelete && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(17, 24, 39, 0.5)',
              backdropFilter: 'blur(8px)',
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
                maxWidth: '460px',
                background: '#ffffff',
                borderRadius: '24px',
                padding: '28px 32px',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.2)',
                border: '1px solid rgba(229, 231, 235, 0.8)',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
              className="animate-entrance"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '44px', height: '44px', borderRadius: '14px', background: '#ffe4e6', color: '#e11d48', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <AlertTriangle size={22} />
                </div>
                <div>
                  <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#111827', margin: 0 }}>
                    Delete Practice Session?
                  </h3>
                  <span style={{ fontSize: '12px', color: '#6b7280' }}>
                    {sessionToDelete.role_title} • {sessionToDelete.company}
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '13px', color: '#4b5563', lineHeight: '1.5', margin: 0 }}>
                Are you sure you want to permanently delete this practice session? This will remove all generated questions, transcripts, audio recordings, and evaluation reports. This action cannot be undone.
              </p>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSessionToDelete(null)}
                  disabled={isDeletingSession}
                  style={{
                    padding: '9px 18px',
                    borderRadius: '9999px',
                    border: '1px solid #d1d5db',
                    background: '#ffffff',
                    color: '#374151',
                    fontSize: '13px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDeleteSession}
                  disabled={isDeletingSession}
                  style={{
                    padding: '9px 20px',
                    borderRadius: '9999px',
                    border: 'none',
                    background: '#e11d48',
                    color: '#ffffff',
                    fontSize: '13px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 2px 8px rgba(225, 29, 72, 0.3)',
                  }}
                >
                  {isDeletingSession ? <Clock size={14} style={{ animation: 'spin 2s linear infinite' }} /> : <Trash2 size={14} />}
                  <span>{isDeletingSession ? 'Deleting...' : 'Delete Session'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* DEEP-DIVE SESSION INSPECTION MODAL */}
        {inspectModalOpen && (
          <div
            className="history-modal-backdrop"
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
              className="history-inspect-modal animate-entrance"
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
            >
              {/* Modal Header */}
              <div
                className="history-inspect-header"
                style={{
                  padding: '20px 28px',
                  borderBottom: '1px solid #f3f4f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: '#fafafa',
                }}
              >
                <div style={{ flex: 1, minWidth: 0, paddingRight: '8px' }}>
                  <h3
                    className="history-inspect-title"
                    style={{ fontSize: '18px', fontWeight: '800', color: '#111827', margin: 0, wordBreak: 'break-word' }}
                  >
                    {inspectDetail?.role_title || 'Session Inspection'}
                  </h3>
                  <span
                    className="history-inspect-subtitle"
                    style={{ fontSize: '12px', color: '#6b7280', display: 'block', marginTop: '2px' }}
                  >
                    {inspectDetail?.company} • {inspectDetail?.seniority_level} Level
                  </span>
                </div>
                <button
                  className="history-modal-close-btn"
                  onClick={() => {
                    setInspectModalOpen(false);
                    setInspectDetail(null);
                  }}
                  style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}
                >
                  <X size={18} />
                </button>
              </div>

              {/* Modal Navigation Tabs */}
              <div
                className="history-inspect-tabs"
                style={{ display: 'flex', borderBottom: '1px solid #f3f4f6', background: '#ffffff', padding: '0 28px' }}
              >
                <button
                  className="history-inspect-tab-btn"
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
                  <HelpCircle size={15} style={{ flexShrink: 0 }} />
                  <span className="history-tab-desktop-text">Question Tree ({inspectDetail?.question_tree?.length || 0})</span>
                  <span className="history-tab-mobile-text">Questions ({inspectDetail?.question_tree?.length || 0})</span>
                </button>
                <button
                  className="history-inspect-tab-btn"
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
                  <UserCheck size={15} style={{ flexShrink: 0 }} />
                  <span className="history-tab-desktop-text">Resume & Profile Analysis</span>
                  <span className="history-tab-mobile-text">Resume Analysis</span>
                </button>
              </div>

              {/* Modal Body Content */}
              <div
                className="history-inspect-body"
                style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}
              >
                {inspectLoading ? (
                  <p style={{ textAlign: 'center', color: '#6b7280', padding: '32px' }}>Loading inspection data...</p>
                ) : inspectTab === 'questions' ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {inspectDetail?.question_tree?.length > 0 ? (
                      inspectDetail.question_tree.map((q, qIdx) => (
                        <div
                          key={qIdx}
                          className="history-inspect-qcard"
                          style={{
                            padding: '16px',
                            borderRadius: '16px',
                            background: '#f9fafb',
                            border: '1px solid #f3f4f6',
                          }}
                        >
                          <div
                            className="history-inspect-qhead"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}
                          >
                            <span
                              className="history-inspect-qtopic"
                              style={{ fontSize: '11px', fontWeight: '800', color: '#65597b', textTransform: 'uppercase', letterSpacing: '0.05em' }}
                            >
                              Q{qIdx + 1} • {q.topic || 'Domain Question'}
                            </span>
                            {q.difficulty && (
                              <span
                                className="history-inspect-qdiff"
                                style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b', flexShrink: 0 }}
                              >
                                {q.difficulty}
                              </span>
                            )}
                          </div>
                          <p
                            className="history-inspect-qtext"
                            style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: '0 0 8px 0', lineHeight: '1.4' }}
                          >
                            {q.question_text || q.text}
                          </p>
                          {q.expected_keywords && (
                            <div
                              className="history-inspect-qkeywords"
                              style={{ fontSize: '12px', color: '#6b7280' }}
                            >
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
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        <div style={{ background: '#f5f0fb', padding: '14px', borderRadius: '14px', border: '1px solid #e9d5ff' }}>
                          <h4 style={{ fontSize: '13.5px', fontWeight: '800', color: '#65597b', margin: '0 0 4px 0' }}>
                            Candidate Profile Match
                          </h4>
                          <p style={{ fontSize: '12.5px', color: '#4b5563', margin: 0, lineHeight: '1.45' }}>
                            {inspectDetail.resume_analysis.summary || inspectDetail.resume_analysis.overview || 'Profile analyzed against target job description requirements.'}
                          </p>
                        </div>
                        {inspectDetail.resume_analysis.skills_overlap && (
                          <div>
                            <strong style={{ fontSize: '12.5px', color: '#111827', display: 'block', marginBottom: '6px' }}>Skill Overlap Highlights:</strong>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                              {(inspectDetail.resume_analysis.skills_overlap || []).map((s, idx) => (
                                <span key={idx} style={{ fontSize: '11px', padding: '3px 8px', background: '#dcfce7', color: '#15803d', borderRadius: '9999px', fontWeight: '600' }}>
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

        {/* TURN-BY-TURN QUESTION & ANSWER INTERACTIVE AUDIO PLAYER MODAL */}
        {audioModalOpen && audioModalSession && (
          <div
            className="history-modal-backdrop"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              width: '100vw',
              height: '100vh',
              background: 'rgba(17, 24, 39, 0.5)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 99999,
              padding: '20px',
            }}
          >
            <div
              className="history-audio-modal animate-entrance"
              style={{
                width: '100%',
                maxWidth: '820px',
                height: '88vh',
                background: '#ffffff',
                borderRadius: '24px',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.22)',
                border: '1px solid rgba(229, 231, 235, 0.9)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {/* Hidden HTML5 Audio Element */}
              <audio
                ref={audioRef}
                src={`/api/v1/voice/recording/${audioModalSession.id}${
                  localStorage.getItem('netran_token') || localStorage.getItem('token')
                    ? `?token=${encodeURIComponent(localStorage.getItem('netran_token') || localStorage.getItem('token'))}`
                    : ''
                }`}
                preload="auto"
                onTimeUpdate={handleAudioTimeUpdate}
                onLoadedMetadata={(e) => {
                  const dur = e.currentTarget.duration;
                  if (dur && !isNaN(dur) && isFinite(dur)) setDuration(dur);
                }}
                onDurationChange={(e) => {
                  const dur = e.currentTarget.duration;
                  if (dur && !isNaN(dur) && isFinite(dur)) setDuration(dur);
                }}
                onCanPlay={(e) => {
                  const dur = e.currentTarget.duration;
                  if (dur && !isNaN(dur) && isFinite(dur)) setDuration(dur);
                }}
                onEnded={() => setIsPlayingAudio(false)}
                onError={(e) => {
                  console.warn('History audio load error:', e);
                  setIsPlayingAudio(false);
                }}
              />

              {/* Modal Top Header */}
              <div
                className="history-audio-header"
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid #f3f4f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: '#faf9fc',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
                  <div
                    className="history-audio-icon-box"
                    style={{ width: '40px', height: '40px', borderRadius: '12px', background: '#ede6f8', color: '#65597b', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}
                  >
                    <Headphones size={20} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3
                      className="history-audio-title"
                      style={{ fontSize: '15.5px', fontWeight: '800', color: '#111827', margin: 0, wordBreak: 'break-word' }}
                    >
                      {audioModalSession.role_title}
                    </h3>
                    <span
                      className="history-audio-subtitle"
                      style={{ fontSize: '11.5px', color: '#6b7280', display: 'inline-flex', alignItems: 'center', gap: '5px', marginTop: '1px' }}
                    >
                      <span>{audioModalSession.company}</span>
                      <span>•</span>
                      <Radio size={11} style={{ color: isPlayingAudio ? '#22c55e' : '#9ca3af' }} />
                      <span>{isPlayingAudio ? `Turn ${activeTurnIndex + 1}` : 'Paused'}</span>
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  {/* Continuous Play Toggle */}
                  <button
                    className="history-audio-autoadvance-btn"
                    onClick={() => setIsContinuousPlay((prev) => !prev)}
                    title="Toggle auto-play to next turn when current answer finishes"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '6px 12px',
                      borderRadius: '9999px',
                      border: isContinuousPlay ? '1px solid #65597b' : '1px solid #d1d5db',
                      background: isContinuousPlay ? '#ede6f8' : '#ffffff',
                      color: isContinuousPlay ? '#65597b' : '#6b7280',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      transition: 'all 150ms ease',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <RefreshCw size={12} />
                    <span className="history-tab-desktop-text">Auto-Advance Q&A</span>
                    <span className="history-tab-mobile-text">Auto-Play</span>
                  </button>

                  {/* Close Modal Button */}
                  <button
                    className="history-modal-close-btn"
                    onClick={handleCloseAudioModal}
                    style={{
                      background: '#f3f4f6',
                      border: 'none',
                      borderRadius: '50%',
                      width: '30px',
                      height: '30px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#6b7280',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  >
                    <X size={17} />
                  </button>
                </div>
              </div>

              {/* Modal Body: Turn-by-Turn Q&A List */}
              <div
                className="history-audio-body"
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                  background: '#fcfbfe',
                }}
              >
                {audioModalLoading ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                    <Clock size={24} style={{ animation: 'spin 2s linear infinite', margin: '0 auto 8px auto', display: 'block', color: '#65597b' }} />
                    <p style={{ fontSize: '14px', fontWeight: '600' }}>Loading question & answer timeline...</p>
                  </div>
                ) : getActiveTurnsList().length > 0 ? (
                  getActiveTurnsList().map((turn, tIdx) => {
                    const isActive = activeTurnIndex === tIdx;
                    const turnDuration = turn.audio_end_sec && turn.audio_start_sec !== undefined
                      ? Math.max(0, turn.audio_end_sec - turn.audio_start_sec)
                      : 0;

                    return (
                      <div
                        key={turn.turn_id || tIdx}
                        ref={(el) => (turnCardRefs.current[tIdx] = el)}
                        className="history-audio-turn-card"
                        style={{
                          borderRadius: '16px',
                          background: isActive ? '#ffffff' : '#fafafa',
                          border: isActive ? '2px solid #65597b' : '1px solid #ede8f5',
                          padding: '16px 18px',
                          boxShadow: isActive ? '0 8px 24px rgba(101, 89, 123, 0.1)' : 'none',
                          transition: 'all 200ms ease',
                          position: 'relative',
                        }}
                      >
                        {/* Turn Header Bar */}
                        <div
                          className="history-audio-turn-head"
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', flex: 1 }}>
                            <span style={{ fontSize: '11px', fontWeight: '800', background: isActive ? '#65597b' : '#e5e7eb', color: isActive ? '#ffffff' : '#374151', padding: '2.5px 8px', borderRadius: '9999px', textTransform: 'uppercase' }}>
                              Turn {tIdx + 1}
                            </span>
                            <span style={{ fontSize: '12.5px', fontWeight: '700', color: '#374151' }}>
                              {turn.topic || 'Domain Question'}
                            </span>
                            {turn.difficulty && (
                              <span style={{ fontSize: '10.5px', fontWeight: '600', padding: '1.5px 7px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b' }}>
                                {turn.difficulty}
                              </span>
                            )}
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                            {turnDuration > 0 && (
                              <span style={{ fontSize: '11.5px', fontWeight: '600', color: '#6b7280', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                                <Clock size={11} />
                                {formatTime(turnDuration)}
                              </span>
                            )}

                            {/* Play this specific turn button */}
                            <button
                              className="history-audio-turn-play-btn"
                              onClick={() => {
                                if (isActive && isPlayingAudio) {
                                  audioRef.current?.pause();
                                  setIsPlayingAudio(false);
                                } else {
                                  playTurn(tIdx);
                                }
                              }}
                              title={isActive && isPlayingAudio ? 'Pause Turn' : 'Play Turn'}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                                padding: '5px 11px',
                                borderRadius: '9999px',
                                border: 'none',
                                background: isActive && isPlayingAudio ? '#65597b' : '#ede6f8',
                                color: isActive && isPlayingAudio ? '#ffffff' : '#65597b',
                                fontSize: '11.5px',
                                fontWeight: '700',
                                cursor: 'pointer',
                                transition: 'all 150ms ease',
                              }}
                            >
                              {isActive && isPlayingAudio ? <Pause size={12} /> : <Play size={12} style={{ marginLeft: '1px' }} />}
                              <span className="history-tab-desktop-text">{isActive && isPlayingAudio ? 'Pause' : 'Play'}</span>
                            </button>
                          </div>
                        </div>

                        {/* EVA'S QUESTION CARD */}
                        <div style={{ background: '#f5f0fb', borderRadius: '12px', padding: '10px 12px', marginBottom: '10px', borderLeft: '3px solid #65597b' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '3px' }}>
                            <Sparkles size={12} style={{ color: '#65597b' }} />
                            <span style={{ fontSize: '10.5px', fontWeight: '800', color: '#65597b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Eva Question:
                            </span>
                          </div>
                          <p style={{ fontSize: '13px', fontWeight: '700', color: '#111827', margin: 0, lineHeight: '1.35' }}>
                            {turn.question_text || '(Question text unavailable)'}
                          </p>
                        </div>

                        {/* CANDIDATE'S SPOKEN RESPONSE */}
                        <div style={{ background: '#ffffff', borderRadius: '12px', padding: '10px 12px', border: '1px solid #f0edf5' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                              <Mic size={12} style={{ color: '#0369a1' }} />
                              <span style={{ fontSize: '10.5px', fontWeight: '800', color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                                Candidate Response:
                              </span>
                            </div>
                            {turn.audio_start_sec !== undefined && turn.audio_end_sec !== undefined && (
                              <span style={{ fontSize: '10.5px', color: '#9ca3af' }}>
                                [{formatTime(turn.audio_start_sec)} → {formatTime(turn.audio_end_sec)}]
                              </span>
                            )}
                          </div>
                          <p style={{ fontSize: '12.5px', color: '#374151', margin: 0, lineHeight: '1.45', fontStyle: turn.candidate_transcript?.startsWith('(') ? 'italic' : 'normal' }}>
                            {turn.candidate_transcript || '(No transcript recorded for this turn)'}
                          </p>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                    <p style={{ fontSize: '14px' }}>No turn audio records found for this session.</p>
                  </div>
                )}
              </div>

              {/* Modal Bottom Sticky Master Controls Bar */}
              <div
                className="history-audio-dock"
                style={{
                  padding: '14px 20px 16px 20px',
                  background: 'linear-gradient(180deg, #322b3f 0%, #252030 100%)',
                  borderTop: '1px solid rgba(230, 214, 255, 0.16)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  boxShadow: '0 -6px 22px rgba(50, 43, 63, 0.16)',
                }}
              >
                {/* Scrubbing Bar & Time */}
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
                      accentColor: '#d6c7ee',
                      cursor: 'pointer',
                      height: '4px',
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: '700', marginTop: '4px' }}>
                    <span style={{ color: '#f3e8ff' }}>{formatTime(currentTime)}</span>
                    <span style={{ color: '#cfc0e8', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Headphones size={11} style={{ color: '#e6d6ff' }} />
                      <span>{formatTime(duration)}</span>
                    </span>
                  </div>
                </div>

                {/* Controls Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                  {/* Volume Control */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button
                      onClick={() => {
                        if (audioRef.current) {
                          audioRef.current.muted = !isMuted;
                          setIsMuted(!isMuted);
                        }
                      }}
                      style={{ background: 'transparent', border: 'none', color: '#e6d6ff', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
                      title={isMuted ? 'Unmute' : 'Mute'}
                    >
                      {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      className="history-audio-volume-slider"
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
                      style={{ width: '56px', accentColor: '#d6c7ee', cursor: 'pointer' }}
                    />
                  </div>

                  {/* Center Playback Steppers */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {/* Previous Turn */}
                    <button
                      className="history-audio-nav-btn"
                      onClick={handlePrevTurn}
                      disabled={activeTurnIndex === 0}
                      title="Previous Question"
                      style={{
                        padding: '5px 11px',
                        borderRadius: '9999px',
                        background: 'rgba(230, 214, 255, 0.12)',
                        border: '1px solid rgba(230, 214, 255, 0.18)',
                        color: activeTurnIndex === 0 ? 'rgba(230, 214, 255, 0.35)' : '#ffffff',
                        fontSize: '11.5px',
                        fontWeight: '700',
                        cursor: activeTurnIndex === 0 ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px',
                        transition: 'all 150ms ease',
                      }}
                    >
                      <ChevronLeft size={14} />
                      <span className="history-tab-desktop-text">Prev</span>
                    </button>

                    {/* Master Play/Pause Button */}
                    <button
                      className="history-audio-playbtn"
                      onClick={toggleMasterPlayPause}
                      style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #65597b 0%, #4d4162 100%)',
                        color: '#ffffff',
                        border: '1px solid rgba(230, 214, 255, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 4px 14px rgba(101, 89, 123, 0.35)',
                        transition: 'transform 150ms ease',
                      }}
                      title={isPlayingAudio ? 'Pause Master Audio' : 'Play Master Audio'}
                    >
                      {isPlayingAudio ? <Pause size={17} fill="#ffffff" /> : <Play size={17} fill="#ffffff" style={{ marginLeft: '2px' }} />}
                    </button>

                    {/* Next Turn */}
                    <button
                      className="history-audio-nav-btn"
                      onClick={handleNextTurn}
                      disabled={activeTurnIndex >= getActiveTurnsList().length - 1}
                      title="Next Question"
                      style={{
                        padding: '5px 11px',
                        borderRadius: '9999px',
                        background: 'rgba(230, 214, 255, 0.12)',
                        border: '1px solid rgba(230, 214, 255, 0.18)',
                        color: activeTurnIndex >= getActiveTurnsList().length - 1 ? 'rgba(230, 214, 255, 0.35)' : '#ffffff',
                        fontSize: '11.5px',
                        fontWeight: '700',
                        cursor: activeTurnIndex >= getActiveTurnsList().length - 1 ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px',
                        transition: 'all 150ms ease',
                      }}
                    >
                      <span className="history-tab-desktop-text">Next</span>
                      <ChevronRight size={14} />
                    </button>
                  </div>

                  {/* Playback Speed Toggles */}
                  <div
                    className="history-audio-speed-group"
                    style={{ display: 'flex', alignItems: 'center', gap: '2px', background: 'rgba(0, 0, 0, 0.18)', padding: '2px', borderRadius: '8px', border: '1px solid rgba(230, 214, 255, 0.12)' }}
                  >
                    {[1.0, 1.25, 1.5, 2.0].map((rate) => (
                      <button
                        key={rate}
                        className="history-audio-speed-btn"
                        onClick={() => {
                          setPlaybackRate(rate);
                          if (audioRef.current) audioRef.current.playbackRate = rate;
                        }}
                        style={{
                          padding: '2.5px 6px',
                          borderRadius: '6px',
                          border: 'none',
                          fontSize: '10.5px',
                          fontWeight: '800',
                          background: playbackRate === rate ? '#65597b' : 'transparent',
                          color: playbackRate === rate ? '#ffffff' : '#cfc0e8',
                          cursor: 'pointer',
                          transition: 'all 150ms ease',
                        }}
                      >
                        {rate}x
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </PageWrapper>
    </div>
  );
};

export default History;
