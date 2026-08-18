import React from 'react';

export const PageWrapper = ({ children }) => {
  return (
    <div
      style={{
        width: '100%',
        maxWidth: '100%',
        margin: '0 auto',
        padding: '0 36px 60px 36px',
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
