import api from 'apis/apiClient';
import { API } from 'config';
import { AxiosResponse } from 'axios';

interface LoginParams {
  code: string;
}

interface LoginResponse {
  access_token: string;
  user_info: {
    name: string;
    email: string;
    profile_image_url: string;
  };
}

const authApis = {
  login: (params: LoginParams): Promise<AxiosResponse<LoginResponse>> =>
    api.post<LoginResponse>(API.LOGIN, params, { withCredentials: true }),

  refresh: (): Promise<AxiosResponse<LoginResponse>> =>
    api.post<LoginResponse>(API.REFRESH, {}, { withCredentials: true }),

  logout: (): Promise<AxiosResponse<void>> =>
    api.post<void>(API.LOGOUT, {}, { withCredentials: true }),
};

export default authApis;