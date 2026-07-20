import api from 'apis/apiClient';
import { API } from 'config';
import { ConvertResponse, EvaluationResponse, GenerateVideoResponse, SyllableDetail } from 'types/speech'

const speechApis = {
    convert: (input: string) =>
        api.post<ConvertResponse>(
            API.SPEECH_CONVERT,
            { input_text: input },
            { withCredentials: true }
        ),

    evaluate: (formData: FormData) =>
        api.post<EvaluationResponse>(
            API.SPEECH_EVALUATE,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
                withCredentials: true,
            }
        ),

    evaluateBulk: (formData: FormData) =>
        api.post<EvaluationResponse>(
            API.GAME_BULK,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
                withCredentials: true,
            }
        ),

    generateVideo: (input: string) =>
        api.post<GenerateVideoResponse>(
            API.SPEECH_GENERATE_VIDEO,
            { text: input },
            { withCredentials: true }
        ),

    getVideoById: (video_id: string) =>
        api.get(`${API.SPEECH_GET_VIDEO_BY_ID}/${video_id}`),

    getSyllableDetail: (char: string) =>
        api.get<SyllableDetail>(`${API.SPEECH_SYLLABLE}/${encodeURIComponent(char)}`),

};

export default speechApis;