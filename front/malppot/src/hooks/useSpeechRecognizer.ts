import { useEffect, useRef, useState, MutableRefObject } from 'react';

/* 타입 정의 */
export interface UseSpeechRecognizerOptions {
    lang?: string;
    interim?: boolean;
    recordAudio?: boolean;
    onTranscript?: (text: string) => void;
    onError?: (err: Error) => void;
}
export interface UseSpeechRecognizerReturn {
    start: () => Promise<void>;
    stop: () => Promise<Blob | undefined>;
    listening: boolean;
}

/* webkit prefix 대응 */
declare global {
    interface Window {
        webkitSpeechRecognition: typeof SpeechRecognition;
    }
}

export default function useSpeechRecognizer(
    opts: UseSpeechRecognizerOptions,
): UseSpeechRecognizerReturn {
    const {
        lang = 'ko-KR',
        interim = false,
        recordAudio = false,
        onTranscript,
        onError,
    } = opts;

    const [listening, setListening] = useState(false);

    const recogRef = useRef<SpeechRecognition | null>(null);
    const mediaRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const chunksRef = useRef<Blob[]>([]) as MutableRefObject<Blob[]>;

    // 인식 자동 재시작용 플래그 & 타이머
    const shouldRestartRef = useRef(false);

    // SpeechRecognition 초기화
    useEffect(() => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            onError?.(new Error('Browser does not support SpeechRecognition'));
            return;
        }

        const recog = new SR();
        recog.continuous = true;
        recog.interimResults = interim;
        recog.lang = lang;

        recog.onresult = (e: SpeechRecognitionEvent) => {
            const idx = e.resultIndex ?? e.results.length - 1;
            const text = e.results[idx][0].transcript.trim();
            if (text) onTranscript?.(text);
        };

        recog.onerror = (event: any) => {
            onError?.(new Error('음성 인식 오류: ' + event.error));
        };

        // 인식 세션이 종료되면 자동 재시작
        recog.onend = () => {
            // if (shouldRestartRef.current) {
            //     try { recog.start(); } catch { }
            // }
        };

        recogRef.current = recog;
        return () => recog.stop();
    }, [lang, interim, onTranscript, onError]);

    // MediaRecorder helpers
    const startRecording = async () => {
        if (!recordAudio) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;
            const mr = new MediaRecorder(stream);
            chunksRef.current = [];
            mr.ondataavailable = e => chunksRef.current.push(e.data);
            mr.start();
            mediaRef.current = mr;
        } catch (err: any) {
            onError?.(err);
        }
    };

    const stopRecording = (): Promise<Blob | undefined> => {
        return new Promise(resolve => {
            if (!recordAudio || !mediaRef.current) {
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(t => t.stop());
                    streamRef.current = null;
                }
                resolve(undefined);
                return;
            }
            const mr = mediaRef.current;
            mr.onstop = () => {
                const blob = chunksRef.current.length
                    ? new Blob(chunksRef.current, { type: 'audio/webm' })
                    : undefined;
                mr.stream.getTracks().forEach(t => t.stop());
                mediaRef.current = null;
                streamRef.current = null;
                chunksRef.current = [];
                resolve(blob);
            };
            mr.stop();
        });
    };

    // 외부 API
    const start = async () => {
        if (listening) return;
        await startRecording();
        shouldRestartRef.current = true;
        recogRef.current?.start();
        setListening(true);
    };

    const stop = async (): Promise<Blob | undefined> => {
        if (!listening) return undefined;
        shouldRestartRef.current = false;
        recogRef.current?.stop();
        setListening(false);
        return await stopRecording();
    };

    useEffect(() => {
        return () => {
            recogRef.current?.stop();
            shouldRestartRef.current = false;
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
            mediaRef.current?.stop();
        };
    }, []);

    return { start, stop, listening };
}