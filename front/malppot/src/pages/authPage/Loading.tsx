import React, { useEffect } from "react";
import { useDispatch } from "react-redux"; //useSelector
import { setAccessToken, setUserInfo } from "store/authSlice";
import { useNavigator } from 'hooks/useNavigator';
import styled from "styled-components";
import authApis from "apis/authApi";
// import { RootState } from "store/index"; // RootState 경로 확인

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
`;

const H2 = styled.h2`
  font-size: 18px;
  color: #444;
`;

const Loading = (): React.JSX.Element => {
    const dispatch = useDispatch();

    const { goHome } = useNavigator();
    const handleHome = () => {
        goHome();
        window.location.reload();
    };

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    const handleLoginPost = async (code: string) => {
        try {
            const res = await authApis.login({ code });
            const access_token = res.data.access_token;
            const { name, email, profile_image_url } = res.data.user_info;
            localStorage.setItem("accessToken", access_token);
            dispatch(setAccessToken(access_token));
            dispatch(setUserInfo({ name, email, profile_image_url }));

            handleHome();
        } catch (error) {
            alert("운영 준비중입니다.");
            handleHome();
        }
    };

    useEffect(() => {
        if (code) {
            handleLoginPost(code);
        } else {
            console.warn("code가 없습니다. 로그인 재시도 필요.");
        }
    }, [code]);

    return (
        <LoadingContainer>
            <H2>로그인중입니다...</H2>
        </LoadingContainer>
    );
};

export default Loading;