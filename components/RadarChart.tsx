import React from 'react';
import { StyleMetrics } from '../types';

interface RadarChartProps {
  metrics: StyleMetrics;
}

export const RadarChart: React.FC<RadarChartProps> = ({ metrics }) => {
  const size = 200;
  const center = size / 2;
  const radius = size * 0.4;
  
  const features = [
    { key: 'complexity', label: 'Complejidad' },
    { key: 'formality', label: 'Formalidad' },
    { key: 'emotionality', label: 'Emotividad' },
    { key: 'sarcasm', label: 'Sarcasmo' },
    { key: 'creativity', label: 'Creatividad' },
  ];

  const total = features.length;
  
  // Calculate points for the polygon
  const points = features.map((feature, i) => {
    const angle = (Math.PI * 2 * i) / total - Math.PI / 2;
    // @ts-ignore
    const value = metrics[feature.key] || 0;
    const r = (value / 100) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return `${x},${y}`;
  }).join(' ');

  // Calculate grid lines (concentric pentagons)
  const grids = [0.2, 0.4, 0.6, 0.8, 1].map((scale) => {
     return features.map((_, i) => {
        const angle = (Math.PI * 2 * i) / total - Math.PI / 2;
        const r = radius * scale;
        const x = center + r * Math.cos(angle);
        const y = center + r * Math.sin(angle);
        return `${x},${y}`;
     }).join(' ');
  });

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background Grids */}
        {grids.map((points, i) => (
          <polygon
            key={i}
            points={points}
            fill="none"
            stroke="#334155"
            strokeWidth="1"
          />
        ))}

        {/* Axis Lines */}
        {features.map((_, i) => {
           const angle = (Math.PI * 2 * i) / total - Math.PI / 2;
           const x = center + radius * Math.cos(angle);
           const y = center + radius * Math.sin(angle);
           return (
             <line key={i} x1={center} y1={center} x2={x} y2={y} stroke="#334155" strokeWidth="1" />
           );
        })}

        {/* Data Polygon */}
        <polygon
          points={points}
          fill="rgba(251, 191, 36, 0.2)"
          stroke="#fbbf24"
          strokeWidth="2"
        />

        {/* Labels */}
        {features.map((f, i) => {
           const angle = (Math.PI * 2 * i) / total - Math.PI / 2;
           // Push label out a bit further than radius
           const r = radius + 20; 
           const x = center + r * Math.cos(angle);
           const y = center + r * Math.sin(angle);
           
           return (
             <text
               key={i}
               x={x}
               y={y}
               textAnchor="middle"
               dominantBaseline="middle"
               fill="#94a3b8"
               fontSize="10"
               fontFamily="monospace"
               className="uppercase"
             >
               {f.label}
             </text>
           );
        })}
      </svg>
    </div>
  );
};