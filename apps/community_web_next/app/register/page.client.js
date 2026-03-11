"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import AuthCard from "../../components/auth/AuthCard";
import { useAuth } from "../../components/auth/AuthProvider";
import { REGEX } from "../../lib/constants";

function validateUsername(value) {
  if (!value) {
    return "Please enter a username";
  }

  if (!REGEX.usernameFirstCharacter.test(value)) {
    return "Username must start with a letter";
  }

  if (!REGEX.usernameFull.test(value)) {
    return "Username may only include letters, numbers, underscores, and periods";
  }

  if (value.match(REGEX.koreanCharacters)) {
    if (value.length < 2 || value.length > 12) {
      return "Username must have 2 to 12 characters";
    }
    return "";
  }

  if (value.length < 6 || value.length > 25) {
    return "Username must have 6 to 25 characters";
  }

  return "";
}

export default function RegisterClientPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const { clearError, error, isLoading, isReady, isVisitor, loggedIn, registerUsername, user } =
    useAuth();

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (!user) {
      router.replace("/login");
      return;
    }

    if (loggedIn) {
      router.replace("/");
    }
  }, [isReady, loggedIn, router, user]);

  const validationMessage = useMemo(() => validateUsername(username), [username]);

  return (
    <AuthCard
      description={`${
        user?.first_name || "New"
      } 계정에 사용자 이름을 설정하면 기존 CRA와 같은 플로우로 메인 서비스에 진입합니다.`}
      eyebrow="Onboarding"
      error={error || validationMessage}
      title="사용자 이름 등록"
    >
      <form
        className="auth-form"
        onSubmit={async (event) => {
          event.preventDefault();

          if (validationMessage || !isVisitor) {
            return;
          }

          await registerUsername(username.toLowerCase());
          router.replace("/");
        }}
      >
        <label className="auth-form__field" htmlFor="username">
          Username
        </label>
        <input
          autoComplete="off"
          className="auth-form__input"
          id="username"
          onChange={(event) => {
            clearError();
            setUsername(event.target.value);
          }}
          placeholder="Enter username"
          value={username}
        />
        <button
          className="primary-button auth-button"
          disabled={Boolean(validationMessage) || isLoading || !isVisitor}
          type="submit"
        >
          {isLoading ? "Saving..." : "Continue"}
        </button>
      </form>
    </AuthCard>
  );
}
