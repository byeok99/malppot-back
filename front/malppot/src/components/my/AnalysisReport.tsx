import React, { useState, useMemo, useEffect } from "react";
import clsx from "clsx";

import { AnalysisReportProps, DetailedRecord } from 'types/mypage';
import Pagination from "../common/Pagination";
import styles from "./AnalysisReport.module.css";

const AnalysisReport: React.FC<AnalysisReportProps> = ({ data, onPractice }) => {
    const [accordion, setAccordion] = useState(false);
    const [sortKey, setSortKey] = useState<"accuracy" | "word">("accuracy");
    const [filter, setFilter] = useState<string>("전체");
    const [page, setPage] = useState<number>(1);
    const PER_PAGE = 5;

    useEffect(() => {
        setAccordion(false);
        setFilter("전체");
        setPage(1);
        setSortKey("accuracy");
    }, [data]);

    const processed = useMemo(() => {
        if (!data) return [] as DetailedRecord[];
        let records = [...data.allRecords];
        if (filter !== "전체") records = records.filter((r) => r.mainErrorType === filter);
        records.sort((a, b) => (sortKey === "word" ? a.word.localeCompare(b.word) : a.accuracy - b.accuracy));
        return records;
    }, [data, filter, sortKey]);

    const paginated = processed.slice((page - 1) * PER_PAGE, page * PER_PAGE);

    if (!data) return (
        <div className={styles.analysisReportContainer}>
            <p style={{ textAlign: "center", padding: "4rem 2rem", color: "#868e96" }}>
                상단의 발음 지도에서 분석하고 싶은 자음을 선택해주세요.
            </p>
        </div>
    );

    return (
        <div className={styles.analysisReportContainer}>
            <h2>발음 정밀 리포트</h2>

            {/* 상단 그리드 */}
            <div className={styles.reportGrid}>
                <div className={styles.reportSection}>
                    <h4>AI 추천 연습 단어</h4>
                    <div className={styles.wordList}>
                        {data.recommendedWords.map((w) => (
                            <button key={w.word} className={styles.recommendedWord} onClick={() => onPractice(w.sentence)}>{w.word}</button>
                        ))}
                    </div>
                </div>
            </div>

            <button className={styles.seeAllButton} onClick={() => setAccordion((p) => !p)}>
                {accordion ? "상세 기록 닫기 ▲" : "전체 연습 기록 보기 ▼"}
            </button>

            <div
                className={styles.accordionContent}
                style={{ maxHeight: accordion ? 600 : 0, opacity: accordion ? 1 : 0 }}
            >
                {/* Controls */}
                <div className={styles.controlsWrapper}>
                    <div className={styles.filterButtonGroup}>
                        {["전체", "대치", "왜곡", "생략", "첨가"].map((f) => (
                            <button
                                key={f}
                                className={clsx(styles.controlButton, { [styles.controlButtonActive]: filter === f })}
                                onClick={() => { setFilter(f); setPage(1); }}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                    <div className={styles.filterButtonGroup}>
                        <button
                            className={clsx(styles.controlButton, { [styles.controlButtonActive]: sortKey === "accuracy" })}
                            onClick={() => setSortKey("accuracy")}
                        >
                            정확도 낮은 순
                        </button>
                        <button
                            className={clsx(styles.controlButton, { [styles.controlButtonActive]: sortKey === "word" })}
                            onClick={() => setSortKey("word")}
                        >
                            가나다순
                        </button>
                    </div>
                </div>

                {/* Table */}
                <div className={styles.tableWrapper}>
                    <table className={styles.analysisTable}>
                        <thead>
                            <tr><th>단어</th><th>정확도</th><th>오류 유형</th><th>연습</th></tr>
                        </thead>
                        <tbody>
                            {paginated.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.word}</td>
                                    <td>{item.accuracy}%</td>
                                    <td>{item.mainErrorType}</td>
                                    <td>
                                        <button className={styles.practiceButton} onClick={() => onPractice(item.word)}>연습</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <Pagination totalItems={processed.length} itemsPerPage={PER_PAGE} currentPage={page} onPageChange={setPage} />
            </div>
        </div>
    );
};

export default AnalysisReport;
