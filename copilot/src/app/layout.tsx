import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { Providers } from './providers';

import './globals.css';

export const metadata: Metadata = {
  title: 'Mila assistant',
  description: 'CopilotKit UI over the LangGraph Mila knowledge agent'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
