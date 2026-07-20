export const getScoreColor = (score: number): string => {
    if (score >= 80) return "#27ae60";
    if (score >= 60) return "#f39c12";
    return "#e74c3c";
};