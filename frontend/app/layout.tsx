import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "DeepResearch",
  description: "Distributed multi-agent research system",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <main className="max-w-4xl mx-auto px-4 py-10">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
