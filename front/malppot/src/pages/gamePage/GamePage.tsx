import React, { useEffect, useRef, useState } from 'react';
import {
    useStages,
    useEndlessWords,
    useHighestClearedStage,
    useBestScore,
    useCompleteStage,
    useSaveEndlessScore,
} from 'hooks/useGameQueries';
import NotificationModal from 'components/common/NotificationModal';
import styles from 'pages/gamePage/GamePage.module.css';
import speechApis from 'apis/speechApi';
import { IoMdStopwatch } from "react-icons/io";

const SPEED = 1;
const FALL_INTERVAL = 40;
const ENDLESS_WORD_INTERVAL = 1800;
const STAGE_WORD_INTERVAL = 1000;
const GAME_DURATION = 30;
const ENDLESS_BONUS_TIME = 5;
const ENDLESS_LIVES = 3;
const PLUS_SCORE = 20;
const IconInfinity = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 10c-1.67 0-3.14.85-4.1 2.1-.96 1.26-1.39 2.9-1.39 4.4C4.51 19.57 6.43 21 9 21s4.5-1.43 4.5-4.5c0-1.5-.43-3.14-1.4-4.4C11.14 10.85 9.67 10 8 10h0" />
        <path d="M14 14c1.67 0 3.14-.85 4.1 2.1.96-1.26 1.39-2.9 1.39-4.4C19.49 4.43 17.57 3 15 3s-4.5 1.43-4.5 4.5c0 1.5.43 3.14 1.4 4.4C12.86 13.15 14.33 14 16 14h0" />
    </svg>
);

const IconStages = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
        <path d="m9 12 2 2 4-4" />
    </svg>
);

const IconArrowRight = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <line x1="5" y1="12" x2="19" y2="12" />
        <polyline points="12 5 19 12 12 19" />
    </svg>
);

const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

type GameState = "initial" | "stage_select" | "playing" | "finished";
type GameMode = "endless" | "stage" | null;
type Difficulty = "EASY" | "NORMAL" | "HARD";
type LivesType = number | "∞";
type WordStatus = "active" | "popping";
type StageResult = "cleared" | "failed" | null;

interface StageWord {
    word: string;
    image_url: string;
}

interface FallingWord {
    id: number;
    text: string;
    x: number;
    y: number;
    speed: number;
    image?: string;
    status: WordStatus;
}

interface Stage {
    id: number;
    level: number;
    difficulty: Difficulty;
    goalValue: number;
    words: StageWord[];
    speed: number;
    interval: number;
    lives?: number;
}

const shuffle = <T,>(array: T[]): T[] => {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
};

const Game: React.FC = () => {
    const [gameState, setGameState] = useState<GameState>("initial");
    const [gameMode, setGameMode] = useState<GameMode>(null);
    // const [difficulty, setDifficulty] = useState<Difficulty>("EASY");
    const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
    const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);
    const [fallingWords, setFallingWords] = useState<FallingWord[]>([]);
    const [score, setScore] = useState(0);
    const [lives, setLives] = useState<LivesType>(ENDLESS_LIVES);
    const [playing, setPlaying] = useState(false);
    const [timeLeft, setTimeLeft] = useState<number>(GAME_DURATION);
    const [activeTab, setActiveTab] = useState<Difficulty>("EASY");
    const [stageResult, setStageResult] = useState<StageResult>(null);
    const gameScreenRef = useRef<HTMLDivElement>(null);
    const wordElementRef = useRef<HTMLDivElement>(null);

    // 🔥 추가: 셔플 및 상태
    const [shuffledStageWords, setShuffledStageWords] = useState<StageWord[]>([]);
    const [stageWordIndex, setStageWordIndex] = useState(0);
    const [allWordsDropped, setAllWordsDropped] = useState(false);

    const { data: stages, isLoading: isStagesLoading, error: stagesError } = useStages(true);
    const { data: endlessWords, isLoading: isEndlessLoading, error: endlessError } = useEndlessWords(playing && gameMode === "endless");
    const { data: highestClearedStage, isLoading: isClearedStageLoading } = useHighestClearedStage(gameState === "initial");
    const { data: rawBestScore, isFetching: isBestFetching } = useBestScore(gameState === 'initial');
    const [bestScore, setBestScore] = useState<number>(0);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const recognitionRef = useRef<any>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const micActiveRef = useRef(false);

    const saveEndlessScore = useSaveEndlessScore();
    const completeStage = useCompleteStage();

    const unlockedStage = (highestClearedStage ?? 1) + 1;
    const unlockedDifficulties: Difficulty[] = ["EASY"];
    if ((highestClearedStage ?? 1) >= 5) unlockedDifficulties.push("NORMAL");
    if ((highestClearedStage ?? 1) >= 10) unlockedDifficulties.push("HARD");

    // 🔥 단어 생성
    useEffect(() => {
        if (!playing) return;
        let wordInterval: NodeJS.Timeout;
        if (gameMode === "stage" && selectedStage) {
            const interval = (typeof selectedStage.interval === "number" && selectedStage.interval > 0)
                ? selectedStage.interval
                : STAGE_WORD_INTERVAL;
            wordInterval = setInterval(() => {
                if (stageWordIndex >= shuffledStageWords.length) {
                    clearInterval(wordInterval);
                    setAllWordsDropped(true);  // 소진 flag만 세움
                    return;
                }
                const { word, image_url } = shuffledStageWords[stageWordIndex];
                setStageWordIndex(idx => idx + 1);
                const newX = Math.random() * 90 + 5;
                setFallingWords(words => [
                    ...words,
                    {
                        id: Date.now() + Math.random(),
                        text: word,
                        x: newX,
                        y: 0,
                        speed: typeof selectedStage.speed === "number" && selectedStage.speed > 0 ? selectedStage.speed : SPEED,
                        image: image_url,
                        status: "active" as WordStatus,
                    }
                ]);
            }, interval);
        } else if (gameMode === "endless" && endlessWords && endlessWords.length > 0) {
            wordInterval = setInterval(() => {
                const [text, image] = endlessWords[Math.floor(Math.random() * endlessWords.length)];
                const newX = Math.random() * 90 + 5;
                setFallingWords(words => [
                    ...words,
                    {
                        id: Date.now() + Math.random(),
                        text: text,
                        x: newX,
                        y: 0,
                        speed: SPEED,
                        image: image,
                        status: "active" as WordStatus,
                    }
                ]);
            }, ENDLESS_WORD_INTERVAL);
        }
        return () => clearInterval(wordInterval);
    }, [playing, gameMode, selectedStage, endlessWords, shuffledStageWords, stageWordIndex]);

    // 🔥 단어 소진 + 화면 내 단어가 모두 사라졌을 때 자동 종료
    useEffect(() => {
        if (
            gameMode === "stage" &&
            allWordsDropped &&
            playing &&
            fallingWords.length === 0
        ) {
            setPlaying(false);
            setGameState("finished");
        }
    }, [fallingWords, allWordsDropped, gameMode, playing]);

    // 단어 낙하/생명감소
    useEffect(() => {
        if (!playing) return;

        const fallInterval = setInterval(() => {
            const containerHeight = gameScreenRef.current?.clientHeight || 500;
            const wordHeight = wordElementRef.current?.offsetHeight || 60;

            setFallingWords(prevWords => {
                let lost = 0;
                const updated = prevWords.reduce<FallingWord[]>((acc, word) => {
                    const newY = word.y + word.speed;
                    if (newY >= containerHeight - wordHeight) {
                        lost += 1;
                    } else {
                        acc.push({ ...word, y: newY });
                    }
                    return acc;
                }, []);
                if (lost > 0 && lives !== "∞") setLives(l => Math.max(0, (l as number) - lost));
                return updated;
            });
        }, FALL_INTERVAL);
        return () => clearInterval(fallInterval);
    }, [playing]);

    // 엔드리스 타이머
    useEffect(() => {
        if (!playing || gameMode !== "endless") return;
        if (timeLeft <= 0) {
            setPlaying(false);
            setGameState("finished");
            return;
        }
        const timer = setInterval(() => {
            setTimeLeft(t => t - 1);
        }, 1000);
        return () => clearInterval(timer);
    }, [playing, gameMode, timeLeft]);

    // 게임오버/스테이지 종료 체크
    useEffect(() => {
        if (!playing) return;
        if (lives !== "∞" && lives <= 0) {
            setGameState("finished");
            setPlaying(false);
        } else if (gameMode === "stage" && selectedStage && score >= selectedStage.goalValue) {
            setGameState("finished");
            setStageResult("cleared");
            setPlaying(false);
            completeStage.mutate({ stageId: selectedStage.id });
        } else if (gameMode === "endless" && score >= bestScore) {
            saveEndlessScore.mutate(
                { newScore: score }
            );
            setBestScore(score)
        }
    }, [lives, playing, gameMode, selectedStage, score]);

    useEffect(() => {
        if (rawBestScore !== undefined && rawBestScore !== null) {
            setBestScore(rawBestScore);
        }
    }, [rawBestScore]);

    // 음성 인식/녹음 루프
    useEffect(() => {
        if (!playing) return;

        if (!SpeechRecognition) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다. Chrome을 사용하세요.");
            setPlaying(false);
            return;
        }

        let stopped = false;
        micActiveRef.current = true;

        const startRecognition = async () => {
            if (stopped) return;

            let stream;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            } catch (e) {
                alert("마이크 사용 권한을 허용해 주세요.");
                setPlaying(false);
                return;
            }

            mediaStreamRef.current = stream;
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            const recognition = new SpeechRecognition();
            recognitionRef.current = recognition;
            recognition.lang = 'ko-KR';
            recognition.continuous = false;
            recognition.interimResults = false;

            let recognizedText = '';
            let finished = false;

            recognition.onresult = (event: any) => {
                if (finished) return;
                finished = true;
                recognizedText = event.results[0][0].transcript.trim().replace(/\s/g, "");
                try { mediaRecorder.stop(); } catch { }
            };
            recognition.onerror = () => {
                if (finished) return;
                finished = true;
                try { mediaRecorder.stop(); } catch { }
            };
            recognition.onend = () => {
                if (!stopped) startRecognition();
            };

            mediaRecorder.ondataavailable = (e) => {
                audioChunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = () => {
                if (stopped) return;
                const recognizedStr = recognizedText.replace(/\s/g, "");

                let matchedSentence = "";
                let matchedWords: string[] = [];

                setFallingWords(words => {
                    let matchedCount = 0;
                    matchedWords = [];

                    const newWords = words.filter(word => {
                        const cleanWord = word.text.replace(/\s/g, "");
                        const isMatched = recognizedStr.includes(cleanWord);
                        if (isMatched) {
                            matchedCount += 1;
                            matchedWords.push(word.text)
                        }
                        return !isMatched;
                    });

                    if (gameMode === "endless" && matchedCount > 0) {
                        setScore(score => score + matchedCount * PLUS_SCORE);
                        setTimeLeft(time => time + ENDLESS_BONUS_TIME * matchedCount);
                    } else if (matchedCount > 0) {
                        setScore(score => score + matchedCount * PLUS_SCORE);
                    }

                    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                    matchedSentence = matchedWords.join(" ");

                    if (matchedSentence) {
                        const formData = new FormData();
                        formData.append("reference_text", matchedSentence);
                        formData.append("original_text", matchedSentence);
                        formData.append("audio", audioBlob, "recording.webm");
                        speechApis.evaluate(formData);
                    }

                    return newWords;
                });

                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach(track => track.stop());
                    mediaStreamRef.current = null;
                }
                recognitionRef.current = null;
                mediaRecorderRef.current = null;
            };

            mediaRecorder.start();
            recognition.start();
        };

        stopped = false;
        startRecognition();

        return () => {
            stopped = true;
            micActiveRef.current = false;
            try {
                if (recognitionRef.current) {
                    recognitionRef.current.onresult = null;
                    recognitionRef.current.onerror = null;
                    recognitionRef.current.onend = null;
                    recognitionRef.current.abort && recognitionRef.current.abort();
                    recognitionRef.current.stop && recognitionRef.current.stop();
                    recognitionRef.current = null;
                }
            } catch { }
            try {
                if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
                mediaRecorderRef.current = null;
            } catch { }
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach(track => track.stop());
                mediaStreamRef.current = null;
            }
        };
    }, [playing, gameMode]);

    // 핸들러
    const resetGame = () => {
        setFallingWords([]);
        setScore(0);
        setLives(ENDLESS_LIVES);
        setTimeLeft(GAME_DURATION);
        setShuffledStageWords([]);
        setStageWordIndex(0);
        setAllWordsDropped(false);
    };

    const handleStartEndless = () => {
        setGameMode("endless");
        setGameState("playing");
        setPlaying(true);
        resetGame();
    };

    const handleSelectStage = () => setGameState("stage_select");

    const handleStageStart = (stage: Stage) => {
        setSelectedStage(stage);
        // setDifficulty(stage.difficulty);
        setLives(typeof stage.lives === "number" && stage.lives > 0 ? stage.lives : "∞");
        setGameMode("stage");
        setGameState("playing");
        setPlaying(true);
        setTimeLeft(0);
        setFallingWords([]);
        setScore(0);
        setShuffledStageWords(shuffle(stage.words)); // 셔플!
        setStageWordIndex(0); // 인덱스 리셋
        setAllWordsDropped(false); // flag 초기화
    };

    const ErrorMessage: React.FC<{ message: string; onExit: () => void }> = ({ message, onExit }) => (
        <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <div className={styles.centerText}>{message}</div>
            <div style={{ margin: "16px 0" }} />
            <button
                className={styles.exitButton}
                onClick={onExit}
            >
                메인으로
            </button>
        </div>
    )

    function renderContent() {
        switch (gameState) {
            case "initial":
                return (
                    <div className={styles.newLobbyContainer}>
                        <div className={styles.visualPanel}>
                            <h1>
                                게임으로 즐기는
                                <br />
                                <span>[말:뻗]</span>
                            </h1>
                            <p>게임과 함께 자연스럽게 발음을 연습해보세요!</p>
                        </div>
                        <div className={styles.controlsPanel}>
                            <h1 className={styles.gameTitle}>단어 비 게임</h1>
                            <button className={styles.menuButton} onClick={handleStartEndless}>
                                <div className={styles.icon}>
                                    <IconInfinity />
                                </div>
                                <div className={styles.textContent}>
                                    <h3>무한 도전</h3>
                                    <p>시간 내에 최대한 많은 점수를 획득해보세요.</p>
                                </div>
                                <div className={styles.arrow}>
                                    <IconArrowRight />
                                </div>
                            </button>
                            <button className={styles.menuButton} onClick={handleSelectStage}>
                                <div className={styles.icon}>
                                    <IconStages />
                                </div>
                                <div className={styles.textContent}>
                                    <h3>단계별 연습</h3>
                                    <p>차근차근 단계를 클리어하며 실력을 키워보세요.</p>
                                </div>
                                <div className={styles.arrow}>
                                    <IconArrowRight />
                                </div>
                            </button>
                            <div className={styles.utilLinks}>
                                <button className={styles.secondaryLink} onClick={() => setIsHelpOpen(true)}>
                                    게임 방법
                                </button>
                            </div>
                        </div>
                    </div>
                );
            case "stage_select":
                if (isStagesLoading || isClearedStageLoading) return <div>로딩 중...</div>;
                if (stagesError) return <ErrorMessage message={"단어를 불러올 수 없습니다."} onExit={() => { setGameState("initial"); setGameMode(null); }} />;
                if (!stages || !Array.isArray(stages) || stages.length === 0) return <ErrorMessage message={"스테이지 데이터가 없습니다."} onExit={() => { setGameState("initial"); setGameMode(null); }} />;

                const difficulties: Difficulty[] = ["EASY", "NORMAL", "HARD"];

                return (
                    <div className={styles.lobbyWrapper}>
                        <h1 className={styles.lobbyTitle}>단계별 연습</h1>
                        <div className={styles.stageSelectWrapper}>
                            <div className={styles.tabContainer}>
                                {difficulties.map((difficulty) => (
                                    <button
                                        key={difficulty}
                                        className={`${styles.tabButton} ${activeTab === difficulty ? styles.active : ""}`}
                                        onClick={() => setActiveTab(difficulty)}
                                        disabled={!unlockedDifficulties.includes(difficulty)}
                                    >
                                        {difficulty} {!unlockedDifficulties.includes(difficulty) && "🔒"}
                                    </button>
                                ))}
                            </div>
                            <div className={styles.tabContent}>
                                {stages
                                    .filter((s) => s.difficulty === activeTab)
                                    .map((stage) => (
                                        <button
                                            key={stage.id}
                                            className={styles.stageButton}
                                            disabled={stage.id > unlockedStage}
                                            onClick={() => handleStageStart(stage)}
                                        >
                                            {stage.level}
                                        </button>
                                    ))}
                            </div>
                        </div>
                        <button className={styles.stageSelectUtilButton} onClick={() => { setGameState("initial"); setGameMode(null); }}>
                            모드 선택으로
                        </button>
                    </div >
                );
            case "playing":
                if (gameMode === "endless" && isEndlessLoading) return <div className={styles.centerText}>무한 도전 모드 단어를 불러오는 중…</div>;
                if (isBestFetching) return <ErrorMessage message={"이전 점수를 불러올 수 없습니다."} onExit={() => { setGameState("initial"); setGameMode(null); }} />;
                if (gameMode === "endless" && endlessError) return <ErrorMessage message={"단어를 불러올 수 없습니다."} onExit={() => { setGameState("initial"); setGameMode(null); }} />;

                let goalText: string;
                if (gameMode === "stage" && selectedStage) {
                    goalText = `목표: ${score} / ${selectedStage.goalValue}`;
                } else {
                    goalText = `최고 ${bestScore}점`;
                }

                const renderLives = () => {
                    if (lives === "∞") {
                        return <span style={{ fontSize: '1.5rem' }}>❤️ ∞</span>;
                    }

                    const initialLives = gameMode === 'endless'
                        ? ENDLESS_LIVES
                        : (selectedStage?.lives ?? 0);

                    if (initialLives === 0) {
                        return <span style={{ fontSize: '1.5rem' }}>❤️ ∞</span>;
                    }

                    const currentLives = typeof lives === 'number' ? lives : 0;
                    const fullHearts = Array.from({ length: currentLives }, (_, i) => <span key={`full_${i}`}>❤️</span>);
                    const brokenHearts = Array.from({ length: initialLives - currentLives }, (_, i) => <span key={`broken_${i}`}>💔</span>);

                    return <div style={{ display: 'flex', gap: '0.2rem', fontSize: '1.5rem' }}>{fullHearts}{brokenHearts}</div>;
                };


                return (
                    <div className={styles.gameContainer}>
                        <div className={styles.playContainer}>
                            <div className={styles.scoreBoard}>
                                <button className={styles.exitButton} onClick={() => { setPlaying(false); setGameState("finished"); }}>게임 종료</button>
                                <div style={{ justifySelf: "center" }}>
                                    {renderLives()}
                                </div>
                                <h2>{goalText}</h2>
                            </div>
                            <div className={styles.gameScreen} ref={gameScreenRef}>
                                {gameMode == "endless" ?
                                    <div className={styles.timeDisplay}><IoMdStopwatch size="40" style={{ verticalAlign: "bottom" }} />{timeLeft}</div>
                                    : null}
                                <div className={styles.scoreDisplay}>{score}</div>
                                {fallingWords.map((w, i) => (
                                    <div
                                        ref={i === 0 ? wordElementRef : null}
                                        key={w.id}
                                        className={`${styles.word} ${w.status === "popping" ? styles.popping : ""}`}
                                        style={{ top: `${w.y}px`, left: `${w.x}%`, textAlign: "center" }}
                                        onAnimationEnd={() => {
                                            if (w.status === "popping") return;
                                        }}
                                    >
                                        {w.image && (
                                            <img src={w.image} alt={w.text} style={{ width: 60, height: 60, objectFit: "contain" }} />
                                        )}
                                        <div style={{ textAlign: "center", fontSize: "2rem" }}>{w.text}</div>
                                    </div>
                                ))}
                                <div className={styles.bottomLine} />
                            </div>
                        </div>
                    </div>
                );
            case "finished":
                const isCleared = stageResult === "cleared";
                const nextStage =
                    gameMode === "stage"
                        ? stages?.find((s) => selectedStage && s.id === selectedStage.id + 1)
                        : null;

                return (
                    <div className={styles.lobbyWrapper}>
                        <h1 className={styles.lobbyTitle}>
                            {gameMode === "stage"
                                ? isCleared
                                    ? "Stage Clear!"
                                    : "Mission Failed"
                                : "게임 종료"}
                        </h1>
                        <p className={styles.lobbyDescription}>
                            최종 점수: <strong>{score}점</strong>
                        </p>
                        {gameMode === "endless" && (
                            <p className={styles.lobbyDescription}>내 최고 점수: {bestScore}점</p>
                        )}
                        <div className={styles.buttonGroup}>
                            {gameMode === "stage" && isCleared && nextStage && (
                                <button
                                    className={`${styles.gameButton} ${styles.primary}`}
                                    onClick={() => handleStageStart(nextStage)}
                                >
                                    다음 단계
                                </button>
                            )}
                            <button
                                className={`${styles.gameButton} ${!isCleared ? styles.primary : ""}`}
                                onClick={() =>
                                    gameMode === "stage"
                                        ? selectedStage && handleStageStart(selectedStage)
                                        : handleStartEndless()
                                }
                            >
                                다시하기
                            </button>
                            <button className={styles.gameButton} onClick={() => { setGameState("initial"); setGameMode(null); }}>
                                모드 선택으로
                            </button>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    }


    return (
        <div className={styles.gamePageWrapper}>
            {isHelpOpen && (
                <NotificationModal message={"하늘에서 내려오는 낱말을 보고 마이크에 대고 정확하게 발음하여 점수를 획득하는 게임입니다. (Chrome 브라우저 권장)"} onClose={() => setIsHelpOpen(false)} />
            )}
            {renderContent()}
        </div>

    );
};

export default Game;