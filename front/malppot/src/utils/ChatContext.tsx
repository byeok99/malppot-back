import React, { createContext, useContext, useState } from "react";

interface Message {
  speaker: string;
  transcript: string;
}

interface ChatContextType {
  messages: Message[];
  addMessage: (speaker: string, transcript: string) => void;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);

  const addMessage = (speaker: string, transcript: string) => {
    setMessages(prev => [...prev, { speaker, transcript }]);
  };

  const clearMessages = () => setMessages([]);

  return (
    <ChatContext.Provider value={{ messages, addMessage, clearMessages }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};