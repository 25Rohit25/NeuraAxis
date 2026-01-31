# @neuraxis/web

> Next.js 15 Frontend for NEURAXIS Medical Diagnosis Platform

## Overview

This is the main frontend application for NEURAXIS, built with Next.js 15 using the App Router architecture. It provides a modern, responsive interface for healthcare professionals to interact with AI-powered diagnostic tools.

## Features

- 🚀 **Next.js 15** with App Router and Server Components
- 🎨 **Tailwind CSS** for utility-first styling
- 📦 **TypeScript** for type safety
- 🔐 **NextAuth.js** for authentication
- 🗃️ **Zustand** for state management
- 📊 **React Query** for server state
- ♿ **Accessible** components following WCAG guidelines

## Project Structure

```
src/
├── app/                    # App Router pages and layouts
│   ├── (auth)/            # Authentication routes
│   ├── (dashboard)/       # Protected dashboard routes
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── ui/               # Base UI components
│   ├── features/         # Feature-specific components
│   └── layouts/          # Layout components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
├── stores/               # Zustand stores
├── styles/               # Global styles
└── types/                # TypeScript types
```

## Getting Started

```bash
# From the monorepo root
npm run dev --filter=@neuraxis/web

# Or from this directory
npm run dev
```

## Environment Variables

See `.env.example` in the project root for required environment variables.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | TypeScript type checking |
| `npm run test` | Run tests |

## Key Dependencies

- **next**: ^15.0.0
- **react**: ^18.3.0
- **tailwindcss**: ^3.4.0
- **next-auth**: ^5.0.0
- **zustand**: ^4.4.0
- **@tanstack/react-query**: ^5.17.0
