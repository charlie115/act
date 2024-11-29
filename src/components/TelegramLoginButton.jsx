// src/components/TelegramLoginButton.jsx
import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useLoginTelegramMutation } from 'redux/api/drf/auth';
import useScript from 'hooks/useScript';

export default function TelegramLoginButton({ buttonId = 'telegram-button' }) {
  const [loginTelegram] = useLoginTelegramMutation();
  const { telegramBot, user } = useSelector((state) => state.auth);

  const dataOnAuth = (telegramUser) => {
    loginTelegram({ user: user?.uuid, ...telegramUser });
  };

  useEffect(() => {
    window.TelegramWidget = { dataOnAuth };
  }, []);

  useScript(
    telegramBot && user && !user?.telegram_chat_id
      ? 'https://telegram.org/js/telegram-widget.js?22'
      : null,
    {
      nodeId: buttonId,
      attributes: {
        'data-onauth': 'TelegramWidget.dataOnAuth(user)',
        'data-request-access': 'write',
        'data-telegram-login': telegramBot,
        'data-size': 'medium',
      },
    },
    []
  );

  return <div id={buttonId} />;
}