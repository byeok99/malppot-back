import React from "react";
import styled, { keyframes } from "styled-components";

// --- Styled Components ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
`;

const ModalContainer = styled.div`
  background-color: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
  text-align: center;
  animation: ${fadeIn} 0.3s ease-out;
`;

const Message = styled.p`
  font-size: 1.1rem;
  color: #333;
  margin: 0 0 2rem 0;
  line-height: 1.6;
`;

const ButtonWrapper = styled.div`
  display: flex;
  justify-content: center; /* 버튼을 중앙에 배치 */
`;

const ConfirmButton = styled.button`
  width: 100%;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #6a9b3e;
  background-color: #6a9b3e;
  color: white;

  &:hover {
    opacity: 0.85;
  }
`;

// --- Props 인터페이스 정의 ---
interface NotificationModalProps {
    message: string;
    onClose: () => void; // onClose는 인자를 받지 않고 void를 반환하는 함수
}

// --- NotificationModal 컴포넌트 (TypeScript 적용) ---
const NotificationModal: React.FC<NotificationModalProps> = ({ message, onClose }) => {
    return (
        <Overlay onClick={onClose}>
            <ModalContainer onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                <Message>{message}</Message>
                <ButtonWrapper>
                    <ConfirmButton onClick={onClose}>확인</ConfirmButton>
                </ButtonWrapper>
            </ModalContainer>
        </Overlay>
    );
};

export default NotificationModal;