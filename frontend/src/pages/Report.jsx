import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  RotateCcw,
  RotateCw,
  BarChart2,
  Share2,
  Calendar,
  Clock,
  User,
  Lightbulb,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Mic,
  Award,
  Sparkles,
  BookOpen,
  ShieldAlert,
  FileText,
  Cpu,
  TrendingUp,
  Printer,
  Download,
  Check,
  ArrowRight,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Headphones,
  SlidersHorizontal,
} from 'lucide-react';
import Card from '../components/ui/Card';
import PageWrapper from '../components/layout/PageWrapper';
import useReports from '../hooks/useReports';
import useAuth from '../hooks/useAuth';

export const Report = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const { report, status, progressMessage, isLoading, error } = useReports(sessionId);
  const { user } = useAuth();
  const userInitial = user?.display_name
    ? user.display_name.charAt(0).toUpperCase()
    : user?.email
    ? user.email.charAt(0).toUpperCase()
    : 'C';

  const [isCopied, setIsCopied] = useState(false);

  // Accordion state for turn breakdown
  const [expandedQuestions, setExpandedQuestions] = useState({});

  // Turn Audio playback state
  const [playingTurnId, setPlayingTurnId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [audioError, setAudioError] = useState(null);
  const audioRef = useRef(null);

  // Initialize first turn open when report loads
  useEffect(() => {
    if (report && report.turn_evaluations && report.turn_evaluations.length > 0) {
      setExpandedQuestions({ 0: true });
    }
  }, [report]);

  // High-frequency 60fps playhead updater while audio is actively playing
  useEffect(() => {
    let animId;
    if (isPlaying) {
      const step = () => {
        if (audioRef.current && !audioRef.current.paused) {
          setAudioCurrentTime(audioRef.current.currentTime || 0);
          const dur = audioRef.current.duration;
          if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
            setAudioDuration(dur);
          }
          animId = requestAnimationFrame(step);
        }
      };
      animId = requestAnimationFrame(step);
    }
    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [isPlaying]);

  const handleToggleTurnAudio = (turnId, startSec, endSec) => {
    const token = localStorage.getItem('netran_token') || localStorage.getItem('token');
    const audioEl = audioRef.current;
    if (!audioEl) return;

    if (playingTurnId === turnId) {
      if (isPlaying) {
        audioEl.pause();
        setIsPlaying(false);
      } else {
        audioEl
          .play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.error('Audio play error:', err);
            setIsPlaying(false);
          });
      }
      return;
    }

    // Calculate initial estimated duration from turn metadata
    const expectedDur = (endSec && startSec && endSec > startSec) ? (endSec - startSec) : 0;
    setPlayingTurnId(turnId);
    setAudioCurrentTime(0);
    setAudioDuration(expectedDur);
    setAudioError(null);

    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';
    const turnAudioUrl = `/api/v1/voice/recording/${sessionId}/turn/${turnId}${tokenQuery}`;

    audioEl.src = turnAudioUrl;
    audioEl.playbackRate = playbackRate;
    audioEl.currentTime = 0;
    audioEl.load();
    audioEl
      .play()
      .then(() => {
        setIsPlaying(true);
      })
      .catch((err) => {
        console.warn('Turn clip fallback to continuous stream:', err);
        if (startSec !== undefined && startSec !== null) {
          const fullAudioUrl = `/api/v1/voice/recording/${sessionId}${tokenQuery}`;
          audioEl.src = fullAudioUrl;
          audioEl.currentTime = startSec || 0;
          audioEl
            .play()
            .then(() => setIsPlaying(true))
            .catch((e) => {
              console.error('Full stream error:', e);
              setIsPlaying(false);
            });
        } else {
          setIsPlaying(false);
        }
      });
  };

  const handleSeekTurnAudio = (e) => {
    const newTime = parseFloat(e.target.value);
    setAudioCurrentTime(newTime);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
  };

  const handleJumpTurnAudio = (delta) => {
    if (audioRef.current) {
      const targetTime = Math.max(
        0,
        Math.min(audioDuration || 9999, (audioRef.current.currentTime || 0) + delta)
      );
      audioRef.current.currentTime = targetTime;
      setAudioCurrentTime(targetTime);
    }
  };

  const handleCyclePlaybackRate = () => {
    const rates = [1.0, 1.25, 1.5, 2.0];
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const nextRate = rates[nextIdx];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleQuestion = (index) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleShare = async () => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(window.location.href);
      } else {
        const textArea = document.createElement('textarea');
        textArea.value = window.location.href;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleListenAllAudio = () => {
    if (report && report.turn_evaluations && report.turn_evaluations.length > 0) {
      const allOpen = {};
      report.turn_evaluations.forEach((_, idx) => {
        allOpen[idx] = true;
      });
      setExpandedQuestions(allOpen);

      const firstTurn = report.turn_evaluations[0];
      handleToggleTurnAudio(firstTurn.turn_id, firstTurn.audio_start_sec, firstTurn.audio_end_sec);
    }
  };

  // Helper for color styling hiring signal badge
  const getHiringSignalStyle = (signal) => {
    switch (signal?.toLowerCase()) {
      case 'strong hire':
        return { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' };
      case 'hire':
        return { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' };
      case 'lean no hire':
        return { bg: '#fef3c7', text: '#b45309', border: '#fde68a' };
      case 'no hire':
        return { bg: '#fee2e2', text: '#b91c1c', border: '#fca5a5' };
      default:
        return { bg: '#f3e8ff', text: '#6b21a8', border: '#e9d5ff' };
    }
  };

  // Helper for formatting ISO date
  const formatDate = (isoString) => {
    if (!isoString) return new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    try {
      return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return isoString;
    }
  };

  // Loading Skeleton View
  if (isLoading || status === 'evaluating') {
    return (
      <div style={{ background: '#f8f9fa', minHeight: '100vh', padding: '60px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-family, system-ui)' }}>
        <Card style={{ padding: '40px', maxWidth: '520px', width: '100%', textAlign: 'center', background: '#ffffff', borderRadius: '24px', boxShadow: '0 12px 36px rgba(0,0,0,0.04)' }}>
          <Cpu size={44} style={{ color: '#65597b', marginBottom: '20px' }} className="animate-spin" />
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#111827', marginBottom: '10px' }}>
            Preparing Evaluation Scorecard...
          </h2>
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px', lineHeight: '1.6' }}>
            {progressMessage || 'Gemini multimodal evaluation engine is processing candidate audio telemetry and performance metrics.'}
          </p>
          <button
            onClick={() => navigate(`/processing/${sessionId}`)}
            style={{
              padding: '11px 22px',
              borderRadius: '9999px',
              background: '#65597b',
              color: '#ffffff',
              border: 'none',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            View Live Processing Progress
          </button>
        </Card>
      </div>
    );
  }

  // Error State View
  if (error || !report) {
    return (
      <div style={{ background: '#f8f9fa', minHeight: '100vh', padding: '60px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <Card style={{ padding: '40px', maxWidth: '520px', width: '100%', textAlign: 'center', background: '#ffffff', borderRadius: '24px' }}>
          <AlertTriangle size={44} style={{ color: '#dc2626', marginBottom: '20px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#111827', marginBottom: '10px' }}>
            Report Not Found or Processing
          </h2>
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '24px' }}>
            {error || 'No evaluation report artifact could be located for this session yet.'}
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button
              onClick={() => navigate(`/processing/${sessionId}`)}
              style={{ padding: '10px 20px', borderRadius: '9999px', background: '#65597b', color: '#ffffff', border: 'none', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}
            >
              Check Processing Status
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              style={{ padding: '10px 20px', borderRadius: '9999px', background: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb', fontWeight: '600', fontSize: '13px', cursor: 'pointer' }}
            >
              Go to Dashboard
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Destructure real report fields from CandidateReportPayload
  const {
    overall_hiring_signal = 'Hire',
    overall_technical_score = 80,
    overall_vocal_confidence_score = 85,
    technical_pillars = [],
    behavioral_flags = [],
    candidate_feedback = {},
    turn_evaluations = [],
    executive_summary = 'Candidate demonstrated solid technical understanding across system architecture concepts.',
    generated_at,
  } = report;

  const signalStyle = getHiringSignalStyle(overall_hiring_signal);
  const totalFillerWords = turn_evaluations.reduce((acc, t) => acc + (t.filler_word_count || 0), 0);

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: '40px', fontFamily: 'var(--font-family, system-ui)' }}>
      {/* Scoped CSS for Phone & Responsive Viewports */}
      <style>{`
        .report-page-wrapper {
          padding: 24px 32px 48px 32px !important;
          max-width: 1100px;
          margin: 0 auto;
        }
        .report-hero-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
          gap: 16px;
        }
        .report-feedback-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 16px;
        }
        .report-assessment-layout {
          display: grid;
          grid-template-columns: 130px 1fr;
          gap: 18px;
          align-items: center;
        }
        .report-q-body-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 18px;
        }
        .report-flag-item {
          background: #ffffff;
          padding: 12px 16px;
          border-radius: 12px;
          border: 1px solid #ffe4e6;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .report-flag-content {
          display: flex;
          align-items: center;
          gap: 10px;
          flex: 1;
        }
        .report-q-header {
          padding: 16px 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          cursor: pointer;
          user-select: none;
          gap: 14px;
        }
        .report-q-left {
          display: flex;
          align-items: center;
          gap: 14px;
          flex: 1;
        }
        .report-audio-widget {
          margin-top: 16px;
          border-radius: 16px;
          padding: 14px 18px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 14px;
        }
        .report-next-steps-card {
          padding: 24px 32px;
          border-radius: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 18px;
        }

        /* Mobile Adjustments (<= 640px) */
        @media (max-width: 640px) {
          .report-page-wrapper {
            padding: 12px 14px 48px 14px !important;
            gap: 12px !important;
          }
          .report-top-bar {
            margin-bottom: 2px !important;
          }
          .report-back-btn {
            padding: 7px 14px !important;
            font-size: 12.5px !important;
          }
          .report-back-btn-subtext {
            display: none !important;
          }
          .report-banner-card {
            padding: 12px 13px 12px 13px !important;
            border-radius: 14px !important;
          }
          .report-banner-title {
            font-size: 16px !important;
            line-height: 1.25 !important;
          }
          .report-banner-icon {
            width: 19px !important;
            height: 19px !important;
          }
          .report-banner-meta {
            gap: 5px !important;
            font-size: 11px !important;
            margin-top: 6px !important;
          }
          .report-meta-bullet {
            display: none !important;
          }
          .report-banner-meta > div {
            background: #f9fafb;
            padding: 2.5px 7px !important;
            border-radius: 6px;
            border: 1px solid #f3f4f6;
            font-size: 11px !important;
            gap: 4px !important;
          }
          .report-banner-meta svg {
            width: 12px !important;
            height: 12px !important;
          }
          .report-banner-actions {
            width: 100% !important;
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 6px !important;
            margin-top: 8px !important;
          }
          .report-banner-actions button {
            width: 100% !important;
            justify-content: center !important;
            padding: 6px 8px !important;
            font-size: 11.5px !important;
            height: 33px !important;
            border-radius: 9999px !important;
            gap: 5px !important;
          }
          .report-banner-actions button svg {
            width: 13px !important;
            height: 13px !important;
          }
          .report-hero-grid {
            grid-template-columns: 1fr !important;
            gap: 10px !important;
          }
          .report-hero-card {
            padding: 13px 14px 13px 14px !important;
            border-radius: 14px !important;
          }
          .report-hero-card-header {
            margin-bottom: 10px !important;
          }
          .report-hero-card-title {
            font-size: 14.5px !important;
          }
          .report-hero-card-title svg {
            width: 16px !important;
            height: 16px !important;
          }
          .report-hero-signal-badge {
            padding: 2px 8px !important;
            font-size: 11px !important;
          }
          .report-assessment-layout {
            grid-template-columns: 88px 1fr !important;
            gap: 10px !important;
          }
          .report-donut-wrapper {
            width: 84px !important;
            height: 84px !important;
          }
          .report-donut-svg {
            width: 84px !important;
            height: 84px !important;
          }
          .report-donut-score {
            font-size: 21px !important;
          }
          .report-donut-denom {
            font-size: 9.5px !important;
          }
          .report-donut-label {
            font-size: 10px !important;
            margin-top: 3px !important;
          }
          .report-telemetry-container {
            gap: 6px !important;
          }
          .report-telemetry-card {
            padding: 6px 9px !important;
            border-radius: 9px !important;
          }
          .report-telemetry-label {
            font-size: 11px !important;
            gap: 5px !important;
          }
          .report-telemetry-label svg {
            width: 12px !important;
            height: 12px !important;
          }
          .report-telemetry-val {
            font-size: 11.5px !important;
          }
          .report-telemetry-bar {
            height: 3.5px !important;
          }
          .report-filler-badge {
            font-size: 10.5px !important;
            padding: 1.5px 6px !important;
          }
          .report-flag-item {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 8px !important;
            padding: 12px 14px !important;
          }
          .report-flag-content {
            width: 100% !important;
            align-items: flex-start !important;
            flex-direction: column !important;
            gap: 6px !important;
          }
          .report-flag-turn {
            align-self: flex-end !important;
            margin-left: 0 !important;
            margin-top: -22px !important;
          }
          .report-feedback-grid {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
          }
          .report-q-header {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 10px !important;
            padding: 14px 14px !important;
          }
          .report-q-left {
            width: 100% !important;
            align-items: flex-start !important;
            gap: 10px !important;
          }
          .report-q-right {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding-top: 8px !important;
            border-top: 1px dashed #f3f4f6 !important;
          }
          .report-q-badges {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
          }
          .report-q-badges span {
            font-size: 11px !important;
            padding: 3px 8px !important;
          }
          .report-q-body {
            padding: 14px 12px !important;
          }
          .report-q-body-grid {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
          }
          .report-audio-widget {
            flex-direction: column !important;
            align-items: stretch !important;
            padding: 12px 12px !important;
            gap: 12px !important;
          }
          .report-audio-main-row {
            width: 100% !important;
          }
          .report-audio-scrubber-row {
            width: 100% !important;
            min-width: 0 !important;
          }
          .report-audio-controls-row {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 6px !important;
          }
          .report-next-steps-card {
            padding: 18px 16px !important;
            border-radius: 16px !important;
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 14px !important;
          }
          .report-next-steps-buttons {
            width: 100% !important;
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
          }
          .report-next-steps-buttons button {
            flex: 1 1 calc(50% - 4px) !important;
            justify-content: center !important;
            padding: 9px 12px !important;
            font-size: 12.5px !important;
          }
          .report-next-steps-buttons button.start-new-btn {
            flex: 1 1 100% !important;
          }
        }
      `}</style>

      {/* Global Audio Element for Turn-by-Turn Playback */}
      <audio
        ref={audioRef}
        preload="auto"
        onTimeUpdate={(e) => {
          setAudioCurrentTime(e.currentTarget.currentTime || 0);
        }}
        onLoadedMetadata={(e) => {
          const dur = e.currentTarget.duration;
          if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
            setAudioDuration(dur);
          }
        }}
        onDurationChange={(e) => {
          const dur = e.currentTarget.duration;
          if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
            setAudioDuration(dur);
          }
        }}
        onCanPlay={(e) => {
          const dur = e.currentTarget.duration;
          if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
            setAudioDuration(dur);
          }
        }}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          setAudioCurrentTime(0);
        }}
        onError={(e) => {
          console.warn('Audio playback error event:', e);
          setAudioError('Audio recording stream currently unavailable for this turn.');
          setIsPlaying(false);
        }}
        style={{ display: 'none' }}
      />

      {/* Main Page Container with comfortable top margin and balanced padding */}
      <PageWrapper className="report-page-wrapper" style={{ gap: '16px' }}>
        {/* TOP-LEFT BACK BUTTON & CANDIDATE PROFILE BAR */}
        <div
          className="report-top-bar no-print"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '4px',
          }}
        >
          {/* Back to Dashboard Button with Netran AI Branding */}
          <button
            onClick={() => navigate('/dashboard')}
            className="report-back-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              background: '#ffffff',
              border: '1px solid #e5e7eb',
              padding: '9px 18px',
              borderRadius: '9999px',
              color: '#374151',
              fontSize: '13.5px',
              fontWeight: '700',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              transition: 'all 0.2s ease',
            }}
          >
            <ArrowLeft size={16} style={{ color: '#65597b' }} />
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#65597b' }}>
              <Sparkles size={15} />
              <span>Netran AI</span>
            </span>
            <span className="report-back-btn-subtext" style={{ color: '#d1d5db' }}>|</span>
            <span className="report-back-btn-subtext" style={{ color: '#4b5563' }}>Back to Dashboard</span>
          </button>

          {/* Candidate Profile Avatar Badge */}
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '50%',
              background: '#f3e8ff',
              color: '#65597b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '800',
              fontSize: '14px',
              boxShadow: '0 2px 8px rgba(101, 89, 123, 0.12)',
              border: '1px solid #e9d8fd',
            }}
            title={user?.email || 'Candidate Profile'}
          >
            {userInitial}
          </div>
        </div>

        {/* PRINT-ONLY HEADER BANNER */}
        <div className="print-only-header" style={{ display: 'none', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '2px solid #65597b', paddingBottom: '14px' }}>
            <div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: '#65597b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={22} />
                <span>Netran AI Candidate Evaluation Scorecard</span>
              </div>
              <p style={{ fontSize: '13px', color: '#4b5563', margin: '4px 0 0 0' }}>
                Autonomous Technical Interview Evaluation & Multimodal Audio Telemetry
              </p>
            </div>
            <div style={{ textAlign: 'right', fontSize: '13px', color: '#4b5563', lineHeight: '1.5' }}>
              <div>Session ID: <strong style={{ color: '#111827' }}>{sessionId}</strong></div>
              <div>Date: {formatDate(generated_at)}</div>
              <div>Hiring Signal: <strong style={{ color: signalStyle.text }}>{overall_hiring_signal}</strong></div>
            </div>
          </div>
        </div>

        {/* SESSION SUMMARY BANNER CARD */}
        <Card
          style={{
            padding: '22px 28px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
            boxShadow: '0 4px 18px rgba(0, 0, 0, 0.02)',
          }}
          className="report-banner-card animate-entrance print-break-inside-avoid"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '18px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1
                  className="report-banner-title"
                  style={{
                    fontSize: '24px',
                    fontWeight: '800',
                    color: '#111827',
                    letterSpacing: '-0.02em',
                    margin: 0,
                  }}
                >
                  Multimodal Evaluation Scorecard
                </h1>
                <Award className="report-banner-icon" size={24} style={{ color: '#65597b', flexShrink: 0 }} />
              </div>

              {/* Session Meta Information */}
              <div
                className="report-banner-meta"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  marginTop: '8px',
                  color: '#6b7280',
                  fontSize: '13.5px',
                  fontWeight: '500',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <User size={15} />
                  <span>Interviewed by Eva (AI)</span>
                </div>
                <span className="report-meta-bullet">•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={15} />
                  <span>Completed {formatDate(generated_at)}</span>
                </div>
                <span className="report-meta-bullet">•</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={15} />
                  <span>Turns Evaluated: {turn_evaluations.length}</span>
                </div>
              </div>
            </div>

            {/* Banner Action Buttons */}
            <div className="report-banner-actions no-print" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <button
                onClick={handleListenAllAudio}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '9px 18px',
                  borderRadius: '9999px',
                  background: '#f3e8ff',
                  color: '#65597b',
                  border: '1px solid #d8b4fe',
                  fontWeight: '700',
                  fontSize: '13.5px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                title="Listen to all recorded candidate question-and-answer turns"
              >
                <Headphones size={15} />
                <span>Listen Audio</span>
              </button>

              <button
                onClick={handlePrint}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '9px 18px',
                  borderRadius: '9999px',
                  background: '#65597b',
                  color: '#ffffff',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '13.5px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(101, 89, 123, 0.2)',
                }}
              >
                <Printer size={15} />
                <span>Export PDF / Print</span>
              </button>

              <button
                onClick={handleShare}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '9px 18px',
                  borderRadius: '9999px',
                  background: isCopied ? '#dcfce7' : '#ffffff',
                  color: isCopied ? '#15803d' : '#374151',
                  border: `1px solid ${isCopied ? '#bbf7d0' : '#e5e7eb'}`,
                  fontWeight: '600',
                  fontSize: '13.5px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {isCopied ? <Check size={15} /> : <Share2 size={15} />}
                <span>{isCopied ? 'Link Copied!' : 'Share'}</span>
              </button>

              <button
                onClick={() => navigate('/setup')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '9px 18px',
                  borderRadius: '9999px',
                  background: '#f3e8ff',
                  color: '#65597b',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '13.5px',
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={15} />
                <span>Retake</span>
              </button>
            </div>
          </div>
        </Card>

        {/* TOP ROW GRID: OVERALL READINESS & DOMAIN PILLARS */}
        <div className="report-hero-grid">
          <Card
            className="report-hero-card"
            style={{
              padding: '22px 24px',
              background: '#ffffff',
              borderRadius: '20px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.02)',
            }}
          >
            {/* Header with Title and Hiring Signal Badge */}
            <div className="report-hero-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div className="report-hero-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={18} style={{ color: '#65597b' }} />
                <h2 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: 0 }}>
                  Overall Assessment
                </h2>
              </div>

              {/* Hiring Signal Badge Chip */}
              <span
                className="report-hero-signal-badge"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  background: signalStyle.bg,
                  color: signalStyle.text,
                  border: `1px solid ${signalStyle.border}`,
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  fontSize: '12px',
                  fontWeight: '700',
                }}
              >
                <span>{overall_hiring_signal}</span>
              </span>
            </div>

            {/* Main Score & Telemetry Two-Column Layout */}
            <div className="report-assessment-layout">
              {/* Circular Donut Gauge */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                <div className="report-donut-wrapper" style={{ position: 'relative', width: '120px', height: '120px' }}>
                  <svg className="report-donut-svg" width="120" height="120" viewBox="0 0 160 160">
                    <circle cx="80" cy="80" r="62" fill="none" stroke="#f3f4f6" strokeWidth="14" />
                    <circle
                      cx="80"
                      cy="80"
                      r="62"
                      fill="none"
                      stroke="#65597b"
                      strokeWidth="14"
                      strokeDasharray={2 * Math.PI * 62}
                      strokeDashoffset={2 * Math.PI * 62 * (1 - Math.min(100, Math.max(0, overall_technical_score)) / 100)}
                      strokeLinecap="round"
                      transform="rotate(-90 80 80)"
                      style={{ transition: 'stroke-dashoffset 1s ease' }}
                    />
                  </svg>

                  <div
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                    }}
                  >
                    <span className="report-donut-score" style={{ fontSize: '30px', fontWeight: '800', color: '#111827', lineHeight: '1' }}>
                      {overall_technical_score}
                    </span>
                    <span className="report-donut-denom" style={{ fontSize: '11px', fontWeight: '700', color: '#6b7280', marginTop: '2px' }}>
                      / 100
                    </span>
                  </div>
                </div>
                <span className="report-donut-label" style={{ fontSize: '11.5px', fontWeight: '700', color: '#65597b', marginTop: '6px' }}>
                  Technical Score
                </span>
              </div>

              {/* Telemetry Micro-Cards */}
              <div className="report-telemetry-container" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {/* Vocal Confidence Card */}
                <div
                  className="report-telemetry-card"
                  style={{
                    background: '#f9fafb',
                    borderRadius: '12px',
                    padding: '10px 14px',
                    border: '1px solid #f3f4f6',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div className="report-telemetry-label" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#4b5563', fontSize: '12.5px', fontWeight: '600' }}>
                      <Zap size={14} style={{ color: '#65597b' }} />
                      <span>Vocal Confidence</span>
                    </div>
                    <span className="report-telemetry-val" style={{ fontSize: '13px', fontWeight: '800', color: overall_vocal_confidence_score >= 70 ? '#15803d' : '#b45309' }}>
                      {overall_vocal_confidence_score}%
                    </span>
                  </div>
                  <div className="report-telemetry-bar" style={{ width: '100%', height: '5px', background: '#e5e7eb', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${overall_vocal_confidence_score}%`,
                        height: '100%',
                        background: overall_vocal_confidence_score >= 70 ? '#15803d' : '#b45309',
                        borderRadius: '9999px',
                      }}
                    />
                  </div>
                </div>

                {/* Speech & Audio Telemetry Card */}
                <div
                  className="report-telemetry-card"
                  style={{
                    background: '#f9fafb',
                    borderRadius: '12px',
                    padding: '10px 14px',
                    border: '1px solid #f3f4f6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div className="report-telemetry-label" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#4b5563', fontSize: '12.5px', fontWeight: '600' }}>
                    <Mic size={14} style={{ color: '#65597b' }} />
                    <span>Est. Filler Words</span>
                  </div>
                  <span
                    className="report-filler-badge"
                    style={{
                      fontSize: '12px',
                      fontWeight: '800',
                      padding: '2px 8px',
                      borderRadius: '9999px',
                      background: totalFillerWords > 8 ? '#fee2e2' : '#dcfce7',
                      color: totalFillerWords > 8 ? '#991b1b' : '#15803d',
                    }}
                  >
                    {totalFillerWords} words
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* CARD 2: TECHNICAL DOMAIN PILLARS */}
          <Card
            className="report-hero-card"
            style={{
              padding: '22px 24px',
              background: '#ffffff',
              borderRadius: '20px',
              border: '1px solid rgba(229, 231, 235, 0.8)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.02)',
            }}
          >
            {/* Header */}
            <div>
              <div className="report-hero-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div className="report-hero-card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart2 size={18} style={{ color: '#65597b' }} />
                  <h2 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: 0 }}>
                    Technical Domain Pillars
                  </h2>
                </div>
                <span
                  className="report-hero-signal-badge"
                  style={{
                    fontSize: '11.5px',
                    fontWeight: '700',
                    color: '#65597b',
                    background: '#f3e8ff',
                    border: '1px solid #e9d8fd',
                    padding: '3px 9px',
                    borderRadius: '9999px',
                  }}
                >
                  {technical_pillars.length} Pillars
                </span>
              </div>

              {/* Clean, High-Legibility Skill Bars */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {technical_pillars.length > 0 ? (
                  technical_pillars.map((pillar, pIdx) => (
                    <div key={pIdx}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                        <span style={{ fontSize: '13px', fontWeight: '700', color: '#374151' }}>
                          {pillar.pillar_name}
                        </span>
                        <span
                          style={{
                            fontSize: '12px',
                            fontWeight: '800',
                            color: pillar.score >= 70 ? '#15803d' : pillar.score >= 40 ? '#b45309' : '#65597b',
                            background: '#f9fafb',
                            padding: '1px 7px',
                            borderRadius: '6px',
                            border: '1px solid #f3f4f6',
                          }}
                        >
                          {pillar.score}%
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: '#f3f4f6', borderRadius: '9999px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${pillar.score}%`,
                            height: '100%',
                            background: '#65597b',
                            borderRadius: '9999px',
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '13.5px', color: '#6b7280', fontStyle: 'italic' }}>
                    No pillar breakdown scores generated.
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Scale Legend Indicator */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: '14px',
                paddingTop: '10px',
                borderTop: '1px solid #f3f4f6',
                fontSize: '11px',
                color: '#6b7280',
                fontWeight: '600',
              }}
            >
              <span>0-39% Needs Focus</span>
              <span>•</span>
              <span>40-69% Competent</span>
              <span>•</span>
              <span>70-100% Strong</span>
            </div>
          </Card>
        </div>

        {/* BEHAVIORAL FLAGS CARD (IF ANY) */}
        {behavioral_flags.length > 0 && (
          <Card style={{ padding: '18px 24px', background: '#fff1f2', borderRadius: '18px', border: '1px solid #fecdd3' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <ShieldAlert size={19} style={{ color: '#e11d48' }} />
              <h2 style={{ fontSize: '16px', fontWeight: '800', color: '#9f1239', margin: 0 }}>
                Observed Behavioral & Telemetry Flags ({behavioral_flags.length})
              </h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
              {behavioral_flags.map((flag, idx) => (
                <div key={idx} className="report-flag-item">
                  <div className="report-flag-content">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <span style={{ fontSize: '11.5px', fontWeight: '800', padding: '3px 8px', borderRadius: '9999px', background: flag.severity === 'CRITICAL' ? '#fee2e2' : '#fef3c7', color: flag.severity === 'CRITICAL' ? '#991b1b' : '#92400e' }}>
                        {flag.severity}
                      </span>
                      <span className="report-flag-turn" style={{ fontSize: '12.5px', color: '#9ca3af', fontWeight: '700' }}>
                        Turn #{flag.turn_id}
                      </span>
                    </div>
                    <span style={{ fontSize: '13.5px', color: '#1f2937', fontWeight: '500', lineHeight: '1.5' }}>
                      {flag.description}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* CANDIDATE FEEDBACK & STUDY ROADMAP */}
        {candidate_feedback && (candidate_feedback.key_strengths || candidate_feedback.primary_growth_areas) && (
          <div className="report-feedback-grid">
            {/* Strengths */}
            <Card style={{ padding: '20px 24px', background: '#ffffff', borderRadius: '18px', border: '1px solid rgba(229, 231, 235, 0.8)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: '#15803d', fontWeight: '800', fontSize: '15px' }}>
                <CheckCircle2 size={18} />
                <span>Key Technical Strengths</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(candidate_feedback.key_strengths || []).map((str, i) => (
                  <li key={i} style={{ fontSize: '13.5px', color: '#374151', lineHeight: '1.5' }}>
                    {str}
                  </li>
                ))}
              </ul>
            </Card>

            {/* Growth Areas */}
            <Card style={{ padding: '20px 24px', background: '#ffffff', borderRadius: '18px', border: '1px solid rgba(229, 231, 235, 0.8)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: '#b45309', fontWeight: '800', fontSize: '15px' }}>
                <TrendingUp size={18} />
                <span>Primary Growth Areas</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(candidate_feedback.primary_growth_areas || []).map((area, i) => (
                  <li key={i} style={{ fontSize: '13.5px', color: '#374151', lineHeight: '1.5' }}>
                    {area}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        )}

        {/* RECOMMENDED STUDY TOPICS */}
        {candidate_feedback?.recommended_topics_to_study?.length > 0 && (
          <Card style={{ padding: '18px 24px', background: '#ffffff', borderRadius: '18px', border: '1px solid rgba(229, 231, 235, 0.8)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#65597b', fontWeight: '800', fontSize: '15px' }}>
              <BookOpen size={18} />
              <span>Recommended Topics & Frameworks to Study</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {candidate_feedback.recommended_topics_to_study.map((topic, i) => (
                <span key={i} style={{ fontSize: '13px', fontWeight: '600', padding: '6px 14px', borderRadius: '9999px', background: '#f5f0fb', color: '#65597b', border: '1px solid #e9d8fd', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={13} />
                  <span>{topic}</span>
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* BOTTOM SECTION: QUESTION-BY-QUESTION BREAKDOWN WITH EVA & AUDIO PLAYBACK */}
        <Card
          style={{
            padding: '24px 28px',
            background: '#ffffff',
            borderRadius: '20px',
            border: '1px solid rgba(229, 231, 235, 0.8)',
          }}
          className="report-hero-card"
        >
          {/* Section Title */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
              <MessageSquare size={18} style={{ color: '#65597b' }} />
              <h2 style={{ fontSize: '15px', fontWeight: '800', color: '#1f2937', letterSpacing: '0.04em', margin: 0, textTransform: 'uppercase' }}>
                Question-By-Question Breakdown & Spoken Audio ({turn_evaluations.length} Turns)
              </h2>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#6b7280' }}>
              <Headphones size={15} style={{ color: '#65597b' }} />
              <span>Click "Listen Answer" on any turn to review how you spoke</span>
            </div>
          </div>

          {/* Turn Accordions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {turn_evaluations.length > 0 ? (
              turn_evaluations.map((t, idx) => {
                const isExpanded = expandedQuestions[idx];
                const isThisTurnPlaying = playingTurnId === t.turn_id && isPlaying;
                const isThisTurnSelected = playingTurnId === t.turn_id;

                return (
                  <div
                    key={t.turn_id || idx}
                    style={{
                      border: `1px solid ${isThisTurnSelected ? '#d8b4fe' : '#e5e7eb'}`,
                      borderRadius: '16px',
                      overflow: 'hidden',
                      transition: 'all 0.2s ease',
                      boxShadow: isThisTurnSelected ? '0 4px 16px rgba(101, 89, 123, 0.08)' : 'none',
                    }}
                  >
                    {/* Accordion Header */}
                    <div
                      onClick={() => toggleQuestion(idx)}
                      className="report-q-header"
                      style={{
                        background: isExpanded ? '#fafafa' : '#ffffff',
                      }}
                    >
                      <div className="report-q-left">
                        <span
                          style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            background: isThisTurnSelected ? '#65597b' : '#f3e8ff',
                            color: isThisTurnSelected ? '#ffffff' : '#65597b',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: '800',
                            fontSize: '12px',
                            flexShrink: 0,
                            transition: 'all 0.2s ease',
                          }}
                        >
                          Q{t.turn_id}
                        </span>
                        <h3 style={{ fontSize: '14.5px', fontWeight: '700', color: '#111827', margin: 0, flex: 1, lineHeight: '1.4' }}>
                          {t.question_text}
                        </h3>
                      </div>

                      {/* Header Score Badges & Inline Audio Indicator */}
                      <div className="report-q-right" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div className="report-q-badges">
                          {isThisTurnPlaying && (
                            <span
                              style={{
                                fontSize: '11.5px',
                                fontWeight: '800',
                                padding: '3px 8px',
                                borderRadius: '9999px',
                                background: '#65597b',
                                color: '#ffffff',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                            >
                              <Volume2 size={12} />
                              <span>Playing</span>
                            </span>
                          )}

                          <span style={{ fontSize: '12px', fontWeight: '800', padding: '4px 10px', borderRadius: '9999px', background: '#ede6f8', color: '#65597b' }}>
                            Tech: {t.technical_score}/10
                          </span>
                          <span style={{ fontSize: '12px', fontWeight: '800', padding: '4px 10px', borderRadius: '9999px', background: '#e0f2fe', color: '#0369a1' }}>
                            Vocal: {t.vocal_confidence_score}/10
                          </span>
                        </div>
                        <div style={{ color: '#6b7280' }}>
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </div>
                      </div>
                    </div>

                    {/* Accordion Body */}
                    <div
                      className="report-q-body turn-accordion-body"
                      style={{
                        display: isExpanded ? 'block' : 'none',
                        padding: '18px 22px 22px 22px',
                        borderTop: '1px solid #f3f4f6',
                        background: '#ffffff',
                      }}
                    >
                      <div className="report-q-body-grid">
                        {/* Left Column: Dual Transcripts */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          {/* Candidate Live STT Transcript */}
                          <div style={{ background: '#fafafa', borderRadius: '14px', padding: '16px', border: '1px solid #f3f4f6' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '8px', fontSize: '12px', fontWeight: '800', color: '#6b7280' }}>
                              <Mic size={14} />
                              <span>Candidate Live Answer (STT)</span>
                            </div>
                            <p style={{ fontSize: '13.5px', fontStyle: 'italic', color: '#374151', margin: 0, lineHeight: '1.6' }}>
                              "{t.candidate_transcript || 'No candidate response recorded for this turn.'}"
                            </p>
                          </div>

                          {/* Gemini Verified Clean Transcript */}
                          {t.gemini_verified_transcript && t.gemini_verified_transcript !== t.candidate_transcript && (
                            <div style={{ background: '#f0fdf4', borderRadius: '14px', padding: '16px', border: '1px solid #bbf7d0' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '8px', fontSize: '12px', fontWeight: '800', color: '#15803d' }}>
                                <CheckCircle2 size={14} />
                                <span>Gemini Verified Audio Transcript</span>
                              </div>
                              <p style={{ fontSize: '13.5px', color: '#166534', margin: 0, lineHeight: '1.6' }}>
                                "{t.gemini_verified_transcript}"
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Right Column: Eva's Assessment */}
                        <div style={{ background: '#fafafa', borderRadius: '14px', padding: '16px', border: '1px solid #f3f4f6' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '12px', fontSize: '12.5px', fontWeight: '800', color: '#65597b' }}>
                            <Sparkles size={15} />
                            <span>Eva's Turn Assessment</span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {/* Audio notes */}
                            {t.audio_notes && (
                              <div style={{ fontSize: '13px', color: '#374151', lineHeight: '1.5' }}>
                                <strong>Delivery & Tone:</strong> {t.audio_notes}
                              </div>
                            )}

                            {/* Missing concepts */}
                            {t.missing_concepts && t.missing_concepts.length > 0 && (
                              <div>
                                <div style={{ fontSize: '12px', fontWeight: '800', color: '#dc2626', marginBottom: '5px' }}>
                                  Missing Key Concepts:
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                  {t.missing_concepts.map((concept, cIdx) => (
                                    <span key={cIdx} style={{ fontSize: '11.5px', fontWeight: '700', background: '#fee2e2', color: '#991b1b', padding: '3px 8px', borderRadius: '9999px' }}>
                                      {concept}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Resume verification note */}
                            {t.resume_verification_note && (
                              <div style={{ fontSize: '12px', color: '#4b5563', fontStyle: 'italic', marginTop: '4px', borderTop: '1px dashed #e5e7eb', paddingTop: '8px' }}>
                                <strong>Resume Alignment:</strong> {t.resume_verification_note}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* TURN AUDIO PLAYBACK CONTROLS WIDGET */}
                      <div
                        className="report-audio-widget"
                        style={{
                          marginTop: '16px',
                          background: isThisTurnSelected ? '#f8f4fc' : '#f9fafb',
                          border: `1px solid ${isThisTurnSelected ? '#d8b4fe' : '#e5e7eb'}`,
                          borderRadius: '16px',
                          padding: '14px 18px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          flexWrap: 'wrap',
                          gap: '14px',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {/* Play Button & Spoken Audio Info */}
                        <div className="report-audio-main-row" style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: '240px' }}>
                          <button
                            onClick={() => handleToggleTurnAudio(t.turn_id, t.audio_start_sec, t.audio_end_sec)}
                            style={{
                              width: '42px',
                              height: '42px',
                              borderRadius: '50%',
                              background: isThisTurnPlaying ? '#4c1d95' : '#65597b',
                              color: '#ffffff',
                              border: 'none',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: 'pointer',
                              boxShadow: '0 4px 12px rgba(101, 89, 123, 0.2)',
                              flexShrink: 0,
                              transition: 'transform 0.15s ease',
                            }}
                            title={isThisTurnPlaying ? 'Pause Audio' : `Listen Spoken Answer for Turn #${t.turn_id}`}
                          >
                            {isThisTurnPlaying ? (
                              <Pause size={18} fill="#ffffff" />
                            ) : (
                              <Play size={18} fill="#ffffff" style={{ marginLeft: '2px' }} />
                            )}
                          </button>

                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '13.5px', fontWeight: '800', color: '#111827' }}>
                                Candidate Spoken Answer Audio
                              </span>
                              {isThisTurnPlaying && (
                                <span
                                  style={{
                                    fontSize: '11.5px',
                                    fontWeight: '800',
                                    padding: '2px 8px',
                                    borderRadius: '9999px',
                                    background: '#e9d5ff',
                                    color: '#6b21a8',
                                  }}
                                >
                                  Playing Turn #{t.turn_id}
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Mic size={13} />
                              <span>
                                {isThisTurnSelected
                                  ? `${formatTime(audioCurrentTime)} / ${formatTime((audioDuration && audioDuration > 0) ? audioDuration : ((t.audio_end_sec && t.audio_start_sec && t.audio_end_sec > t.audio_start_sec) ? (t.audio_end_sec - t.audio_start_sec) : (t.telemetry?.turn_duration_sec || 0)))}`
                                  : (t.audio_end_sec && t.audio_start_sec && t.audio_end_sec > t.audio_start_sec)
                                  ? `Duration: ~${Math.round(t.audio_end_sec - t.audio_start_sec)}s (Turn #${t.turn_id})`
                                  : t.telemetry?.turn_duration_sec
                                  ? `Duration: ~${Math.round(t.telemetry.turn_duration_sec)}s (Turn #${t.turn_id})`
                                  : `Turn #${t.turn_id} Audio Stream`}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Interactive Scrubber (When this turn is selected) */}
                        {isThisTurnSelected && (
                          <div className="report-audio-scrubber-row" style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 2, minWidth: '220px' }}>
                            <input
                              type="range"
                              min={0}
                              max={((audioDuration && audioDuration > 0) ? audioDuration : ((t.audio_end_sec && t.audio_start_sec && t.audio_end_sec > t.audio_start_sec) ? (t.audio_end_sec - t.audio_start_sec) : (t.telemetry?.turn_duration_sec || 1)))}
                              step={0.1}
                              value={audioCurrentTime}
                              onChange={handleSeekTurnAudio}
                              style={{
                                width: '100%',
                                accentColor: '#65597b',
                                cursor: 'pointer',
                                height: '6px',
                              }}
                            />
                            <span style={{ fontSize: '12px', fontWeight: '800', color: '#65597b', minWidth: '70px', textAlign: 'right' }}>
                              {formatTime(audioCurrentTime)} / {formatTime((audioDuration && audioDuration > 0) ? audioDuration : ((t.audio_end_sec && t.audio_start_sec && t.audio_end_sec > t.audio_start_sec) ? (t.audio_end_sec - t.audio_start_sec) : (t.telemetry?.turn_duration_sec || 0)))}
                            </span>
                          </div>
                        )}

                        {/* Audio Controls (±5s, Speed, Listen CTA) */}
                        <div className="report-audio-controls-row" style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                          {isThisTurnSelected && (
                            <>
                              <button
                                onClick={() => handleJumpTurnAudio(-5)}
                                style={{
                                  background: '#ffffff',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '9999px',
                                  padding: '5px 10px',
                                  fontSize: '12px',
                                  fontWeight: '700',
                                  color: '#4b5563',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                }}
                                title="Rewind 5s"
                              >
                                <RotateCcw size={11} />
                                <span>-5s</span>
                              </button>

                              <button
                                onClick={() => handleJumpTurnAudio(5)}
                                style={{
                                  background: '#ffffff',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '9999px',
                                  padding: '5px 10px',
                                  fontSize: '12px',
                                  fontWeight: '700',
                                  color: '#4b5563',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                }}
                                title="Forward 5s"
                              >
                                <RotateCw size={11} />
                                <span>+5s</span>
                              </button>

                              <button
                                onClick={handleCyclePlaybackRate}
                                style={{
                                  background: '#ffffff',
                                  border: '1px solid #d8b4fe',
                                  borderRadius: '9999px',
                                  padding: '5px 11px',
                                  fontSize: '12px',
                                  fontWeight: '800',
                                  color: '#65597b',
                                  cursor: 'pointer',
                                }}
                                title="Change playback speed"
                              >
                                {playbackRate}x
                              </button>
                            </>
                          )}

                          {!isThisTurnSelected && (
                            <button
                              onClick={() => handleToggleTurnAudio(t.turn_id, t.audio_start_sec, t.audio_end_sec)}
                              style={{
                                padding: '8px 16px',
                                borderRadius: '9999px',
                                background: '#ffffff',
                                border: '1px solid #d8b4fe',
                                color: '#65597b',
                                fontSize: '13px',
                                fontWeight: '700',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                              }}
                            >
                              <Volume2 size={14} />
                              <span>Listen Answer</span>
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Optional Error Notice */}
                      {isThisTurnSelected && audioError && (
                        <div style={{ marginTop: '8px', fontSize: '12.5px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <AlertTriangle size={13} />
                          <span>{audioError}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                No per-turn evaluation items recorded for this session.
              </div>
            )}
          </div>
        </Card>

        {/* NEXT STEPS & NAVIGATION ACTION CARD */}
        <Card
          className="report-next-steps-card no-print"
          style={{
            background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
            border: '1px solid rgba(101, 89, 123, 0.15)',
            boxShadow: '0 8px 24px rgba(101, 89, 123, 0.04)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '46px', height: '46px', borderRadius: '15px', background: '#ede6f8', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#65597b', flexShrink: 0 }}>
              <Sparkles size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#111827', margin: '0 0 3px 0' }}>
                Ready for your next mock session?
              </h3>
              <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>
                Practice another track or review your historical performance trends.
              </p>
            </div>
          </div>

          <div className="report-next-steps-buttons" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => navigate('/analytics')}
              style={{
                padding: '9px 18px',
                borderRadius: '11px',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                color: '#374151',
                fontSize: '13.5px',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              View Analytics
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                padding: '9px 18px',
                borderRadius: '11px',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                color: '#374151',
                fontSize: '13.5px',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/setup')}
              className="start-new-btn"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 20px',
                borderRadius: '11px',
                border: 'none',
                background: '#65597b',
                color: '#ffffff',
                fontSize: '13.5px',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(101, 89, 123, 0.2)',
              }}
            >
              <span>Start New Session</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </Card>
      </PageWrapper>
    </div>
  );
};

export default Report;

