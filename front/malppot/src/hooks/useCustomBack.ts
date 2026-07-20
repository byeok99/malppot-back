import { useEffect } from 'react';

function useCustomBack(customBack: () => void) {
    useEffect(() => {
        // history 스택에 현재 페이지를 강제로 하나 추가(뒤로가도 현재 페이지 유지)
        history.pushState(null, '', location.href);

        // popstate 핸들러는 반드시 함수로 선언!
        const onPopState = () => {
            // history를 다시 push해서 앞으로 못 나가게 고정
            history.pushState(null, '', location.href);
            customBack();
        };

        window.addEventListener('popstate', onPopState);

        return () => {
            window.removeEventListener('popstate', onPopState);
        };
    }, [customBack]);
}

export default useCustomBack;
