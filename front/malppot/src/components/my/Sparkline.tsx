// src/components/myPage/Sparkline.tsx
import React from 'react';
import styled from 'styled-components';

interface SparklineProps {
  scores?: number[];
}

const PointTooltipContainer = styled.g`
  .tooltip {
    visibility: hidden;
    opacity: 0;
    transition: visibility 0s, opacity 0.2s linear;
    pointer-events: none;
  }
  &:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }
`;

const PointTooltipText = styled.text`
  font-size: 12px;
  font-weight: bold;
  fill: #343a40;
  text-anchor: middle;
`;

const Sparkline = ({ scores = [] }: SparklineProps): React.JSX.Element => {
  if (scores.length === 0) {
    return <span style={{ color: "#aaa", fontSize: "0.9rem" }}>기록 없음</span>;
  }
  const width = 120;
  const height = 30;
  const lastScore = scores[scores.length - 1];
  const prevScore = scores.length > 1 ? scores[scores.length - 2] : lastScore;
  const strokeColor = lastScore >= prevScore ? "#27ae60" : "#e74c3c";
  const getCoords = (score: number, i: number, length: number) => {
    const x = length > 1 ? (i / (length - 1)) * width : width / 2;
    const y = height - (score / 100) * (height - 10) - 5;
    return { x, y };
  };
  const points = scores
    .map((s, i) => {
      const { x, y } = getCoords(s, i, scores.length);
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      style={{ overflow: "visible" }}
    >
      <line
        x1="0"
        y1={height - (50 / 100) * (height - 10) - 5}
        x2={width}
        y2={height - (50 / 100) * (height - 10) - 5}
        stroke="#eee"
        strokeDasharray="2,2"
      />
      {scores.length > 1 && (
        <polyline
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          points={points}
        />
      )}
      {scores.map((s, i) => {
        const { x, y } = getCoords(s, i, scores.length);
        return (
          <PointTooltipContainer key={i}>
            <circle cx={x} cy={y} r="8" fill="transparent" />
            <circle cx={x} cy={y} r="3" fill={strokeColor} />
            <PointTooltipText className="tooltip" x={x} y={y - 10}>
              {s}점
            </PointTooltipText>
          </PointTooltipContainer>
        );
      })}
    </svg>
  );
};

export default Sparkline;