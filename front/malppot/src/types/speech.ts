export interface ConvertResponse {
    converted_text: string;
}

export interface GenerateVideoResponse {
    video_id: string;
}

export interface SyllableDetail {
    char: string;
    tongue_url: string[];
    lips_url: string[];
    gpt_tip: string;
}

export interface WordFeedback {
    word: string;
    average_score: number;
    errtype: string;
    syllables: SyllableDetail[];
    video_url: string | null;
}

export interface EvaluationResponse {
    session_id: string;
    reference_text: string;
    scores: number;
    feedback: WordFeedback[];
}