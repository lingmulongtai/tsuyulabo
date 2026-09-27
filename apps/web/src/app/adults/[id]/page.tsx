import { AdultDetail } from "@/components/brain/AdultDetail";

export default async function AdultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AdultDetail id={id} />;
}
