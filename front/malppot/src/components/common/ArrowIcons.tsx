// src/components/common/ArrowIcons.tsx
import React from 'react';

export const UpArrowIcon = (): React.JSX.Element => (
    <svg
        className="arrow-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#27ae60"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        {" "}
        <path d="M12 19V5M5 12l7-7 7 7" />{" "}
    </svg>
);

export const DownArrowIcon = (): React.JSX.Element => (
    <svg
        className="arrow-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#e74c3c"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        {" "}
        <path d="M12 5v14M19 12l-7 7-7-7" />{" "}
    </svg>
);