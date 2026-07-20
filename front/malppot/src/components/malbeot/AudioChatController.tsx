import { useRef, useImperativeHandle, forwardRef } from "react";
import { useSelector } from 'react-redux';
import store, { RootState } from 'store';
import { WS_BASE_URL, API } from '../../config';
import authApis from 'apis/authApi';

const BUFFER_SIZE = 4800;

export interface AudioChatControllerHandle {
    startAudio: () => Promise<void>;
    stopAudio: () => Promise<void>;
}

type ChatMode = "feedback" | "general" | null;

interface Props {
    onUserText?: (text: string) => void;
    onModelText?: (text: string) => void;
    onSpeakingChange?: (isSpeaking: boolean) => void;
    onError?: (errorMessage: string) => void;
    mode?: ChatMode
}

const AudioChatController = forwardRef<AudioChatControllerHandle, Props>(
    ({ onUserText, onModelText, onSpeakingChange, onError, mode }, ref) => {
        const accessToken = useSelector((state: RootState) => state.auth.accessToken);
        const wsRef = useRef<WebSocket | null>(null);
        const playerRef = useRef<Player | null>(null);
        const recorderRef = useRef<Recorder | null>(null);
        const bufferRef = useRef<Uint8Array>(new Uint8Array());
        const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
        const reconnectingRef = useRef<boolean>(false); // prevent multi-reconnect

        class Player {
            playbackNode: AudioWorkletNode | null = null;
            audioContext: AudioContext | null = null;

            async init(sampleRate: number) {
                this.audioContext = new AudioContext({ sampleRate });
                await this.audioContext.audioWorklet.addModule("/audio-playback-worklet.js");
                this.playbackNode = new AudioWorkletNode(this.audioContext, "audio-playback-worklet");
                this.playbackNode.connect(this.audioContext.destination);
            }

            play(buffer: Int16Array) {
                this.playbackNode?.port.postMessage(buffer);
            }

            stop() {
                this.playbackNode?.port.postMessage(null);
            }
        }

        class Recorder {
            audioContext: AudioContext | null = null;
            mediaStream: MediaStream | null = null;
            mediaStreamSource: MediaStreamAudioSourceNode | null = null;
            workletNode: AudioWorkletNode | null = null;

            constructor(private onDataAvailable: (data: ArrayBuffer) => void) { }

            async start(stream: MediaStream) {
                try {
                    if (this.audioContext) await this.audioContext.close();
                    this.audioContext = new AudioContext({ sampleRate: 24000 });
                    await this.audioContext.audioWorklet.addModule("/audio-processor-worklet.js");

                    this.mediaStream = stream;
                    this.mediaStreamSource = this.audioContext.createMediaStreamSource(this.mediaStream);
                    this.workletNode = new AudioWorkletNode(this.audioContext, "audio-processor-worklet");

                    this.workletNode.port.onmessage = event => {
                        this.onDataAvailable(event.data.buffer);
                    };

                    this.mediaStreamSource.connect(this.workletNode);
                    this.workletNode.connect(this.audioContext.destination);
                } catch (error) {
                    console.error('Recorder Error:', error);
                    this.stop();
                }
            }

            async stop() {
                this.mediaStream?.getTracks().forEach(track => track.stop());
                if (this.audioContext) await this.audioContext.close();
                this.mediaStream = null;
                this.mediaStreamSource = null;
                this.workletNode = null;
                this.audioContext = null;
            }
        }

        const startAudio = async (overrideToken?: string) => {
            try {
                const tokenToUse = overrideToken || accessToken;
                if (!tokenToUse) return;
                const ws = new WebSocket(`${WS_BASE_URL + API.AIMALBEOT}?mode=${mode}&access_token=${tokenToUse}`);
                wsRef.current = ws;

                const player = new Player();
                await player.init(24000);
                playerRef.current = player;

                ws.onmessage = event => {
                    const data = JSON.parse(event.data);
                    const t = data.type;

                    if (t === 'response.audio.delta') {
                        const binary = atob(data.delta);
                        const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
                        const pcmData = new Int16Array(bytes.buffer);
                        player.play(pcmData);
                        onSpeakingChange?.(true);
                        if (speakingTimeoutRef.current) clearTimeout(speakingTimeoutRef.current);
                        speakingTimeoutRef.current = setTimeout(() => onSpeakingChange?.(false), 300);
                    } else if (t === 'conversation.item.input_audio_transcription.completed') {
                        onUserText?.(data.transcript);
                    } else if (t === 'response.audio_transcript.done') {
                        onModelText?.(data.transcript);
                    } else if (t === 'response.audio_buffer.speech_started') {
                        console.log("🎤 Speech started");
                    } else if (t === 'error') {
                        const errorMsg = data.message || "알 수 없는 오류가 발생했습니다.";
                        if (errorMsg.includes("401") && errorMsg.toLowerCase().includes("token")) {
                            handleTokenExpired();
                        } else {
                            console.error("❌ WebSocket Error:", errorMsg);
                            onError?.(errorMsg);
                        }
                    } else {
                        console.log("📦 Unknown type:", t);
                    }
                };

                ws.onerror = (event) => {
                    console.error("❌ WebSocket connection error:", event);
                    onError?.("서버와의 연결 중 문제가 발생했습니다.");
                };

                ws.onclose = (event) => {
                    if (!event.wasClean) {
                        console.warn("⚠️ WebSocket closed unexpectedly:", event);
                        onError?.("서버와의 연결이 비정상적으로 종료되었습니다.");
                    }
                };

                const appendToBuffer = (newData: Uint8Array) => {
                    const currentBuffer = bufferRef.current;
                    const newBuffer = new Uint8Array(currentBuffer.length + newData.length);
                    newBuffer.set(currentBuffer);
                    newBuffer.set(newData, currentBuffer.length);
                    bufferRef.current = newBuffer;
                };

                const handleAudioData = (data: ArrayBuffer) => {
                    const uint8Array = new Uint8Array(data);
                    appendToBuffer(uint8Array);

                    if (bufferRef.current.length >= BUFFER_SIZE) {
                        const toSend = bufferRef.current.slice(0, BUFFER_SIZE);
                        bufferRef.current = bufferRef.current.slice(BUFFER_SIZE);

                        const regularArray = String.fromCharCode(...toSend);
                        const base64 = btoa(regularArray);

                        const ws = wsRef.current;
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({ type: 'input_audio_buffer.append', audio: base64 }));
                        }
                    }
                };

                const recorder = new Recorder(handleAudioData);
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                await recorder.start(stream);
                recorderRef.current = recorder;

            } catch (error) {
                console.error('Error setting up audio:', error);
            }
        };

        const stopAudio = async () => {
            wsRef.current?.close();
            wsRef.current = null;
            playerRef.current?.stop();
            playerRef.current = null;
            await recorderRef.current?.stop();
            recorderRef.current = null;
            bufferRef.current = new Uint8Array();
        };

        const handleTokenExpired = async () => {
            if (reconnectingRef.current) return;
            reconnectingRef.current = true;
            try {
                await stopAudio(); // 기존 연결 정리
                const resp = await authApis.refresh();
                const newToken = resp.data.access_token;


                // const newAccessToken = refreshResponse.data.access_token;
                if (newToken) {
                    store.dispatch({ type: 'auth/setAccessToken', payload: newToken });
                    await startAudio(newToken); // 갱신 토큰으로 재연결
                } else {
                    onError?.("토큰 갱신에 실패했습니다. 다시 로그인 해주세요.");
                }
            } catch (err) {
                onError?.("토큰 갱신에 실패했습니다. 다시 로그인 해주세요.");
            } finally {
                reconnectingRef.current = false;
            }
        };


        useImperativeHandle(ref, () => ({
            startAudio,
            stopAudio
        }));

        return <div style={{ marginTop: '20px' }} />;
    }
);

export default AudioChatController;