# community_web_next

Official Next.js frontend for ACW public pages.

## Environment

- `NEXT_PUBLIC_SITE_URL`: canonical site URL
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID`: Google OAuth client id for login
- `ACW_API_SERVER_URL`: server-side DRF API base, for example `http://drf:8000/api`
- `ACW_API_PROXY_TARGET`: client-side proxy target, for example `http://drf:8000`
- `NEXT_PUBLIC_DRF_URL`: public DRF origin used to resolve media URLs in rich content

## Commands

```bash
pnpm install
pnpm dev
pnpm build
pnpm start
```

## Current Scope

- public traffic is routed here through the main community nginx entrypoint
- authenticated and bot-heavy routes still render migration placeholders where parity work is pending
