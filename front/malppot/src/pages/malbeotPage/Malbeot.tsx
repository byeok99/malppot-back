import React, { useState, useRef, useEffect, ReactElement } from "react";
import { useSelector } from "react-redux";
import { RootState } from "store";
import { useNavigator } from "hooks/useNavigator";
import Modal from "components/common/Modal";
import CharacterRenderer from "components/malbeot/CharacterRenderer";
import { useChat } from "utils/ChatContext";
import AudioChatController from "components/malbeot/AudioChatController";
import styles from "./Malbeot.module.css";
import { LuMessageCircleQuestion, LuMessagesSquare } from "react-icons/lu";
import { MdArrowBack } from "react-icons/md";
import useCustomBack from "hooks/useCustomBack"


interface AudioChatControllerHandle {
    startAudio: () => Promise<void>;
    stopAudio: () => Promise<void>;
}

const getCurrentTime = (): string => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    return `${hours}:${minutes}`;
};
const FeedbackIcon = (): ReactElement => <LuMessageCircleQuestion className="icon" size={48} />;
const GeneralIcon = (): ReactElement => <LuMessagesSquare className="icon" size={48} />;

type ViewState = "mode_selection" | "chatting" | "summary";
type ChatMode = "feedback" | "general" | null;

const Malbeot: React.FC = () => {
    const { goAuth } = useNavigator();
    const accessToken = useSelector((state: RootState) => state.auth.accessToken);

    const [isStarted, setIsStarted] = useState<boolean>(false);
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
    const { messages, addMessage, clearMessages } = useChat();
    const [viewState, setViewState] = useState<ViewState>("mode_selection");
    const [chatMode, setChatMode] = useState<ChatMode>(null);
    const audioControllerRef = useRef<AudioChatControllerHandle | null>(null);
    const chatEndRef = useRef<HTMLDivElement | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        if (!accessToken) {
            setIsModalOpen(true);
        }
    }, [accessToken]);

    const handleConfirmAndLogin = () => {
        setIsModalOpen(false);
        goAuth();
    };

    const handleCancel = () => {
        setIsModalOpen(false);
        // 모달 닫기 외에 다른 동작이 필요하다면 여기에 추가
    };

    const handleModeSelect = (mode: ChatMode) => {
        if (!mode) return;
        clearMessages();
        setChatMode(mode);
        setViewState("chatting");
        setIsStarted(false); // 모드 선택 시 isStarted 초기화
    }

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleStart = async (): Promise<void> => {
        alert("운영 준비 중입니다.")
        return;
        if (!isStarted) {
            clearMessages();
            await audioControllerRef.current?.startAudio();
            setIsStarted(true);
            addMessage("system", `대화가 시작되었습니다 (${getCurrentTime()})`);
        } else {
            await audioControllerRef.current?.stopAudio();
            setIsStarted(false);
            addMessage("system", `대화가 종료되었습니다 (${getCurrentTime()})`);
        }
    };

    useCustomBack(() => {
        if (isStarted) {
            audioControllerRef.current?.stopAudio();
            setIsStarted(false);
            setViewState("mode_selection");
            setChatMode(null);
            clearMessages();
            // 필요하다면 alert("대화가 종료되었습니다");
        }
    })

    const renderContent = () => {
        switch (viewState) {
            case "chatting":
                return (
                    <div className={styles.pageWrapper}>
                        <div className={styles.topBar}>
                            <button
                                className={styles.backButton}
                                onClick={() => {
                                    setIsStarted(false);
                                    setViewState("mode_selection");
                                    setChatMode(null);
                                    clearMessages();
                                    // 만약 대화가 시작된 상태라면 audio도 멈춤
                                    audioControllerRef.current?.stopAudio();
                                }}
                                aria-label="뒤로가기"
                            >
                                <MdArrowBack size={28} />
                            </button>
                        </div>
                        <section className={styles.characterSection}>
                            <CharacterRenderer isSpeaking={isSpeaking} />
                            <button className={styles.startButton} onClick={handleStart}>
                                {isStarted ? "대화 종료하기" : "대화 시작하기"}
                            </button>
                        </section>

                        <section className={styles.chatSection}>
                            <div className={styles.chatMessages}>
                                {messages.length === 0 && (
                                    <div className={styles.systemMessage}>
                                        아래 버튼을 눌러 대화를 시작해보세요.
                                    </div>
                                )}
                                {messages.map((msg, idx) => {
                                    if (msg.speaker === "system") {
                                        return (
                                            <div key={idx} className={styles.systemMessage}>
                                                {msg.transcript}
                                            </div>
                                        );
                                    }
                                    return (
                                        <div
                                            key={idx}
                                            className={`${styles.messageRow} ${msg.speaker === "user" ? styles.user : styles.model}`}
                                        >
                                            <div className={`${styles.messageBubble} ${msg.speaker === "user" ? styles.user : styles.model}`}>
                                                {msg.transcript}
                                            </div>
                                        </div>

                                    );
                                })}
                                <div ref={chatEndRef} />
                            </div>
                        </section>

                        <AudioChatController
                            ref={audioControllerRef}
                            onUserText={(text: string) => addMessage("user", text)}
                            onModelText={(text: string) => addMessage("model", text)}
                            onSpeakingChange={setIsSpeaking}
                            onError={(msg) => alert(msg)}
                            mode={chatMode}
                        />
                    </div>
                )
            case "summary":
            case "mode_selection":
            default:
                return (
                    <div className={styles.modeSelectionContainer}>
                        <h1 className={styles.modeSelectionTitle}>
                            어떤 <span className={styles.highlight}>대화</span>를 원하시나요?
                        </h1>
                        <div className={styles.modeCardWrapper}>
                            <div className={styles.modeCard} onClick={() => handleModeSelect("feedback") as unknown as void}>
                                <FeedbackIcon />
                                <div>
                                    <h3>피드백 모드</h3>
                                    <p>
                                        대화하며 발음에 대한
                                        <br />실시간 피드백을 받습니다.
                                    </p>
                                </div>
                            </div>
                            <div className={styles.modeCard} onClick={() => handleModeSelect("general") as unknown as void}>
                                <GeneralIcon />
                                <div>
                                    <h3>일반 모드</h3>
                                    <p>
                                        자유롭게 대화하며
                                        <br />유창성을 기릅니다.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                );
        }
    }
    return (
        <div className={styles.pageWrapper}>
            {renderContent()}
            {isModalOpen && (
                <Modal
                    message="로그인이 필요한 서비스입니다. 로그인 하시겠습니까?"
                    onConfirm={handleConfirmAndLogin}
                    onCancel={handleCancel}
                />
            )}
        </div>
    );
};

export default Malbeot;