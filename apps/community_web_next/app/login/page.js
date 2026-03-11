import { buildMetadata } from "../../lib/site";
import LoginClientPage from "./page.client";

export const metadata = {
  ...buildMetadata({
    title: "Login",
    description: "Google 계정으로 ACW 계정에 로그인합니다.",
    pathname: "/login",
  }),
  robots: {
    index: false,
    follow: false,
  },
};

export default async function LoginPage({ searchParams }) {
  const resolvedSearchParams = await searchParams;
  return <LoginClientPage nextPath={resolvedSearchParams?.next} />;
}
