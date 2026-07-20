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
  gap: 0.75rem;
`;

const Button = styled.button`
  flex: 1;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #ddd;

  &:hover {
    opacity: 0.85;
  }
`;

const ConfirmButton = styled(Button)`
  background-color: #6a9b3e;
  color: white;
  border-color: #6a9b3e;
`;

const CancelButton = styled(Button)`
  background-color: #f1f1f1;
  color: #555;
`;

// --- Props 인터페이스 정의 ---
interface ModalProps {
    message: string;
    onConfirm: () => void; // 인자를 받지 않고 void를 반환하는 함수
    onCancel: () => void;  // 인자를 받지 않고 void를 반환하는 함수
}

// --- Modal 컴포넌트 (TypeScript 적용) ---
const Modal: React.FC<ModalProps> = ({ message, onConfirm, onCancel }) => {
    return (
        <Overlay onClick={onCancel}> {/* 오버레이 클릭 시 onCancel(모달 닫기) 실행 */}
            <ModalContainer onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                <Message>{message}</Message>
                <ButtonWrapper>
                    <CancelButton onClick={onCancel}>아니오</CancelButton>
                    <ConfirmButton onClick={onConfirm}>예</ConfirmButton>
                </ButtonWrapper>
            </ModalContainer>
        </Overlay>
    );
};

export default Modal;