import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import WelcomeBanner from '../components/dashboard/WelcomeBanner';
import StatsRow from '../components/dashboard/StatsRow';
import LaunchPractice from '../components/dashboard/LaunchPractice';
import LastSessionCard from '../components/dashboard/LastSessionCard';
import SessionsTable from '../components/dashboard/SessionsTable';
import TemplatePicker from '../components/dashboard/TemplatePicker';
import useDashboard from '../hooks/useDashboard';
import { duplicateSession } from '../services/sessionService';

export const Dashboard = () => {
  const { data, loading } = useDashboard();
  const navigate = useNavigate();

  // Template Picker modal state
  const [showTemplatePicker, setShowTemplatePicker] = useState(false);

  const handleStartFullMock = () => {
    setShowTemplatePicker(true);
  };

  const handlePracticeCustomJD = () => {
    navigate('/setup');
  };

  /** Called when TemplatePicker successfully creates a session — navigate to voice interview. */
  const handleSessionReady = (sessionId) => {
    setShowTemplatePicker(false);
    navigate(`/interview/${sessionId}`);
  };

  const [isDuplicating, setIsDuplicating] = useState(false);

  const handleRetakeSession = async () => {
    if (data?.lastSession?.id && !isDuplicating) {
      try {
        setIsDuplicating(true);
        const res = await duplicateSession(data.lastSession.id);
        if (res?.session_id) {
          navigate(`/interview/${res.session_id}`);
        } else {
          navigate('/setup');
        }
      } catch (err) {
        console.error("Failed to duplicate session:", err);
        navigate('/setup');
      } finally {
        setIsDuplicating(false);
      }
    } else {
      navigate('/setup');
    }
  };

  const handleViewReport = () => {
    if (data?.lastSession?.id) {
      navigate(`/report/${data.lastSession.id}`);
    } else {
      navigate('/setup');
    }
  };

  const handleNewWorkspace = () => {
    navigate('/setup');
  };

  const handleViewFeedback = (sessionId) => {
    navigate(`/report/${sessionId}`);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar userName={data.candidateName} />

      {/* Main Dashboard Body */}
      <PageWrapper>
        {/* 1. Welcome Banner */}
        <WelcomeBanner
          candidateName={data.candidateFirstName}
          readinessPct={data.readinessScore}
          targetRole={data.targetRole}
        />

        {/* 2. Four Metric Stats Cards */}
        <StatsRow
          readinessPct={data.readinessScore}
          streakDays={data.practiceStreakDays}
          strongestSkills={data.strongestSkills}
          strongestSubtitle={data.strongestSkillsDetail}
          needsFocusSkill={data.needsFocusSkill}
          needsFocusSubtitle={data.needsFocusDetail}
          loading={loading}
        />

        {/* 3. Middle Two-Column Grid: Launch Practice + Last Interview Session */}
        <div className="dashboard-split-grid">
          <LaunchPractice
            onStartFullMock={handleStartFullMock}
            onPracticeCustomJD={handlePracticeCustomJD}
          />
          <LastSessionCard
            lastSession={data.lastSession}
            onRetake={handleRetakeSession}
            onViewReport={handleViewReport}
          />
        </div>

        {/* 4. Bottom Full-Width Card: Recent Practice Sessions & Feedback */}
        <SessionsTable
          sessions={data.recentSessions}
          onNewWorkspace={handleNewWorkspace}
          onViewFeedback={handleViewFeedback}
        />
      </PageWrapper>

      {/* Template Picker Modal — mounts at root level for proper overlay positioning */}
      <TemplatePicker
        isOpen={showTemplatePicker}
        onClose={() => setShowTemplatePicker(false)}
        onSessionReady={handleSessionReady}
      />
    </div>
  );
};

export default Dashboard;

