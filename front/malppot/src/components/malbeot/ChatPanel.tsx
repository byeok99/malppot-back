import React from "react";
import { useChat } from "utils/ChatContext";
import styles from "./ChatPanel.module.css";

const ChatPanel = (): React.JSX.Element => {
    const { messages } = useChat();

    return (
        <div className={styles.panelWrapper}>
            <h2 className={styles.header}>대화내용</h2>
            <div className={styles.chatMessages}>
                {messages.length === 0 ? (
                    <>
                        <div className={`${styles.messageRow} ${styles.modelMessage}`}>
                            <div className={`${styles.messageBubble} ${styles.modelBubble}`}>
                                AI 말벗과 대화해보세요!
                            </div>
                        </div>
                        <div className={`${styles.messageRow} ${styles.modelMessage}`}>
                            <div className={`${styles.messageBubble} ${styles.modelBubble}`}>
                                이곳에 채팅 내용이 표시됩니다.
                            </div>
                        </div>
                    </>
                ) : (
                    messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`${styles.messageRow} ${msg.speaker === "user" ? styles.userMessage : styles.modelMessage
                                }`}
                        >
                            <div
                                className={`${styles.messageBubble} ${msg.speaker === "user" ? styles.userBubble : styles.modelBubble
                                    }`}
                            >
                                {msg.transcript}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ChatPanel;