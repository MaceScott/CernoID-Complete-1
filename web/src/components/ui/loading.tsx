import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
}

const Loading: React.FC<LoadingProps> = ({ size = 'md' }) => {
  const sizeClass = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-12 w-12' : 'h-8 w-8';
  return (
    <div className={`flex items-center justify-center ${sizeClass}`}>
      <div className="animate-spin rounded-full border-t-2 border-b-2 border-gray-900"></div>
    </div>
  );
};

export default Loading; 