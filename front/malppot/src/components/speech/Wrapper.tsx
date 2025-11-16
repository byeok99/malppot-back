import React from "react";
import styled from "styled-components";

const StyledWrapper = styled.div`
  max-width: 540px;
  margin: 0 auto;
  padding: 40px 20px 80px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
`;

const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <StyledWrapper>{children}</StyledWrapper>;
};

export default Wrapper;