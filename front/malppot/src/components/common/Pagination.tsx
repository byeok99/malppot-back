import React from 'react';
import styled from 'styled-components';

interface PaginationProps {
    totalItems: number;
    itemsPerPage: number;
    currentPage: number;
    onPageChange: (page: number) => void;
}

const PaginationWrapper = styled.div`
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.25rem;
    margin-top: 1.5rem;
`;

const PageButton = styled.button<{ $active: boolean }>`
    min-width: 32px;
    padding: 0.5rem;
    border: 1px solid #dee2e6;
    background-color: ${(props) => (props.$active ? "#6a9b3e" : "#fff")};
    color: ${(props) => (props.$active ? "#fff" : "#495057")};
    border-radius: 6px;
    cursor: pointer;
    &:disabled {
        background-color: #f8f9fa;
        cursor: not-allowed;
        color: #ced4da;
    }
`;

const Pagination = ({
    totalItems,
    itemsPerPage,
    currentPage,
    onPageChange,
}: PaginationProps): React.JSX.Element | null => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const PAGE_GROUP_SIZE = 10;

    if (totalPages <= 1) return null;

    const currentGroup = Math.ceil(currentPage / PAGE_GROUP_SIZE);
    const startPage = (currentGroup - 1) * PAGE_GROUP_SIZE + 1;
    const endPage = Math.min(startPage + PAGE_GROUP_SIZE - 1, totalPages);

    const pageNumbers = [];
    for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
    }

    return (
        <PaginationWrapper>
            <PageButton onClick={() => onPageChange(1)} disabled={currentPage === 1} $active={false}>
                &lt;&lt;
            </PageButton>
            <PageButton
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                $active={false}
            >
                &lt;
            </PageButton>
            {pageNumbers.map((page) => (
                <PageButton
                    key={page}
                    $active={page === currentPage}
                    onClick={() => onPageChange(page)}
                >
                    {page}
                </PageButton>
            ))}
            <PageButton
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                $active={false}
            >
                &gt;
            </PageButton>
            <PageButton
                onClick={() => onPageChange(totalPages)}
                disabled={currentPage === totalPages}
                $active={false}
            >
                &gt;&gt;
            </PageButton>
        </PaginationWrapper>
    );
};

export default Pagination;