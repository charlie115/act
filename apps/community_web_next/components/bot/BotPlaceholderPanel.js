export default function BotPlaceholderPanel({ title = "패널을 선택하세요", description = "좌측 메뉴에서 원하는 기능을 선택합니다." }) {
  return (
    <div className="grid min-h-[40vh] place-items-center rounded-xl border border-border bg-surface">
      <div className="text-center space-y-2">
        <p className="text-lg font-semibold text-ink-muted">{title}</p>
        <p className="text-sm text-ink-muted/60">{description}</p>
      </div>
    </div>
  );
}
