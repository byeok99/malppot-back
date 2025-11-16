import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { GoogleOAuthProvider } from '@react-oauth/google'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import store from 'store/index';
import { ChatProvider } from 'utils/ChatContext';

import GlobalStyle from 'components/GlobalStyle';
import Layout from 'components/layout/Layout';
import Home from 'pages/homePage/Home';
import Auth from 'pages/authPage/Auth';
import Loading from 'pages/authPage/Loading';
import Malbeot from 'pages/malbeotPage/Malbeot';
import Speech from 'pages/speechPage/Speech';
import My from "pages/myPage/MyPage";
import Game from "pages/gamePage/GamePage";


const queryClient = new QueryClient();

const Router = () => {
    return (
        <Routes>
            <Route element={<Layout />}>
                <Route path="/" element={<Home />} />
                <Route path="/auth" element={<Auth />} />
                <Route path="/loading" element={<Loading />} />
                <Route path="/malbeot" element={<Malbeot />} />
                <Route path="/speech" element={<Speech />} />
                <Route path="/my" element={<My />} />
                <Route path="/game" element={<Game />} />
            </Route>
        </Routes>
    )
}
createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <Provider store={store}>
            <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_AUTH_CLIENT_ID}>
                <QueryClientProvider client={queryClient}>
                    <ChatProvider>
                        <BrowserRouter>
                            <GlobalStyle />
                            <Router />
                        </BrowserRouter>
                    </ChatProvider>
                </QueryClientProvider>
            </GoogleOAuthProvider>
        </Provider>
    </StrictMode>
)
