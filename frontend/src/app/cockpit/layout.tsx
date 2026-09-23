import { AuthGate } from '@/components/auth/AuthGate';

export default function CockpitLayout({ children }: { children: React.ReactNode }) {
    return <AuthGate>{children}</AuthGate>;
}