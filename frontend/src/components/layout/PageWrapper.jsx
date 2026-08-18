import React from 'react';

export const PageWrapper = ({ children }) => {
  return (
    <div
      style={{
        maxWidth: 'var(--container-max)',
        margin: '0 auto',
        padding: '0 24px 60px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
      }}
    >
      {children}
    </div>
  );
};

export default PageWrapper;
