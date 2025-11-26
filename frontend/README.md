# Frontend - AI Platform

Next.js frontend for AI Autonomous Knowledge & Workflow Platform.

## Features

- **Chat Interface**: Real-time chat with AI
- **Document Upload**: Upload PDF, DOCX, TXT, images
- **Document Management**: View, track, and delete documents
- **Real-time Status**: Auto-refresh document processing status
- **Dark Mode**: Supports light and dark themes

## Tech Stack

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Axios

## Getting Started

### Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

### Docker

```bash
docker build -t ai-platform-frontend .
docker run -p 3000:3000 ai-platform-frontend
```

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Components

- `Chat.tsx` - Chat interface with message history
- `DocumentUpload.tsx` - File upload form
- `DocumentList.tsx` - Document list with stats

## API Integration

See `lib/api.ts` for all API calls:
- Chat: `POST /api/v1/chat`
- Upload: `POST /api/v1/documents/upload`
- List: `GET /api/v1/documents/`
- Delete: `DELETE /api/v1/documents/{id}`
- Stats: `GET /api/v1/documents/stats/indexing`
