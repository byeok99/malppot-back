// src/hooks/useNavigator.js
import { useNavigate } from "react-router-dom";

export const useNavigator = () => {
    const navigate = useNavigate();

    return {
        goBack: () => navigate(-1),
        goHome: () => navigate("/"),
        goMalbeot: () => navigate("/malbeot"),
        goSpeech: (word: string = "") => navigate("/speech", { state: { defaultText: word } }),
        goGame: () => navigate("/game"),
        goAuth: () => navigate("/auth"),
        goMy: () => navigate("/my")
    };
};