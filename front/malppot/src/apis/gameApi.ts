import api from 'apis/apiClient';
import { API } from 'config';
import type {
    EvaluationResponse,
    WordsResponse,
    HighestStageRes,
    StageData,
    CompleteStageRes,
} from 'types/game';

const gameApis = {
    /* ① 발음 평가 (bulk) */
    evaluateBulk: (formData: FormData) =>
        api.post<EvaluationResponse>(API.GAME_BULK, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            withCredentials: true,
        }),

    /* ② 무한 모드 단어 풀 */
    getEndlessWords: () =>
        api.post<WordsResponse>(API.GAME_WORDS, {}, { withCredentials: true }),

    /* ③ 최고 클리어 스테이지 번호 */
    getHighestClearedStage: () =>
        api.get<HighestStageRes>(API.GAME_STAGE_HIGHEST, { withCredentials: true }),

    /* ④ 특정 스테이지 상세 */
    getStages: () =>
        api.get<StageData[]>(`${API.GAME_STAGES}`, {
            withCredentials: true,
        }),

    /* ⑤ 스테이지 클리어(점수 저장) */
    clearStage: (stageId: number) =>
        api.post<CompleteStageRes>(
            `${API.GAME_CLEAR}`,
            { stage_id: stageId },
            { withCredentials: true }
        ),

    saveEndlessBestScore: ({ newScore }: { newScore: number; }) =>
        api.post(
            `${API.GAME_ENDLESS}`,
            { new_score: newScore },
            { withCredentials: true }
        ),

    getBestScore: () =>
        api.get<number>(
            API.GAME_BEST_SCORE,
            { withCredentials: true }
        ),

};

export default gameApis;
