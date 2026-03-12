"use client";

import Deposit from "pages/bot/Deposit";
import LegacyOutletContextRouter from "../legacy/LegacyOutletContextRouter";

export default function LegacyBotDepositClient({ marketCodeCombination }) {
  return (
    <div className="legacy-surface legacy-surface--bot">
      <LegacyOutletContextRouter context={{ marketCodeCombination }}>
        <Deposit />
      </LegacyOutletContextRouter>
    </div>
  );
}
