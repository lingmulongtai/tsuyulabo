import { HomeScreen } from "@/components/home/HomeScreen";
import { AppShell } from "@/components/shell/AppShell";
import { MOCK_HOME } from "@/lib/mock";

export default function Home() {
  return (
    <AppShell>
      <HomeScreen data={MOCK_HOME} />
    </AppShell>
  );
}
