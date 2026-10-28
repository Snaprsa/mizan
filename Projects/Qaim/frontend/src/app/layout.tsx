import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Qaim — Real Estate Valuation',
    description: 'Saudi real estate valuation workflow',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>
                <nav className="nav">
                    <a href="/" className="nav-logo">Qaim</a>
                    <span className="nav-label">Real Estate Valuation</span>
                </nav>
                {children}
            </body>
        </html>
    );
}
