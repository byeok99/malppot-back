export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export const API: Record<string, string> = {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    MYPAGE: '/mypage/data',
    MYPAGE_SUMMARY: '/mypage/summary',
    MYPAGE_PHONEME: '/mypage/phoneme',
    MYPAGE_REPORT: 'mypage/report',
    AIMALBEOT: '/malbeot/ws',
    SPEECH_CONVERT: '/speech/convert',
    SPEECH_EVALUATE: '/speech/evaluate',
    SPEECH_GENERATE_VIDEO: '/heygen/generate-video',
    SPEECH_GET_VIDEO_BY_ID: '/heygen/videos',
    GAME_BULK: '/game/evaluate/bulk',
    GAME_WORDS: '/game/words',
    GAME_STAGE_HIGHEST: '/game/highest-cleared',
    GAME_STAGES: '/game/stages',
    GAME_CLEAR: '/game/clear',
    GAME_BEST_SCORE: 'game/best-score',
    GAME_ENDLESS: 'game/endless',
    SPEECH_SYLLABLE: 'speech/syllable'
};

export const ROUTES: Record<string, string> = {
    HOME: "/",
    MY: "/my",
    AUTH: "/login",
    MALBEOT: "/malbeot",
    SPEECH: "/speech",
    GAME: "/game",
};