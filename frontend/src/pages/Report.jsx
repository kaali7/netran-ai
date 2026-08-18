import React from 'react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';

export const Report = () => {
  return (
    <div>
      <Navbar />
      <PageWrapper>
        <Card>
          <h1 className="text-headline-xl">Evaluation Scorecard & Multimodal Insights</h1>
          <p className="text-body-md" style={{ marginTop: '8px' }}>
            Stage 4 technical scoring, speech delivery metrics, and feedback breakdown (Phase 2).
          </p>
        </Card>
      </PageWrapper>
    </div>
  );
};

export default Report;
