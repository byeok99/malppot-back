// src/hooks/useSyllableDetail.ts
import { useQuery } from '@tanstack/react-query';
import speechApis from 'apis/speechApi';
import { SyllableDetail } from 'types/speech';

export const useSyllableDetail = (char: string | null) => {
    return useQuery<SyllableDetail, Error>({
        queryKey: ['syllable', 'detail', char],
        enabled: !!char, // char가 null/빈값이면 fetch 안함
        queryFn: () => speechApis.getSyllableDetail(char!).then(r => r.data),
        staleTime: 30 * 1000, // 30초마다 fresh
        retry: 1,
    });
};
