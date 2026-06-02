import "./globals.css";

export const metadata = {
  title: "RankKit",
  description: "Local-first competitive rating leagues.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
