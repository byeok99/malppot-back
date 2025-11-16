import { WordFeedback } from 'types/speech'

export type WordsResponse = { words: string[] };

interface StageWord {
    word: string;
    image_url: string;
}

export interface EvaluationResponse {
    session_id: string;
    reference_text: string;
    scores: number;
    feedback: WordFeedback[];
}

export interface StageData {
    id: number;
    level: number;
    difficulty: 'EASY' | 'NORMAL' | 'HARD';
    goalValue: number;
    speed: number;
    interval: number;
    lives: number;
    words: StageWord[];
}

export interface HighestStageRes {
    highestClearedStage: number;   // 예: 7 (없으면 1)
}

// export type StageDataRes = StageData;

export interface CompleteStageRes {
    bestScore: number;  // 갱신된 최고 점수
    cleared: boolean;   // true = 이번에 목표 달성
}