export default function Loading() {
  return (
    <div className="mx-auto grid min-h-[40vh] w-[min(1280px,calc(100vw-24px))] place-items-center">
      <div className="grid gap-3 text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
        <p className="text-sm text-ink-muted">로딩 중...</p>
      </div>
    </div>
  );
}
