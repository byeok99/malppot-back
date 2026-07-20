/** ---------- 공통 ---------- */
export interface Accuracy {
    previous: number;
    current: number;
}

export interface GraphData {
    record_date: string;   // YYYY-MM-DD
    score: number;
}

/** ---------- 1. 기존 구조 그대로 유지 ---------- */
export interface UserData {
    userName: string;
    profileImageUrl: string | null;
    practiceStreak: number;
    totalPracticeCount: number;
    accuracy: Accuracy;
}

export interface PhonemeAccuracy {
    [phoneme: string]: number;   // ex) 'ㄱ': 92
}

export interface DetailedAnalysisItem {
    id: string;
    word: string;
    phoneme: string;
    accuracy: number;
    mainErrorType: string;   // '생략' | '첨가' | '왜곡' | '없음'
    history: number[];       // 과거 점수 추이
}

/** ---------- 2. 변경: 오류 분포 ---------- */
export interface ErrorDistribution {
    /** 퍼센트 값 (0~100) */
    생략: number;
    첨가: number;
    왜곡: number;
    없음: number;
}


/** ---------- 3. 신규: phonemeDetailedAnalysis ---------- */
export interface ErrorTendency {
    omission?: number;     // 생략 %
    insertion?: number;    // 첨가 %
    distortion?: number;   // 왜곡 %
    none?: number;         // 없음 % (거의 0 이지만 포함)
}

export interface PhonemePositionAnalysis {
    averageAccuracy: number;            // 해당 위치 평균
    errorTendency: ErrorTendency;       // 오류 비율
}

export interface MyPageResponse {
    userData: UserData;
    graphData: GraphData[];
    phonemeAccuracy: PhonemeAccuracy;
    tenseConsonants: PhonemeAccuracy;
    detailedAnalysis: DetailedAnalysisItem[];

    /** NEW: 자음별 상세 분석 (backend key: phonemeDetailedAnalysis) */
    phonemeDetailedAnalysis: { [phoneme: string]: PhonemeAnalysis };
}


export interface AnalysisReportProps {
    data: PhonemeAnalysis | null;
    onPractice: (word: string) => void;
    selectedPhoneme: string;
}

export interface DetailedRecord {
    id: string | number;
    word: string;
    accuracy: number;
    mainErrorType: string;
    history: number[];
}

export interface PositionalStat {
    averageAccuracy: number;
    errorTendency: ErrorTendency;
}

export interface PositionalAnalysis {
    initial?: PositionalStat | null;
    final?: PositionalStat | null;
    초성?: PositionalStat | null;
    종성?: PositionalStat | null;
    [key: string]: PositionalStat | null | undefined;   // 인덱스 시그니처 추가
}

export interface PhonemeAnalysis {
    overallAccuracy: number;
    positionalAnalysis: PositionalAnalysis;
    recommendedWords: { word: string; sentence: string; }[];
    allRecords: DetailedRecord[];
}

export type PhonemeDetailedAnalysis = Record<string, PhonemeAnalysis>;

// src/types/mypage.ts
export interface SummaryResponse {
    userData: UserData;
    graphData: GraphData[];
    phonemeAccuracy: PhonemeAccuracy;      // 일반 자음
    tenseConsonants: PhonemeAccuracy;      // 된소리
}

export interface PhonemeDetailResponse {
    // 기존 phonemeDetailedAnalysis[phoneme] 과 같음
    allRecords: DetailedRecord[];
    positionalAnalysis: PositionalAnalysis;
    recommendedWords: { word: string; sentence: string; }[];
}

export interface ErrorTypeStat {
    error_type?: string | null;
    count: number;
    percent: number;
}

// JamoDetail 타입
export interface JamoDetail {
    phoneme: string;               // 자음
    position: string;              // 초성/종성 등 위치
    average_score?: number | null;
    total_attempts: number;
    error_types: ErrorTypeStat[];
}

export interface AttentionPhoneme {
    phoneme: string;
    position: string;
    accuracy: number;
}

export interface PatientReport {
    name: string;
    total_practice_count: number;
    practice_streak: number;
    overall_accuracy: number;
    consonant_scores: Record<string, number>;       // ex: { "ㄱ": 0.92, ... }
    seven_day_accuracy_trend: number[];             // ex: [0.93, 0.92, ...]
    attention_phonemes: AttentionPhoneme[];
    jamo_detail: JamoDetail[];
}