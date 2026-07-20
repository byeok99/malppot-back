import axios, { InternalAxiosRequestConfig, AxiosRequestConfig, AxiosError } from 'axios';
import { BASE_URL, API } from 'config';
import store from 'store/index';
import { RootState } from 'store/index';

interface RefreshResponse {
    access_token: string;
}

const axiosInstance = axios.create({
    baseURL: BASE_URL,
    timeout: 60000,
    headers: {
        'Content-Type': 'application/json',
    },
});

axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = (store.getState() as RootState).auth.accessToken;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    if (config.data instanceof FormData) {
        delete config.headers['Content-Type'];
    }
    return config;
});

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // refresh 자체가 실패한 경우 → 로그아웃
        if (originalRequest.url === API.REFRESH) {
            console.error('🔁 Refresh 요청 실패 → 강제 로그아웃'); // [수정] 오류 메시지 한글로 통일
            store.dispatch({ type: 'auth/clearAccessToken' });
            return Promise.reject(error);
        }

        // accessToken 만료 시 → refresh 토큰으로 재시도
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshResponse = await axiosInstance.post<RefreshResponse>(
                    API.REFRESH,
                    {},
                    { withCredentials: true }
                );
                const newAccessToken = refreshResponse.data.access_token;
                store.dispatch({ type: 'auth/setAccessToken', payload: newAccessToken });

                if (originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                }

                return axiosInstance(originalRequest);
            } catch (refreshError) {
                console.error('❌ 토큰 재발급 실패:', refreshError); // [수정] 오류 메시지 한글로 통일
                store.dispatch({ type: 'auth/clearAccessToken' });
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default axiosInstance;