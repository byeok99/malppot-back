// import React from "react";
// import styled, { keyframes } from "styled-components";
// import { useNavigator } from "hooks/useNavigator";

// const fadeIn = keyframes`
//   from { opacity: 0; transform: translateY(-10px); }
//   to { opacity: 1; transform: translateY(0); }
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
//   z-index: 9999;
// `;

// const ModalContainer = styled.div`
//   background-color: white;
//   padding: 2.5rem;
//   border-radius: 16px;
//   box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
//   width: 90%;
//   max-width: 500px;
//   animation: ${fadeIn} 0.4s ease-out;
//   display: flex;
//   flex-direction: column;
//   gap: 1.5rem;
// `;

// const Title = styled.h2`
//   font-size: 1.6rem;
//   font-weight: 700;
//   color: #343a40;
//   text-align: center;
//   margin: 0;
// `;

// const SummarySection = styled.div`
//   font-size: 1rem;
//   color: #495057;
//   line-height: 1.6;
//   background-color: #f8f9fa;
//   padding: 1rem;
//   border-radius: 8px;
// `;

// const WordListSection = styled.div`
//   h4 {
//     font-size: 1.1rem;
//     font-weight: 600;
//     color: #495057;
//     margin: 0 0 0.75rem 0;
//   }
// `;

// const WordList = styled.div`
//   display: flex;
//   flex-wrap: wrap;
//   gap: 0.75rem;
// `;

// const WordTag = styled.button`
//   background-color: #eef7e9;
//   color: #556b2f;
//   padding: 0.5rem 1rem;
//   border-radius: 16px;
//   font-weight: 500;
//   border: none;
//   cursor: pointer;
//   transition: all 0.2s ease;

//   &:hover {
//     background-color: #d9eecb;
//     transform: translateY(-2px);
//   }
// `;

// const ButtonWrapper = styled.div`
//   display: flex;
//   gap: 0.75rem;
//   margin-top: 1rem;
// `;

// const ActionButton = styled.button`
//   flex: 1;
//   padding: 0.8rem 1.5rem;
//   font-size: 1rem;
//   font-weight: 600;
//   border-radius: 8px;
//   cursor: pointer;
//   transition: all 0.2s;
//   border: 1px solid #ddd;

//   &:hover {
//     opacity: 0.85;
//   }

//   &.primary {
//     background-color: #6a9b3e;
//     color: white;
//     border-color: #6a9b3e;
//   }

//   &.secondary {
//     background-color: #f1f1f1;
//     color: #555;
//   }
// `;

// // --- 타입 정의 ---
// interface SummaryData {
//   overallFeedback: string;
//   recommendedWords: string[];
// }

// interface ConversationSummaryModalProps {
//   summaryData: SummaryData | null;
//   onClose: () => void;
// }

// // --- useNavigator 리턴 타입 보완 (프로젝트 구현에 따라 필요 시 interface 확장) ---
// interface UseNavigator {
//   goPractice: () => void | Promise<void>;
//   goPracticeWithWord: (word: string) => void | Promise<void>;
// }

// const ConversationSummaryModal: React.FC<ConversationSummaryModalProps> = ({ summaryData, onClose }) => {
//   // useNavigator에서 실제로 goPracticeWithWord가 구현되어 있어야 함
//   const { goPractice, goPracticeWithWord } = useNavigator() as UseNavigator;

//   if (!summaryData) return null;

//   return (
//     <Overlay onClick={onClose}>
//       <ModalContainer onClick={(e) => e.stopPropagation()}>
//         <Title>대화 피드백 요약</Title>
//         <SummarySection>{summaryData.overallFeedback}</SummarySection>
//         <WordListSection>
//           <h4>연습이 필요한 단어</h4>
//           <WordList>
//             {summaryData.recommendedWords.map((word: string, index: number) => (
//               <WordTag key={index} onClick={() => goPracticeWithWord(word)}>
//                 {word}
//               </WordTag>
//             ))}
//           </WordList>
//         </WordListSection>
//         <ButtonWrapper>
//           <ActionButton className="secondary" onClick={onClose}>
//             닫기
//           </ActionButton>
//           <ActionButton className="primary" onClick={goPractice}>
//             연습실로 이동
//           </ActionButton>
//         </ButtonWrapper>
//       </ModalContainer>
//     </Overlay>
//   );
// };

// export default ConversationSummaryModal;
