import React from "react";
import styled from "styled-components";

interface InputBoxProps {
  inputText: string;
  setInputText: (val: string) => void;
  handleInputSubmit: () => void;
}

const InputContainer = styled.div`
  background-color: #A6D785;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 16px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
`;

const StyledInput = styled.input`
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  border-radius: 10px;
  border: 1px solid #ccc;
`;

const Icon = styled.span`
  font-size: 18px;
  margin-left: 12px;
  cursor: pointer;
`;

const InputBox: React.FC<InputBoxProps> = ({ inputText, setInputText, handleInputSubmit }) => {
  return (
    <InputContainer>
      <StyledInput
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleInputSubmit()}
        placeholder="예: 저는 오늘 학교에 갔어요"
      />
      <Icon onClick={handleInputSubmit}>↩️</Icon>
    </InputContainer>
  );
};

export default InputBox;