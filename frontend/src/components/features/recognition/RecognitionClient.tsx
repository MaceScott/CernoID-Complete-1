'use client';

import { useState } from 'react';
import { ResultsViewer } from './ResultsViewer';

export function RecognitionClient() {
  const [imageUrl] = useState('');
  const [faces] = useState([]);

  return (
    <ResultsViewer
      imageUrl={imageUrl}
      faces={faces}
      loading={false}
      error={undefined}
      onRefresh={() => {}}
    />
  );
} 