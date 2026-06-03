import "./globals.css";

import { SessionSync } from "./auth/session-sync";
import { Providers } from "./providers";

export const metadata = {
  title: "RankKit",
  description: "Local-first competitive rating leagues.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <SessionSync />
          {children}
        </Providers>
      </body>
    </html>
  );
}
