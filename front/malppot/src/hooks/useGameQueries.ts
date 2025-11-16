import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import gameApis from 'apis/gameApi';

interface CompleteStagePayload {
    stageId: number;
}

interface SaveEndlessScorePayload {
    newScore: number;
}

export const useEndlessWords = (enabled = true) =>
    useQuery({
        queryKey: ['endlessWords'],
        queryFn: () => gameApis.getEndlessWords().then(res => res.data),
        select: data => Array.isArray(data) ? data : data.words ?? [],
        staleTime: 5 * 60 * 1000,
        enabled, // 호출 시점에만 수동으로 사용
        retry: 1, // 1번만 재시도
        retryDelay: 1000, // 1초 후 재시도
    });

export const useHighestClearedStage = (enabled = false) =>
    useQuery({
        queryKey: ['highestClearedStage'],
        queryFn: () => gameApis.getHighestClearedStage().then(r => r.data),
        select: (data: any) =>
            typeof data === 'number' ? data : data.highest_stage ?? 1,
        staleTime: 5 * 60 * 1000,
        enabled,
    });

export const useStages = (enabled = true) =>
    useQuery({
        queryKey: ['stagesData'],
        enabled,
        queryFn: () => gameApis.getStages().then(r => r.data),
        staleTime: 5 * 60 * 1000,
    });

export const useCompleteStage = () => {
    const qc = useQueryClient();

    return useMutation({
        mutationFn: ({ stageId }: CompleteStagePayload) =>
            gameApis.clearStage(stageId).then(r => r.data),

        onSuccess: (_data, variables) => {
            qc.invalidateQueries({ queryKey: ['highestClearedStage'] });
            qc.invalidateQueries({ queryKey: ['stageData', variables.stageId] });
        },
    });
};

export const useSaveEndlessScore = () => {
    return useMutation({
        mutationFn: (payload: SaveEndlessScorePayload) =>
            gameApis.saveEndlessBestScore(payload),
    });
};


export const useBestScore = (enabled = true) =>
    useQuery({
        queryKey: ['bestScore'],
        enabled,
        queryFn: () => gameApis.getBestScore().then(r => r.data),
        staleTime: 5 * 60 * 1000,
    });
