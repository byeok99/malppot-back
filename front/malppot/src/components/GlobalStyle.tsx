import { createGlobalStyle } from "styled-components";

const GlobalStyle = createGlobalStyle`
    *, *::before, *::after {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    html {
        font-size: 80%; /* UI 전체 배율 조정 */
    }

    body {
        // overflow: hidden;
        height: 100vh;
        background-color: #f7f8f9; 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        background: linear-gradient(135deg, #f9f9f9 0%, #e8f5e9 100%);
    }
`;

export default GlobalStyle;
