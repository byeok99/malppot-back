import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { PatientReport } from 'types/mypage';
import { notoSansKR } from 'assets/fonts/NotoSansKR';

export function generatePatientPdf(report: PatientReport) {
    const doc: any = new jsPDF();

    // ───── 한글 폰트 등록 ─────
    doc.addFileToVFS('NotoSansKR.ttf', notoSansKR.base64);
    doc.addFont('NotoSansKR.ttf', 'NotoSansKR', 'normal');
    doc.setFont('NotoSansKR');
    doc.setFontSize(18);

    // ───── 제목 가운데 정렬 ─────
    const title = `조음 훈련 서비스 [말:뻗]`;
    const pageWidth = doc.internal.pageSize.getWidth();
    const textWidth = doc.getTextWidth(title);
    const centerX = (pageWidth - textWidth) / 2;
    doc.text(title, centerX, 20);

    doc.setFontSize(12);
    doc.text(`성명: ${report.name}`, 14, 30);
    doc.text(`총 연습 횟수: ${report.total_practice_count}회`, 14, 38);
    doc.text(`전체 정확도: ${report.overall_accuracy.toFixed(0)}%`, 14, 46);

    // ───── 최근 7일간 정확도 변화 테이블 ─────
    doc.text('최근 7일간 정확도 변화', 14, 56);
    const trendLabels = ['6일 전', '5일 전', '4일 전', '3일 전', '2일 전', '1일 전', '오늘'];
    const trendBody = report.seven_day_accuracy_trend.map((val, idx) => [
        trendLabels[idx],
        `${val.toFixed(0)}%`,
    ]);
    autoTable(doc, {
        startY: 62,
        head: [['날짜', '정확도']],
        body: trendBody,
        theme: 'striped',
        styles: { fontSize: 10, font: 'NotoSansKR' },
        headStyles: { fontSize: 10, font: 'NotoSansKR', fontStyle: 'normal' },
    });

    // ───── 자음별 정확도 테이블 ─────
    doc.text('자음별 정확도', 14, doc.lastAutoTable.finalY + 10);
    const consonantRows = Object.entries(report.consonant_scores).map(([phoneme, score]) => [
        phoneme,
        `${score.toFixed(0)}%`,
    ]);
    autoTable(doc, {
        startY: doc.lastAutoTable.finalY + 16,
        head: [['자음', '정확도']],
        body: consonantRows,
        theme: 'grid',
        styles: { fontSize: 10, font: 'NotoSansKR' },
        headStyles: { fontSize: 10, font: 'NotoSansKR', fontStyle: 'normal' },
    });

    // ───── 자모별 상세 정보 (초성/종성 통합) ─────
    doc.addPage();
    doc.text('자모별 상세 정보 (초성/종성 통합)', 14, 20);

    const grouped = new Map<string, { 초성?: typeof report.jamo_detail[0], 종성?: typeof report.jamo_detail[0] }>();
    for (const item of report.jamo_detail) {
        if (!grouped.has(item.phoneme)) {
            grouped.set(item.phoneme, {});
        }
        const entry = grouped.get(item.phoneme)!;
        if (item.position === '초성') entry.초성 = item;
        else if (item.position === '종성') entry.종성 = item;
    }

    const mergedRows = Array.from(grouped.entries()).map(([phoneme, { 초성, 종성 }]) => [
        phoneme,
        초성 ? `${초성.average_score?.toFixed(0)}%` : '-',
        초성 ? `${초성.total_attempts}회` : '-',
        종성 ? `${종성.average_score?.toFixed(0)}%` : '-',
        종성 ? `${종성.total_attempts}회` : '-',
    ]);

    autoTable(doc, {
        startY: 26,
        head: [['자모', '초성 점수 평균', '초성 시도 횟수', '종성 점수 평균', '종성 시도 횟수']],
        body: mergedRows,
        theme: 'grid',
        styles: { fontSize: 9, font: 'NotoSansKR' },
        headStyles: { fontSize: 10, font: 'NotoSansKR', fontStyle: 'normal' },
    });

    // ───── 주의 자음 테이블 (맨 마지막에 배치) ─────
    if (report.attention_phonemes.length > 0) {
        doc.text('취약한 자음', 14, doc.lastAutoTable.finalY + 10);
        autoTable(doc, {
            startY: doc.lastAutoTable.finalY + 16,
            head: [['자음', '위치', '정확도']],
            body: report.attention_phonemes.map((p) => [
                p.phoneme,
                p.position,
                `${(p.accuracy).toFixed(0)}%`,
            ]),
            theme: 'striped',
            styles: { fontSize: 10, font: 'NotoSansKR' },
            headStyles: { fontSize: 10, font: 'NotoSansKR', fontStyle: 'normal' },
        });
    }

    // ───── PDF 저장 ─────
    doc.save(`report_${report.name}.pdf`);
}