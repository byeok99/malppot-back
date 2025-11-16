import React from 'react';
import Character from 'components/malbeot/Character';

interface Props {
    isSpeaking: boolean;
}

const CharacterRenderer: React.FC<Props> = ({ isSpeaking }) => {
    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            width: '100%',
        }}>
            <Character isSpeaking={isSpeaking} />
        </div>
    );
};

export default CharacterRenderer;