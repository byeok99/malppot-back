import React from "react";
import styled from "styled-components";

const Video = styled.video`
  width: 100%;
  max-width: 400px;
  border-radius: 8px;
  background: #000;
`;

const VideoPlayer: React.FC<{ videoUrl: string | null }> = ({ videoUrl }) => {
  if (!videoUrl) return null;
  return <Video src={videoUrl} controls />;
};

export default VideoPlayer;