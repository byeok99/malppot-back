// import React from "react";
// import styled, { keyframes } from "styled-components";

// const fadeIn = keyframes`
//   from { opacity: 0; transform: scale(0.95); }
//   to { opacity: 1; transform: scale(1); }
// `;

// const Overlay = styled.div`
//   position: fixed;
//   top: 0;
//   left: 0;
//   width: 100%;
//   height: 100%;
//   background-color: rgba(0, 0, 0, 0.6);
//   display: flex;
//   justify-content: center;
//   align-items: center;
//   z-index: 10000;
// `;

// const ModalContainer = styled.div`
//   background-color: white;
//   padding: 2.5rem;
//   border-radius: 16px;
//   box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
//   width: 90%;
//   max-width: 480px;
//   animation: ${fadeIn} 0.3s ease-out;
//   display: flex;
//   flex-direction: column;
//   align-items: center;
//   gap: 1.5rem;
//   text-align: center;
// `;

// const Title = styled.h2`
//   font-size: 1.6rem;
//   font-weight: 700;
//   color: #343a40;
//   margin: 0;
// `;

// const Icon = styled.div`
//   font-size: 3rem;
//   line-height: 1;
// `;

// const SummarySection = styled.div`
//   font-size: 1.1rem;
//   color: #495057;
//   line-height: 1.6;
// `;

// const KeywordSection = styled.div`
//   display: flex;
//   flex-wrap: wrap;
//   gap: 0.75rem;
//   justify-content: center;
// `;

// const KeywordTag = styled.span`
//   background-color: #e9ecef;
//   color: #495057;
//   padding: 0.5rem 1rem;
//   border-radius: 16px;
//   font-weight: 500;
// `;

// const CloseButton = styled.button`
//   width: 100%;
//   padding: 0.8rem 1.5rem;
//   font-size: 1rem;
//   font-weight: 600;
//   border-radius: 8px;
//   cursor: pointer;
//   transition: all 0.2s;
//   background-color: #6a9b3e;
//   color: white;
//   border: none;
//   margin-top: 1rem;

//   &:hover {
//     opacity: 0.85;
//   }
// `;

// const GeneralReportModal = ({ reportData, onClose }) => {
//     if (!reportData) return null;

//     return (
//         <Overlay onClick={onClose}>
//             <ModalContainer onClick={(e) => e.stopPropagation()}>
//                 <Icon>🎉</Icon>
//                 <Title>오늘의 대화 하이라이트</Title>
//                 <SummarySection>{reportData.summaryText}</SummarySection>
//                 <KeywordSection>
//                     {reportData.keywords.map((word, index) => (
//                         <KeywordTag key={index}>#{word}</KeywordTag>
//                     ))}
//                 </KeywordSection>
//                 <CloseButton onClick={onClose}>확인</CloseButton>
//             </ModalContainer>
//         </Overlay>
//     );
// };

// export default GeneralReportModal;
