import React, { useState, useMemo } from 'react';
import styles from './MyPage.module.css';
import clsx from 'clsx';
import { generatePatientPdf } from 'utils/generatePdf';
import { useNavigator } from 'hooks/useNavigator';
import {
    useMyPageSummary,
    usePhonemeDetail,
    usePatientReport
} from 'hooks/useMyPageQueries';

import {
    PositionalAnalysis,
} from 'types/mypage';

import { TIER_CONFIG, getTier, getTierDescription } from 'utils/tierUtils';
import { getScoreColor } from 'utils/colorUtils';

import Lottie from 'lottie-react';
import waitingAnimation from 'assets/models/waiting.json';
import { UpArrowIcon, DownArrowIcon } from 'components/common/ArrowIcons';
import SvgGraph from 'components/my/SvgGraph';
import Pagination from 'components/common/Pagination';
import Sparkline from 'components/my/Sparkline';
import CardTitle from 'components/common/CardTitle';

const PositionalBarChart: React.FC<{ data: PositionalAnalysis }> = ({ data }) => {
    if (!data) return null;

    const initial = data['초성'] ?? data['initial'];
    const final = data['종성'] ?? data['final'];
    if (!initial && !final) return null;

    return (
        <div className={styles.barChartContainer}>
            {initial && (
                <div className={styles.barWrapper}>
                    <span className={styles.barLabel}>초성</span>
                    <div className={styles.bar}>
                        <div
                            className={styles.barFill}
                            style={{
                                width: `${initial.averageAccuracy}%`,
                                backgroundColor: getScoreColor(initial.averageAccuracy),
                            }}
                        />
                    </div>
                    <span className={styles.barScore}>{initial.averageAccuracy}점</span>
                </div>
            )}
            {final && (
                <div className={styles.barWrapper}>
                    <span className={styles.barLabel}>종성</span>
                    <div className={styles.bar}>
                        <div
                            className={styles.barFill}
                            style={{
                                width: `${final.averageAccuracy}%`,
                                backgroundColor: getScoreColor(final.averageAccuracy),
                            }}
                        />
                    </div>
                    <span className={styles.barScore}>{final.averageAccuracy}점</span>
                </div>
            )}
        </div>
    );
};

/* ────────────────────────────────────────────────────
   상세 리포트 패널
───────────────────────────────────────────────────── */
interface AnalysisReportProps {
    data: ReturnType<typeof usePhonemeDetail>['data'] | null | undefined;
    loading: boolean;
    error: Error | null;
    onPractice: (w: string) => void;
    selectedPhoneme: string;
}

const AnalysisReport: React.FC<AnalysisReportProps> = ({
    data,
    loading,
    error,
    onPractice,
    selectedPhoneme,
}) => {
    const [accordion, setAccordion] = useState(true);
    const [sortKey, setSortKey] = useState<'accuracy' | 'word'>('accuracy');
    const [filter, setFilter] = useState<string>('전체');
    const [page, setPage] = useState(1);
    const PER_PAGE = 5;

    /* 필터/정렬 -------------------------------------------------------------- */
    const processed = useMemo(() => {
        if (!data || !Array.isArray(data.allRecords)) return [];
        let records = [...data.allRecords];
        if (filter !== "전체") {
            records = records.filter((r) => r.mainErrorType === filter);
        }
        records.sort((a, b) =>
            sortKey === "word" ? a.word.localeCompare(b.word) : a.accuracy - b.accuracy
        );
        return records;
    }, [data, filter, sortKey]);

    const paginated = processed.slice((page - 1) * PER_PAGE, page * PER_PAGE);

    /* ---------------------------------------------------------------------- */
    if (loading) {
        return (
            <div className={styles.analysisReportContainer} style={{ textAlign: "center" }}>
                <Lottie animationData={waitingAnimation} style={{ width: 160, margin: "0 auto" }} />
                <p style={{ marginTop: 8 }}>데이터 불러오는 중…</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.analysisReportContainer}>
                <p style={{ color: '#fa5252', padding: '2rem' }}>
                    상세 데이터를 불러오지 못했습니다<br />({error.message})
                </p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className={styles.analysisReportContainer}>
                <p style={{ padding: '2rem', color: '#868e96' }}>
                    자음을 선택하면 자세한 분석이 표시됩니다.
                </p>
            </div>
        );
    }

    /* ──────────────────────────────────────── 실제 리포트 UI ─────────────── */
    return (
        <div className={styles.analysisReportContainer}>
            <h2>'{selectedPhoneme}' 발음 정밀 리포트</h2>

            <div className={styles.reportGrid}>
                <div className={styles.reportSection}>
                    <h4>위치별 정확도</h4>
                    <PositionalBarChart data={data.positionalAnalysis} />
                </div>

                <div className={styles.reportSection}>
                    <h4>AI 추천 연습 단어</h4>
                    <div className={styles.wordList}>
                        {(data.recommendedWords ?? []).map((w) => (
                            <button
                                key={w.word}
                                className={styles.recommendedWord}
                                onClick={() => onPractice(w.sentence)}
                            >
                                {w.word}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ▾ 상세 기록 토글 --------------------------------------------------- */}
            <button
                className={styles.seeAllButton}
                onClick={() => setAccordion(p => !p)}
            >
                {accordion ? '상세 기록 닫기 ▲' : '전체 연습 기록 보기 ▼'}
            </button>

            <div
                className={styles.accordionContent}
                style={{ maxHeight: accordion ? 600 : 0, opacity: accordion ? 1 : 0 }}
            >
                {/* --- 필터/정렬 --------------------------------------------------- */}
                <div className={styles.controlsWrapper}>
                    <div className={styles.filterButtonGroup}>
                        {['전체', '없음', '왜곡', '생략', '첨가'].map(f => (
                            <button
                                key={f}
                                className={clsx(styles.controlButton, {
                                    [styles.controlButtonActive]: filter === f,
                                })}
                                onClick={() => {
                                    setFilter(f);
                                    setPage(1);
                                }}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                    <div className={styles.filterButtonGroup}>
                        <button
                            className={clsx(styles.controlButton, {
                                [styles.controlButtonActive]: sortKey === 'accuracy',
                            })}
                            onClick={() => setSortKey('accuracy')}
                        >
                            정확도 낮은 순
                        </button>
                        <button
                            className={clsx(styles.controlButton, {
                                [styles.controlButtonActive]: sortKey === 'word',
                            })}
                            onClick={() => setSortKey('word')}
                        >
                            가나다순
                        </button>
                    </div>
                </div>

                {/* --- 테이블 ------------------------------------------------------ */}
                <div className={styles.tableWrapper}>
                    <table className={styles.analysisTable}>
                        <thead>
                            <tr>
                                <th>단어</th><th>정확도</th><th>오류 유형</th>
                                <th>정확도 변화</th><th>연습</th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginated.map(r => (
                                <tr key={r.id}>
                                    <td>{r.word}</td>
                                    <td>
                                        {Math.round(
                                            r.history.reduce((s, v) => s + v, 0) / r.history.length,
                                        )}
                                        %
                                    </td>
                                    <td>{r.mainErrorType}</td>
                                    <td><Sparkline scores={r.history} /></td>
                                    <td>
                                        <button
                                            className={styles.practiceButton}
                                            onClick={() => onPractice(r.word)}
                                        >
                                            연습
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <Pagination
                    totalItems={processed.length}
                    itemsPerPage={PER_PAGE}
                    currentPage={page}
                    onPageChange={setPage}
                />
            </div>
        </div>
    );
};

/* ────────────────────────────────────────────────────
   메인 페이지 컴포넌트
───────────────────────────────────────────────────── */
const MyPage: React.FC = () => {
    const { goSpeech } = useNavigator();
    const { refetch } = usePatientReport();

    const handleDownload = async () => {
        const result = await refetch();
        console.log(result)
        if (result.data) {
            generatePatientPdf(result.data);
        } else {
            alert('레포트 데이터를 가져오지 못했습니다.');
        }
    };
    /* 1) 상단 요약 ---------------------------------------------------------------- */
    const {
        data: summary,
        isLoading: summaryLoading,
        error: summaryError,
    } = useMyPageSummary();

    /* 2) 현재 선택된 자음 / 상세 쿼리 --------------------------------------------- */
    const [selectedPhoneme, setSelectedPhoneme] = useState('ㄱ');
    const {
        data: phonemeDetailRaw,
        isLoading: detailLoading,
        error: detailError,
    } = usePhonemeDetail(selectedPhoneme);
    const phonemeDetail = useMemo(
        () => (phonemeDetailRaw as any)?.detail ?? phonemeDetailRaw ?? null,
        [phonemeDetailRaw],
    );

    /* 3) 요약 로딩 & 에러 ---------------------------------------------------------- */
    if (summaryLoading) {
        return (
            <div className={styles.loadingWrapper}>
                <Lottie animationData={waitingAnimation} style={{ width: 300 }} />
                <p style={{ marginTop: 12 }}>데이터 로딩 중…</p>
            </div>
        );
    }
    if (summaryError || !summary) {
        return (
            <div className={styles.loadingWrapper}>
                <p style={{ color: '#fa5252', padding: '2rem' }}>
                    마이페이지 정보를 불러오지 못했습니다.<br />
                    {summaryError?.message}
                </p>
            </div>
        );
    }

    /* 4) 요약-데이터 구조 분해 ----------------------------------------------------- */
    const {
        userData,
        graphData,
        phonemeAccuracy,
        tenseConsonants,
    } = summary;

    const tier = getTier(
        userData.practiceStreak,
        userData.totalPracticeCount,
    );

    const handlePractice = (sentence: string) => goSpeech(sentence);

    /* ──────────────────────────────────────────────────── JSX ─────────────────── */
    return (
        <div className={styles.myPageWrapper}>
            {/* ---------- 상단 대시보드 ---------------------------------------------- */}
            <div className={styles.summaryDashboard}>
                {/* 인사 카드 */}
                <div className={clsx(styles.card, styles.greetingCard)}>
                    <div className={styles.userInfo}>
                        <img
                            className={styles.profileImage}
                            src={userData.profileImageUrl ?? undefined}
                            alt="profile"
                        />
                        <h2>
                            <span>{userData.userName}</span>님
                        </h2>
                    </div>
                    <div className={styles.tierInfo}>
                        <span className="tierIcon">{tier.icon}</span>
                        <div className="tierDetails">
                            <span className="tierName">{tier.name}</span>
                        </div>
                        <div className={styles.tierTooltip}>
                            {Object.values(TIER_CONFIG).map((t) => (
                                <div
                                    key={t.name}
                                    className={styles.tierTooltipItem + (tier.name === t.name ? ' ' + styles.active : '')}
                                >
                                    {getTierDescription(t)}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 그래프 카드 */}
                <div className={clsx(styles.card, styles.graphCard)}>
                    <CardTitle
                        title="주간 정확도 변화"
                        tooltipText="최근 7일간의 발음 연습 평균 정확도 변화를 보여줍니다."
                    />
                    <SvgGraph data={graphData} />
                </div>

                {/* 메트릭 카드 2개 */}
                <div className={styles.metricRow}>
                    {/* 연속 연습일 */}
                    <div className={clsx(styles.card, styles.metricCard)}>
                        <CardTitle title="연속 연습일" tooltipText="꾸준함의 지표!" />
                        <p className={styles.metricValue}>
                            {userData.practiceStreak}
                            <span>일째 🔥</span>
                        </p>
                    </div>
                    {/* 평균 정확도 */}
                    <div className={clsx(styles.card, styles.metricCard)}>
                        <CardTitle title="평균 정확도" tooltipText="최근 30일 기준입니다." />
                        <div className={styles.metricChange}>
                            <span className={styles.previousVal}>
                                {userData.accuracy.previous}점
                            </span>
                            {userData.accuracy.current > userData.accuracy.previous ? (
                                <UpArrowIcon />
                            ) : (
                                <DownArrowIcon />
                            )}
                            <div>
                                <span className={styles.currentVal}>
                                    {userData.accuracy.current}
                                </span>
                                <span className={styles.unit}>점</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ---------- 발음 지도 --------------------------------------------------- */}
            <div className={styles.card}>
                <CardTitle
                    title="발음 지도"
                    tooltipText="붉은색일수록 더 연습이 필요한 자음입니다."
                />
                <div className={styles.phonemeGridWrapper}>
                    <div className={styles.phonemeGrid}>
                        {Object.entries(phonemeAccuracy).map(([p, acc]) => (
                            <button
                                key={p}
                                className={clsx(styles.phonemeButton, {
                                    [styles.active]: selectedPhoneme === p,
                                })}
                                style={{ backgroundColor: getScoreColor(acc) }}
                                onClick={() => setSelectedPhoneme(p)}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                    <div className={styles.phonemeGrid}>
                        {Object.entries(tenseConsonants).map(([p, acc]) => (
                            <button
                                key={p}
                                className={clsx(styles.phonemeButton, {
                                    [styles.active]: selectedPhoneme === p,
                                })}
                                style={{ backgroundColor: getScoreColor(acc) }}
                                onClick={() => setSelectedPhoneme(p)}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ---------- 상세 리포트 ------------------------------------------------- */}
            <AnalysisReport
                data={phonemeDetail}
                loading={detailLoading}
                error={detailError}
                onPractice={handlePractice}
                selectedPhoneme={selectedPhoneme}
            />
            <div style={{ textAlign: "center" }}>
                <button className={styles.downloadButton} onClick={handleDownload}>
                    <svg /* download icon */ viewBox="0 0 20 20">
                        <path d="M10 2v10m0 0l-4-4m4 4l4-4M4 16h12" stroke="currentColor" strokeWidth="2" fill="none" />
                    </svg>
                    레포트 다운로드
                </button>
            </div>
        </div>
    );
};

export default MyPage;
