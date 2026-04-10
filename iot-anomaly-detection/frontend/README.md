# Frontend Development Guide

## Starting the Frontend

### Option 1: Local Development
```bash
npm install
npm run dev
```

Open http://localhost:3000

### Option 2: Production Build
```bash
npm install
npm run build
npm start
```

### Option 3: Docker
```bash
docker build -t anomaly-ui .
docker run -p 3000:3000 anomaly-ui
```

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main dashboard
│   └── globals.css         # Global styles
│
├── components/
│   ├── Header.tsx          # Top navigation
│   ├── Footer.tsx          # Footer
│   ├── DashboardOverview.tsx   # KPI cards
│   ├── AnomalyAlerts.tsx       # Alert list
│   └── SignalMonitoring.tsx    # Signal grid
│
├── lib/
│   └── api.ts              # API client
│
└── constants.ts            # Config values
```

## Components

### DashboardOverview
- KPI cards (Health, Signals, Alerts, Uptime)
- Anomaly distribution (Pie chart)
- Trend over time (Bar chart)

### AnomalyAlerts
- Live alert feed with severity colors
- Click to see details
- Suggested investigation paths

### SignalMonitoring
- Interactive signal grid
- Real-time value updates
- 30-min historical chart
- Deviation tracking

## Styling

Uses **Tailwind CSS** with custom theme:
- Dark background: `#0f172a`
- Primary: `#0ea5e9` (cyan)
- Success: `#10b981` (green)
- Warning: `#f59e0b` (amber)
- Critical: `#dc2626` (red)

## Adding Features

### New API Endpoint
1. Add to `src/lib/api.ts`
2. Create component
3. Add to `src/app/page.tsx`

### New Chart
Use `recharts` library:
```tsx
import { LineChart, Line, XAxis, YAxis } from 'recharts';

<LineChart data={data}>
  <XAxis dataKey="time" />
  <YAxis />
  <Line type="monotone" dataKey="value" stroke="#0ea5e9" />
</LineChart>
```

## Customization

### Change Colors
Edit `tailwind.config.ts`:
```ts
colors: {
  primary: '#0ea5e9',  // Cyan
  // ...
}
```

### Change API URL
Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://your-api:8000
```

## Performance

- Component code-splitting: Automatic
- Image optimization: Next.js built-in
- CSS minification: Production build
- Bundle size: ~250KB (optimized)

## Debugging

Enable verbose logging in browser DevTools:
```js
localStorage.debug = 'anomaly:*'
```

## Deployment

### Vercel (Recommended)
```bash
npm i -g vercel
vercel
```

### AWS Amplify
```bash
amplify init
amplify hosting add
```

### Docker
```bash
docker build -t anomaly-ui .
docker run -p 3000:3000 anomaly-ui
```

## Environment Variables

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
