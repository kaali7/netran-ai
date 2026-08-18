import React from 'react';
import Navbar from '../components/layout/Navbar';
import PageWrapper from '../components/layout/PageWrapper';
import Card from '../components/ui/Card';

export const Interview = () => {
  return (
    <div>
      <Navbar />
      <PageWrapper>
        <Card>
          <h1 className="text-headline-xl">Live Voice Interview Room</h1>
          <p className="text-body-md" style={{ marginTop: '8px' }}>
            Full-duplex real-time Web Audio Worklet & WebSocket conversation with Eva (Phase 2).
          </p>
        </Card>
      </PageWrapper>
    </div>
  );
};

export default Interview;
