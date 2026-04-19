import type { Metadata } from 'next';
import './globals.css';
import { ToastProvider } from '@/components/ui/ToastProvider';

export const metadata: Metadata = {
    title: 'LexIntellectus — ERP Legal SaaS',
    description: 'ERP SaaS para el sector legal nicaragüense. Gestión procesal, notarial, financiera y asistente legal con IA.',
    keywords: ['ERP', 'Legal', 'SaaS', 'Nicaragua', 'Abogados', 'Notaría', 'Gestión Legal'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="es">
            <body className="min-h-screen">
                <ToastProvider>
                    {children}
                </ToastProvider>
            </body>
        </html>
    );
}
