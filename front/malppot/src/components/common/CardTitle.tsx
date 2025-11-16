// src/components/common/CardTitle.tsx
import React from 'react';
import styled from 'styled-components';

interface CardTitleProps {
    title: string;
    tooltipText: string;
}

const TitleWrapper = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    h3 {
        margin: 0;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.2rem;
        color: #6a9b3e;
        font-weight: 600;
    }
`;

const TooltipContainer = styled.div`
    position: relative;
    display: inline-block;
    z-index: 10;

    .tooltip-text {
        visibility: hidden;
        width: 280px;
        background-color: #f8fafb;
        color: #212529;
        text-align: center;
        border-radius: 8px;
        padding: 10px;
        position: absolute;
        z-index: 10;
        bottom: 125%;
        left: 50%;
        margin-left: -140px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.85rem;
        font-weight: 500;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    .tooltip-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #6a9b3e transparent transparent transparent;
    }
    &:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
`;

const InfoIcon = styled.span`
    cursor: help;
    color: #6a9b3e;
    font-weight: bold;
    font-size: 1.1rem;
    border: 1.5px solid #a6d785;
    background-color: #f8fbf6;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    line-height: 1;
    transition: all 0.2s;
    &:hover {
        background-color: #eef7e9;
        border-color: #6a9b3e;
    }
`;

const CardTitle = ({ title, tooltipText }: CardTitleProps): React.JSX.Element => (
    <TitleWrapper>
        <h3>{title}</h3>
        <TooltipContainer>
            <InfoIcon>i</InfoIcon>
            <span className="tooltip-text">{tooltipText}</span>
        </TooltipContainer>
    </TitleWrapper>
);

export default CardTitle;