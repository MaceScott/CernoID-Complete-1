import React from 'react';

interface LabelProps {
  children: React.ReactNode;
  className?: string;
}

const Label: React.FC<LabelProps> = ({ children, className = '' }) => {
  return (
    <label className={`text-sm font-medium text-gray-700 ${className}`}>
      {children}
    </label>
  );
};

export default Label; 