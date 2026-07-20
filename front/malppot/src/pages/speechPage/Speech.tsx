import React, { useState, useRef, useMemo, useEffect } from "react";
import { useLocation } from 'react-router-dom';
import Lottie from "lottie-react";
import waitingAnimation from "assets/models/waiting.json";
import speechApis from 'apis/speechApi';
import { SyllableDetail, EvaluationResponse } from 'types/speech';
import styles from "./Speech.module.css";
import { BASE_URL } from "config"
import { useSyllableDetail } from 'hooks/useSyllableDetail';
import NotificationModal from 'components/common/NotificationModal'
import { FiRefreshCcw } from "react-icons/fi";
import { MdStop } from "react-icons/md";

interface LocationState {
    defaultText?: string;
}

// --- 아이콘 컴포넌트 ---

const ConvertIcon = () => <FiRefreshCcw size={20} />;

const MicIcon: React.FC = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
        <line x1="12" y1="19" x2="12" y2="23"></line>
        <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
);
const TipIcon: React.FC = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#fcc419"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M9 18h6M12 14v4M9 14h6a2 2 0 012 2v0a2 2 0 01-2 2h-6a2 2 0 01-2-2v0a2 2 0 012-2zM12 2a5 5 0 013.536 8.536L12 14l-3.536-3.536A5 5 0 0112 2z"></path>
    </svg>
);

const Speech: React.FC = () => {
    const location = useLocation();
    const [modalOpen, setModalOpen] = useState(false);
    const [modalMessage, setModalMessage] = useState<string>("");
    const { defaultText = '' } = (location.state || {}) as LocationState;
    const [practiceState, setPracticeState] = useState<"initial" | "loading" | "feedback">("initial");
    const [inputValue, setInputValue] = useState<string>(defaultText);
    const [convertedText, setConvertedText] = useState<string>("");
    const [isConverting, setIsConverting] = useState<boolean>(false);
    const [isRecording, setIsRecording] = useState<boolean>(false);
    const [feedback, setFeedback] = useState<EvaluationResponse | null>(null);
    const [selectedEojeolIndex, setSelectedEojeolIndex] = useState<number>(0);
    const [selectedSyllable, setSelectedSyllable] = useState<SyllableDetail | null>(null);
    const [lipsVideoIndex, setLipsVideoIndex] = useState(0);
    const [tongueVideoIndex, setTongueVideoIndex] = useState(0);
    const { data: syllableDetail, isFetching } = useSyllableDetail(selectedSyllable?.char ?? null);

    useEffect(() => {
        setLipsVideoIndex(0);
        setTongueVideoIndex(0);
    }, [selectedSyllable]);

    const syllableVideos: string[] = syllableDetail?.tongue_url ?? [];
    const lipsVideos: string[] = syllableDetail?.lips_url ?? [];
    const gptTip: string = syllableDetail?.gpt_tip ?? "";
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    useEffect(() => {
        return () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
                mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const handleReset = (): void => {
        setPracticeState("initial");
        setConvertedText("");
        setFeedback(null);
        setSelectedEojeolIndex(0);
        setSelectedSyllable(null);
    };

    const renderHighlightedSentence = (
        sentence: string,
        errorWords: string[] = []
    ) => {
        // 1) 공백 기준으로 단어 배열 생성
        const tokens = sentence.split(/\s+/);

        return tokens.map((tok, i) => (
            <React.Fragment key={i}>
                {errorWords.includes(tok) ? (
                    <span className={styles.redHighlight}>{tok}</span>
                ) : (
                    tok
                )}
                {i < tokens.length - 1 && " "}
            </React.Fragment>
        ));
    };

    const lowScoreWords = useMemo(
        () =>
            feedback?.feedback
                ?.filter((item) => item.average_score < 60)
                .map((item) => item.word) ?? [],
        [feedback]
    );
    useEffect(() => {
        if (!feedback) return;

        setSelectedEojeolIndex(0);
        const firstSyllable = feedback.feedback?.[0]?.syllables?.[0] ?? null;
        setSelectedSyllable(firstSyllable);
    }, [feedback]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setInputValue(e.target.value);
        if (practiceState === "feedback") handleReset();
    };

    const handleConvert = async (): Promise<void> => {
        if (!/^[가-힣\s!?\.]+$/.test(inputValue) || !inputValue.trim()) {
            setModalMessage("한글, 공백, ! ? . 만 입력해주세요!");
            setModalOpen(true);
            return;
        }


        setIsConverting(true);
        try {
            const convertRes = await speechApis.convert(inputValue);
            const converted: string = convertRes.data.converted_text;
            setConvertedText(converted);
        } catch (err) {
            console.log(err)
            setModalMessage("한글 문장을 입력해주세요.");
            setModalOpen(true);
        } finally {
            setIsConverting(false);
        }
    };

    const handlePronounce = async () => {
        if (!convertedText) {
            setModalMessage("먼저 변환된 문장을 입력해주세요.");
            setModalOpen(true);
            return;
        }

        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                mediaRecorderRef.current = mediaRecorder;
                audioChunksRef.current = [];

                mediaRecorder.ondataavailable = (event: BlobEvent) => {
                    audioChunksRef.current.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    setPracticeState("loading");

                    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm;codecs=opus" });
                    const formData = new FormData();
                    formData.append("reference_text", convertedText);
                    formData.append("original_text", inputValue);
                    formData.append("audio", audioBlob, "recording.webm");

                    try {
                        const res = await speechApis.evaluate(formData);
                        setFeedback(res.data);
                        setSelectedEojeolIndex(0);
                        setSelectedSyllable(res.data.feedback?.[0]?.syllables?.[0] ?? null);
                        setPracticeState("feedback");
                    } catch (err) {
                        setModalMessage("사용자의 음성을 녹음해주세요.");
                        setModalOpen(true);
                        setPracticeState("initial");
                    }

                    stream.getTracks().forEach(track => track.stop());
                    setIsRecording(false);
                };

                mediaRecorder.start();
                setIsRecording(true);
            } catch (err) {
                alert("마이크 권한을 확인해주세요.");
                console.error("마이크 접근 오류:", err);
            }
        } else {
            const recorder = mediaRecorderRef.current;
            if (recorder && recorder.state === "recording") {
                recorder.stop();
            }
        }
    };
    return (
        <div
            className={`${styles.pageContainer} ${(practiceState === "initial" || practiceState === "loading") ? styles.pageContainerCentered : ""}`}
        >
            {practiceState === "feedback" && feedback ? (
                <div className={styles.twoPanelWrapper}>
                    <div className={styles.guidePanel}>
                        <div className={styles.card + ' ' + styles.guideCard}>
                            <h3 className={styles.sectionTitle}>입모양 가이드</h3>
                            <div className={styles.mediaContainer}>
                                {isFetching || !lipsVideos.length ? (
                                    <div className={styles.guidePlaceholder}>
                                        영상을 생성 중입니다.
                                    </div>
                                ) : lipsVideos[lipsVideoIndex]?.endsWith('.mp4') ? (
                                    <video
                                        key={lipsVideos[lipsVideoIndex]}
                                        src={BASE_URL + lipsVideos[lipsVideoIndex]}
                                        controls
                                        autoPlay
                                        muted
                                        loop
                                        onEnded={() => {
                                            if (lipsVideoIndex < lipsVideos.length - 1) {
                                                setLipsVideoIndex(lipsVideoIndex + 1);
                                            } else {
                                                setLipsVideoIndex(0);
                                            }
                                        }}
                                        className={styles.gifImage}
                                    />
                                ) : lipsVideos[lipsVideoIndex]?.endsWith('.png') ? (
                                    <img
                                        key={lipsVideos[lipsVideoIndex]}
                                        src={BASE_URL + lipsVideos[lipsVideoIndex]}
                                        alt="입모양"
                                        className={styles.gifImage}
                                    />
                                ) : null}
                            </div>
                        </div>
                        <div className={styles.card + ' ' + styles.guideCard}>
                            <h3 className={styles.sectionTitle}>혀모양 가이드</h3>
                            <div className={styles.mediaContainer}>
                                {isFetching || !syllableVideos.length ? (
                                    <div className={styles.guidePlaceholder}>
                                        영상을 생성 중입니다.
                                    </div>
                                ) : syllableVideos[tongueVideoIndex]?.endsWith('.mp4') ? (
                                    <video
                                        key={syllableVideos[tongueVideoIndex]}
                                        src={BASE_URL + syllableVideos[tongueVideoIndex]}
                                        controls
                                        autoPlay
                                        muted
                                        loop
                                        onEnded={() => {
                                            if (tongueVideoIndex < syllableVideos.length - 1) {
                                                setTongueVideoIndex(tongueVideoIndex + 1);
                                            } else {
                                                setTongueVideoIndex(0);
                                            }
                                        }}
                                        className={styles.gifImage}
                                    />
                                ) : syllableVideos[tongueVideoIndex]?.endsWith('.png') ? (
                                    <img
                                        key={syllableVideos[tongueVideoIndex]}
                                        src={BASE_URL + syllableVideos[tongueVideoIndex]}
                                        alt="혀모양"
                                        className={styles.gifImage}
                                    />
                                ) : null}
                            </div>
                        </div>
                    </div>

                    <div className={styles.analysisPanel}>
                        <div className={styles.totalCard}>
                            <h3 className={styles.sectionTitle}>종합 평가</h3>
                            <div className={styles.evaluationResult}>
                                <span>
                                    {renderHighlightedSentence(feedback.reference_text, lowScoreWords)}
                                </span>
                                <span className={`${styles.score} ${feedback.scores < 60 ? styles.scoreLow : ""}`}>
                                    {feedback.scores}점
                                </span>
                            </div>
                        </div>

                        <div className={`${styles.card} ${styles.wordAnalysisSection}`}>
                            <h3 className={styles.sectionTitle}>단어별 발음 분석</h3>
                            <div className={styles.eojeolList}>
                                {feedback.feedback.map((item, index) => (
                                    <div
                                        key={index}
                                        className={`${styles.eojeolBlock} ${selectedEojeolIndex === index ? styles.eojeolSelected : ""} ${item.average_score < 60 ? styles.eojeolLow : item.average_score < 80 ? styles.eojeolMid : ""}`}
                                        onClick={() => {
                                            setSelectedEojeolIndex(index);
                                            setSelectedSyllable(item.syllables?.[0]);
                                        }}
                                    >
                                        <div className={styles.eojeolHeader}>
                                            <div className={styles.wordScoreWrap}>
                                                <span className={styles.eojeolText}>{item.word}</span>
                                                <span className={`${styles.eojeolScore} ${item.average_score < 60 ? styles.scoreLow : item.average_score < 80 ? styles.scoreMid : ""}`}>
                                                    {item.average_score === null ? 0 : item.average_score}점
                                                </span>
                                            </div>
                                        </div>
                                        {selectedEojeolIndex === index && (
                                            <>
                                                <div className={styles.eumjeolWrapper}>
                                                    {item.syllables.map((syllable, s_index) => (
                                                        <button
                                                            key={s_index}
                                                            className={`${styles.eumjeolButton} ${selectedSyllable?.char === syllable.char ? styles.eumjeolSelected : ""}`}
                                                            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                                                                e.stopPropagation();
                                                                setSelectedSyllable(syllable);
                                                            }}
                                                        >
                                                            {syllable.char}
                                                        </button>
                                                    ))}
                                                </div>
                                                <div className={styles.tipBox}>
                                                    <strong>
                                                        <TipIcon /> AI 조음 팁
                                                    </strong>
                                                    {gptTip}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button onClick={handleReset} className={styles.resetButton}>
                            다른 문장 연습하기
                        </button>
                    </div>
                </div>
            ) : (
                <div className={`${styles.textCard} ${styles.practiceCard} ${styles.practiceCardCentered}`}>
                    {practiceState === "initial" ? (
                        <>
                            <p className={styles.helperText}>
                                연습할 문장을 입력하고, 버튼을 눌러보세요.
                            </p>
                            <div className={styles.inputRow}>
                                <input
                                    type="text"
                                    placeholder="예시: 저는 오늘 학교에 갔어요"
                                    value={inputValue}
                                    onChange={handleInputChange}
                                    disabled={isRecording}
                                    className={styles.sentenceInput}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter" && !isRecording && !isConverting && inputValue.trim()) {
                                            handleConvert();
                                        }
                                    }}
                                />
                                <button
                                    onClick={handleConvert}
                                    disabled={isRecording || !inputValue.trim() || isConverting}
                                    className={styles.actionButton}
                                >
                                    <ConvertIcon />
                                </button>
                            </div>
                            <div className={styles.inputRow}>
                                <div className={styles.phoneticResult}>
                                    {convertedText ? (
                                        convertedText
                                    ) : (
                                        <span className={styles.placeholderText}>
                                            <ConvertIcon /> 버튼을 눌러 발음을 확인하세요
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={handlePronounce}
                                    disabled={!convertedText} //  || isRecording
                                    className={styles.actionButton}
                                >
                                    {isRecording ? <MdStop size={30} /> : <MicIcon />}

                                </button>
                            </div>
                            {isRecording ? (
                                <div className={styles.recording}>
                                    🎙️ 녹음 중입니다...
                                </div>
                            ) : null}
                        </>
                    ) : (
                        <div className={styles.statusDisplay}>
                            <Lottie
                                animationData={waitingAnimation}
                                style={{ width: 300, height: 300 }}
                            />
                            <p>AI가 발음을 분석하고 있습니다...</p>
                        </div>
                    )}
                </div>
            )}
            {modalOpen && (
                <NotificationModal
                    message={modalMessage}
                    onClose={() => setModalOpen(false)}
                />
            )}
        </div>
    );
};

export default Speech;