import { useQuery } from '@tanstack/react-query';

import {
    SummaryResponse,
    PhonemeDetailResponse,
    PatientReport
} from 'types/mypage';

import myPageApi from 'apis/myPageApi';

export const useMyPageSummary = () => {
    return useQuery<SummaryResponse, Error>({
        queryKey: ['mypage', 'summary'],
        queryFn: () => myPageApi.getSummary().then(r => r.data),
        staleTime: 5 * 60 * 1000,
    });
};

export const usePhonemeDetail = (phoneme: string | null) => {
    return useQuery<PhonemeDetailResponse, Error>({
        queryKey: ['mypage', 'phoneme', phoneme],
        queryFn: () => myPageApi.getPhonemeDetail(phoneme!).then(r => r.data),
        staleTime: 10 * 60 * 1000,
    });
};

export const usePatientReport = () => {
    return useQuery<PatientReport, Error>({
        queryKey: ['mypage', 'report'],
        queryFn: () => myPageApi.getReport().then(r => r.data),
        enabled: false, // 자동 fetch 비활성화
    });
};