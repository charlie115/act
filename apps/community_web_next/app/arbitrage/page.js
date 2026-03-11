import { redirect } from "next/navigation";

export default function ArbitrageIndexPage() {
  redirect("/arbitrage/funding-rate/diff");
}
