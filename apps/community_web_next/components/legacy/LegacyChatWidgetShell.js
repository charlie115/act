"use client";

import { MemoryRouter } from "react-router-dom";

import ChatWidget from "components/chat_widget";

export default function LegacyChatWidgetShell({ isVisible, onStateChange }) {
  return (
    <MemoryRouter initialEntries={["/"]}>
      <ChatWidget isVisible={isVisible} onStateChange={onStateChange} />
    </MemoryRouter>
  );
}
