import { buildMetadata } from "../../lib/site";
import RegisterClientPage from "./page.client";

export const metadata = {
  ...buildMetadata({
    title: "Register",
    description: "방문자 계정에 사용자 이름을 등록해 ACW 서비스를 계속 사용합니다.",
    pathname: "/register",
  }),
  robots: {
    index: false,
    follow: false,
  },
};

export default function RegisterPage() {
  return <RegisterClientPage />;
}
