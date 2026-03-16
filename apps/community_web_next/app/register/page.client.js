"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import AuthCard from "../../components/auth/AuthCard";
import { useAuth } from "../../components/auth/AuthProvider";
import { REGEX } from "../../lib/constants";

function validateUsername(value) {
  if (!value) {
    return "사용자 이름을 입력하세요";
  }

  if (!REGEX.usernameFirstCharacter.test(value)) {
    return "사용자 이름은 문자로 시작해야 합니다";
  }

  if (!REGEX.usernameFull.test(value)) {
    return "영문, 숫자, 밑줄(_), 마침표(.)만 사용 가능합니다";
  }

  if (value.match(REGEX.koreanCharacters)) {
    if (value.length < 2 || value.length > 12) {
      return "한글 이름은 2~12자여야 합니다";
    }
    return "";
  }

  if (value.length < 6 || value.length > 25) {
    return "영문 이름은 6~25자여야 합니다";
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
      description="커뮤니티에서 사용할 이름을 설정하세요."
      eyebrow="회원가입"
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
          사용자 이름
        </label>
        <input
          autoComplete="off"
          className="auth-form__input"
          id="username"
          onChange={(event) => {
            clearError();
            setUsername(event.target.value);
          }}
          placeholder="사용자 이름 입력"
          value={username}
        />
        <button
          className="primary-button auth-button"
          disabled={Boolean(validationMessage) || isLoading || !isVisitor}
          type="submit"
        >
          {isLoading ? "저장 중..." : "계속"}
        </button>
      </form>
    </AuthCard>
  );
}
