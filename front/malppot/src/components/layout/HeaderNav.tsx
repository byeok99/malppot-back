import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom"; // NavLink 대신 useNavigate 사용
import { useNavigator } from "hooks/useNavigator";
import styles from './HeaderNav.module.css';
import Modal from "components/common/Modal";
import { ROUTES } from 'config';

import malbeotIcon from 'assets/icons/malbeot_icon.svg';
import speechIcon from 'assets/icons/speech_icon.svg';
import gameIcon from 'assets/icons/game_icon.svg';

interface HeaderNavProps {
    isLogin: boolean;
}
const HeaderNav: React.FC<HeaderNavProps> = ({ isLogin }) => {
    const { goAuth } = useNavigator();
    const navigate = useNavigate();
    const location = useLocation(); // useLocation 훅 추가
    const [isModalOpen, setIsModalOpen] = useState(false);

    // 클릭 시 로그인 상태 확인 → 미로그인시 모달, 로그인시 이동
    const handleNavClick = (route: string, requireLogin = false) => {
        if (requireLogin && !isLogin) {
            setIsModalOpen(true);
        } else {
            navigate(route);
        }
    };

    const handleConfirmAndLogin = () => {
        setIsModalOpen(false);
        goAuth();
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    return (
        <nav className={styles.navContainer}>
            {isModalOpen && (
                <Modal
                    message="로그인이 필요한 서비스입니다. 로그인 하시겠습니까?"
                    onConfirm={handleConfirmAndLogin}
                    onCancel={handleCancel}
                />
            )}
            <div
                className={`${styles.styledNavLink} ${location.pathname === ROUTES.MALBEOT ? styles.active : ''}`}
                onClick={() => handleNavClick(ROUTES.MALBEOT, true)}
            >
                <img src={malbeotIcon} alt="말벗" className={styles.navIcon} />
                <span className={styles.navText}>AI 말벗</span>
            </div>
            <div
                className={`${styles.styledNavLink} ${location.pathname === ROUTES.SPEECH ? styles.active : ''}`}
                onClick={() => handleNavClick(ROUTES.SPEECH, true)}
            >
                <img src={speechIcon} alt="말소리" className={styles.navIcon} />
                <span className={styles.navText}>말소리 연습실</span>
            </div>
            <div
                className={`${styles.styledNavLink} ${location.pathname === ROUTES.GAME ? styles.active : ''}`}
                onClick={() => handleNavClick(ROUTES.GAME, true)}
            >
                <img src={gameIcon} alt="게임" className={styles.navIcon} />
                <span className={styles.navText}>발음 게임</span>
            </div>
            {isLogin && (
                <div
                    className={`${styles.styledNavLink} ${location.pathname === ROUTES.MY ? styles.active : ''} ${styles.mypage}`}
                    onClick={() => handleNavClick(ROUTES.MY, true)}
                >
                    <span className={styles.navText}>마이페이지</span>
                </div>
            )}
        </nav>
    );
};

export default HeaderNav;
