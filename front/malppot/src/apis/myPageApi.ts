import api from 'apis/apiClient';
import { API } from 'config';

const myApis = {
    getMypageData: () => api.get(API.MYPAGE),
    getSummary: () => api.get(API.MYPAGE_SUMMARY),
    getPhonemeDetail: (phoneme: string) =>
        api.get(`${API.MYPAGE_PHONEME}/${encodeURIComponent(phoneme)}`),
    getReport: () => api.get(API.MYPAGE_REPORT)
}

export default myApis;