// // 입모양 제어를 위하 컴포넌트
// import { useEffect, useRef } from 'react';
// import { useAudioProcessor } from 'utils/useAudioProcessor';

// const CharacterMouth = () => {
//     const audioLevel = useAudioProcessor();
//     const shapeKeyRef = useRef(0);

//     // 오디오 레벨에 따라 Shape Key 조절
//     useEffect(() => {
//         const mouthMovement = Math.min(audioLevel / 100, 1);  // 오디오 레벨을 0~1 범위로 변환
//         shapeKeyRef.current = mouthMovement;  // Shape Key 값 업데이트
//         console.log(`👄 Shape Key: ${mouthMovement}`);
//     }, [audioLevel]);

//     return (
//         <div>
//             <h2>🎙️ 캐릭터 입 모양</h2>
//             <p>현재 오디오 레벨: {audioLevel.toFixed(2)}</p>
//             <p>Shape Key 값: {shapeKeyRef.current.toFixed(2)}</p>
//         </div>
//     );
// };

// export default CharacterMouth;
