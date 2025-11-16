import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AuthState {
    accessToken: string | null;
    name: string | null;
    email: string | null;
    profile_image_url: string | null;
}

const initialState: AuthState = {
    accessToken: localStorage.getItem("accessToken"),
    name: localStorage.getItem("userName"),
    email: localStorage.getItem("userEmail"),
    profile_image_url: localStorage.getItem("profile_image_url")
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        setAccessToken: (state, action: PayloadAction<string>) => {
            state.accessToken = action.payload;
            localStorage.setItem("accessToken", action.payload);
        },
        setUserInfo: (
            state,
            action: PayloadAction<{ name: string; email: string; profile_image_url: string | null }>
        ) => {
            state.name = action.payload.name;
            state.email = action.payload.email;
            state.profile_image_url = action.payload.profile_image_url;

            localStorage.setItem("userName", action.payload.name);
            localStorage.setItem("userEmail", action.payload.email);
            
            if (action.payload.profile_image_url) {
                localStorage.setItem("profile_image_url", action.payload.profile_image_url);
            } else {
                localStorage.removeItem("profile_image_url");
            }
        },
        clearAccessToken: (state) => {
            state.accessToken = null;
            state.name = null;
            state.email = null;
            state.profile_image_url = null;

            localStorage.removeItem("accessToken");
            localStorage.removeItem("userName");
            localStorage.removeItem("userEmail");
            localStorage.removeItem("profile_image_url");
        },
    },
});

export const { setAccessToken, setUserInfo, clearAccessToken } = authSlice.actions;
export default authSlice.reducer;