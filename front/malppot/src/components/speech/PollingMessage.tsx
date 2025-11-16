import React from "react";
import styled from "styled-components";

const Message = styled.div`
  font-size: 16px;
  color: #888;
`;

const RetryButton = styled.button`
  margin-top: 12px;
  background-color: #ffe0e0;
  border: 1px solid #ccc;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
`;

const PollingMessage: React.FC<{
  message: string;
  status: string;
  onRetry: () => void;
}> = ({ message, status, onRetry }) => {
  if (!message) return null;
  return (
    <>
      <Message>{message}</Message>
      {status === "failed" && <RetryButton onClick={onRetry}>🔁 영상 다시 시도</RetryButton>}
    </>
  );
};

export default PollingMessage;