import React from 'react';

export const Card = ({
  children,
  className = '',
  interactive = false,
  style = {},
  ...props
}) => {
  return (
    <div
      className={`glass-card ${interactive ? 'glass-card-interactive' : ''} ${className}`}
      style={style}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
