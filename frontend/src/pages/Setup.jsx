import React from 'react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';

export const Setup = () => {
  return (
    <div>
      <Navbar />
      <PageWrapper>
        <Card>
          <h1 className="text-headline-xl">Interview Setup & Ingestion</h1>
          <p className="text-body-md" style={{ marginTop: '8px' }}>
            Resume and Job Description parsing pipeline (Phase 2).
          </p>
        </Card>
      </PageWrapper>
    </div>
  );
};

export default Setup;
