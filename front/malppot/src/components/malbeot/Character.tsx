import Lottie from "lottie-react";
import talkingAnimation from "assets/models/talking.json";
import waitingAnimation from "assets/models/waiting.json";

const Character = ({ isSpeaking = true }) => {
    return (
        <div style={{ width: 500, height: 500 }}>
            <Lottie
                animationData={isSpeaking ? talkingAnimation : waitingAnimation}
                loop
                autoplay
            />
        </div>
    );
};

export default Character;
