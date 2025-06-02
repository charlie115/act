# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install dependencies
pnpm install

# Start development server (runs on localhost:3000)
pnpm start

# Build for production
pnpm run build:production

# Build for test environment
pnpm run build:test

# Run linting
pnpm run lint

# Scan for i18n translations
pnpm run scan:i18n
```

## Architecture Overview

This is a React-based cryptocurrency trading web application built with:

- **React 18.2** with Create React App
- **Redux Toolkit** for state management with RTK Query for API calls
- **Material-UI v5** for UI components and theming
- **React Router v6** for routing with lazy-loaded pages
- **WebSocket** connections for real-time trading data

### Key Patterns

1. **API Layer**: Uses RTK Query with two main API services:
   - `drf/` - REST API endpoints for auth, trading, wallet, etc.
   - `websocket/` - Real-time data streams for chat and price data

2. **Component Structure**:
   - Shared components in `src/components/`
   - Page components in `src/pages/` (lazy loaded)
   - Table components with custom renderers in `src/components/tables/`

3. **Theming**: Light/dark theme support via MUI theme provider in `src/configs/theme/`

4. **i18n**: Multi-language support (EN, KO, ZH) with translations in `src/assets/translations/`

5. **Routing**: Centralized route configuration in `src/configs/router/` with protected routes

### Environment Configuration

- Uses `.env.test` and `.env.production` files
- Development proxy configured in `setupProxy.js` for API calls
- Absolute imports enabled via `jsconfig.json`

### Important Notes

- Package manager: **pnpm** (not npm or yarn)
- Node version: 18.15.0
- All API calls should use the RTK Query endpoints in `src/redux/api/`
- Theme colors and components are configured in `src/configs/theme/`
- WebSocket connections are managed in `src/redux/api/websocket/`