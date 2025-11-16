import { AxiosRequestConfig, AxiosResponse } from 'axios';
import axiosInstance from 'apis/axiosInstance';

const api = {
    get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return axiosInstance.get<T>(url, config);
    },

    post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return axiosInstance.post<T>(url, data, config);
    },

    put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return axiosInstance.put<T>(url, data, config);
    },

    delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
        return axiosInstance.delete<T>(url, config);
    },
};

export default api;