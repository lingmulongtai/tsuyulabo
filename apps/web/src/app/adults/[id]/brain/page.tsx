import { BrainScreen } from "@/components/brain/BrainScreen";

export default async function BrainPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <BrainScreen flyId={id} />;
}
