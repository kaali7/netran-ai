import React from 'react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import WelcomeBanner from '../components/dashboard/WelcomeBanner';
import StatsRow from '../components/dashboard/StatsRow';
import LaunchPractice from '../components/dashboard/LaunchPractice';
import LastSessionCard from '../components/dashboard/LastSessionCard';
import SessionsTable from '../components/dashboard/SessionsTable';
import useDashboard from '../hooks/useDashboard';

export const Dashboard = () => {
  const { data } = useDashboard();

  const handleStartFullMock = () => {
    alert('Starting Full 15-Question Technical Mock Interview Setup...');
  };

  const handlePracticeCustomJD = () => {
    alert('Opening Custom Job Description Practice Setup...');
  };

  const handleRetakeSession = () => {
    alert(`Retaking Session #${data.lastSession.number}: ${data.lastSession.title}`);
  };

  const handleViewReport = () => {
    alert(`Opening Detailed Multimodal Report for Session #${data.lastSession.number}`);
  };

  const handleNewWorkspace = () => {
    alert('Creating New Workspace for Targeted Interview Prep...');
  };

  const handleViewFeedback = (sessionId) => {
    alert(`Viewing Feedback & Scorecard for Session ${sessionId}`);
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
        />

        {/* 3. Middle Two-Column Grid: Launch Practice + Last Interview Session */}
        <div className="dashboard-split-grid">
          <LaunchPractice
            onStartFullMock={handleStartFullMock}
            onPracticeCustomJD={handlePracticeCustomJD}
          />
          <LastSessionCard
            sessionNumber={data.lastSession.number}
            sessionTitle={data.lastSession.title}
            scorePct={data.lastSession.score}
            status={data.lastSession.status}
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
    </div>
  );
};

export default Dashboard;
