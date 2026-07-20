import React, { useState } from "react";
import styled from "styled-components";

interface GraphData {
    record_date?: string;
    day?: string;
    score: number;
}

interface SvgGraphProps {
    data: GraphData[];
}

const GraphContainer = styled.div`
  display: flex;
  align-items: center;
  min-height: 120px;
`;

const StyledSvg = styled.svg`
  flex-shrink: 0;
  width: 300px;
  height: 100px;
`;

const InfoPanel = styled.div`
  min-width: 90px;
  margin-left: 24px;
  padding: 16px 10px;
  border-radius: 12px;
  background: #fafbfa;
  box-shadow: 0 2px 10px rgba(150,180,130,0.10);
  color: #23560e;
  font-size: 1.05rem;
  font-weight: 500;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
`;

const InfoLabel = styled.div`
  font-size: 13px;
  color: #87967b;
  margin-bottom: 2px;
`;

const InfoValue = styled.div`
  font-size: 19px;
  font-weight: 600;
  color: #3c7321;
`;

const LinePath = styled.polyline`
  stroke: #6a9b3e;
  stroke-width: 2.5;
  fill: none;
`;

const AreaPath = styled.path`
  fill: url(#area-gradient);
`;

function formatKoreanDate(str: string) {
    // YYYY-MM-DD → YYYY년 MM월 DD일
    if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
        const [y, m, d] = str.split('-');
        return `${y}년 ${m}월 ${d}일`;
    }
    return str;
}


const SvgGraph: React.FC<SvgGraphProps> = ({ data }) => {
    const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

    const svgWidth = 300;
    const svgHeight = 110;    // 기존 100 → 110(또는 120)
    const xPadding = 20;
    const topPadding = 8;
    const bottomPadding = 8;

    if (!data || data.length === 0) return null;

    const scores = data.map((d) => d.score);
    const rawMin = Math.min(...scores);
    const rawMax = Math.max(...scores);
    const scoreMin = Math.max(0, rawMin - 5);
    const scoreMax = Math.min(100, rawMax + 5);
    const range = scoreMax - scoreMin || 1;


    const getCoords = (score: number, index: number, total: number) => {
        const x = xPadding + ((svgWidth - 2 * xPadding) * index) / (total - 1 || 1);
        const y = topPadding + ((scoreMax - score) / range) * (svgHeight - topPadding - bottomPadding);
        return { x, y };
    };

    const points = data.map((d, i) => {
        const { x, y } = getCoords(d.score, i, data.length);
        return `${x},${y}`;
    }).join(" ");

    const areaPoints = `M ${xPadding},${svgHeight} L ${points} L ${svgWidth - xPadding},${svgHeight} Z`;

    // 1. hover 또는 마지막 점(default) 선택
    const displayIdx = hoveredIdx ?? data.length - 1;
    const displayData = data[displayIdx];
    const displayLabelRaw = displayData.record_date || displayData.day || `Day ${displayIdx + 1}`;
    const displayLabel = formatKoreanDate(displayLabelRaw);
    const displayScore = `${Math.round(displayData.score)}점`;


    return (
        <GraphContainer>
            <StyledSvg viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="none">
                <defs>
                    <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6a9b3e" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#6a9b3e" stopOpacity="0" />
                    </linearGradient>
                </defs>
                <AreaPath d={areaPoints} />
                <LinePath points={points} />

                {data.map((d, i) => {
                    const { x, y } = getCoords(d.score, i, data.length);
                    return (
                        <g key={i}
                            onMouseEnter={() => setHoveredIdx(i)}
                            onMouseLeave={() => setHoveredIdx(null)}
                            style={{ cursor: "pointer" }}>
                            <circle cx={x} cy={y} r="8" fill="transparent" />
                            <circle cx={x} cy={y} r="3.5" fill={i === displayIdx ? "#35651a" : "#6a9b3e"} />
                        </g>
                    );
                })}
            </StyledSvg>

            <InfoPanel>
                <InfoLabel>날짜</InfoLabel>
                <InfoValue>{displayLabel}</InfoValue>
                <InfoLabel>점수</InfoLabel>
                <InfoValue>{displayScore}</InfoValue>
            </InfoPanel>
        </GraphContainer>
    );
};

export default SvgGraph;
