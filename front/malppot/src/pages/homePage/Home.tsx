import React, { useState } from "react";
import { useSelector } from "react-redux";
import { useNavigator } from "hooks/useNavigator";
import Modal from "components/common/Modal";
import styles from "./Home.module.css";
import { RootState } from "store";
import malbeot_icon from "assets/icons/malbeot_icon.svg";
import speech_icon from "assets/icons/speech_icon.svg";
import game_icon from "assets/icons/game_icon.svg";

const Home: React.FC = () => {
    const { goMalbeot, goSpeech, goAuth, goGame } = useNavigator();
    const accessToken = useSelector((state: RootState) => state.auth.accessToken);
    const isLogin = !!accessToken;
    const userName = useSelector((state: RootState) => state.auth.name);

    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleNavigate = (destination: () => void) => {
        if (isLogin) {
            destination();
        } else {
            setIsModalOpen(true);
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
        <div className={styles.container}>
            {isModalOpen && (
                <Modal
                    message="로그인이 필요한 서비스입니다. 로그인 하시겠습니까?"
                    onConfirm={handleConfirmAndLogin}
                    onCancel={handleCancel}
                />
            )}

            <div className={styles.headerSection}>
                <h1 className={styles.title}>
                    {isLogin ? (
                        <>
                            <span className={styles.highlight}>{userName}님</span>, 안녕하세요!
                        </>
                    ) : (
                        <>
                            모두의 <span className={styles.highlight}>말</span>이<br />
                            세상에 <span className={styles.highlight}>뻗</span>어나갈 수 있도록.
                        </>
                    )}
                </h1>
                <p className={styles.subtitle}>
                    {isLogin
                        ? "오늘도 말뻗과 함께 자신감 있는 소통을 연습해봐요."
                        : "AI 기반 조음 훈련 서비스, [말:뻗]"}
                </p>
            </div>

            <div className={styles.coreFeaturesGrid}>
                <div className={styles.card} onClick={() => handleNavigate(goMalbeot)}>
                    <img
                        src={malbeot_icon}
                        alt="AI 말벗"
                        className={styles.cardImage}
                    />
                    <h2 className={styles.cardTitle}>AI 말벗</h2>
                    <p className={styles.cardDescription}>
                        실제 사람과 대화하듯, AI와 자유롭게 이야기하며 자연스러운 소통을
                        연습해요.
                    </p>
                    <button className={styles.cardButton}>대화 시작하기</button>
                </div>

                <div className={styles.card} onClick={() => handleNavigate(goSpeech)}>
                    <img
                        src={speech_icon}
                        alt="말소리 연습실"
                        className={styles.cardImage}
                    />
                    <h2 className={styles.cardTitle}>말소리 연습실</h2>
                    <p className={styles.cardDescription}>
                        원하는 문장을 따라 말하고, AI의 실시간 피드백과 혀 위치 가이드로
                        발음을 교정해요.
                    </p>
                    <button className={styles.cardButton}>연습 시작하기</button>
                </div>

                <div className={styles.card} onClick={() => handleNavigate(goGame)}>
                    <img
                        src={game_icon}
                        alt="발음 게임"
                        className={styles.cardImage}
                    />
                    <h2 className={styles.cardTitle}>발음 게임</h2>
                    <p className={styles.cardDescription}>
                        재미있는 게임을 통해 어려운 발음을 정복하고<br />정확한 조음 능력을 길러보세요!
                    </p>
                    <button className={styles.cardButton}>연습 시작하기</button>
                </div>
            </div>
            <div className={styles.infoBanner}>
                <span className={styles.emoji}>🎧</span>
                <span>
                    최적의 환경을 위해 <strong>이어폰 마이크</strong> 사용과 <strong>Chrome 브라우저</strong> 이용을 권장합니다.
                </span>
            </div>
        </div>
    );
};

export default Home;
