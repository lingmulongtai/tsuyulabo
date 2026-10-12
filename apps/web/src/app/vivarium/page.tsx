import { Suspense } from "react";
import { Preview } from "./Preview";
export const metadata = { title: "飼育びん | ツユラボ", description: "小さな命を、マクロレンズで。" };
export default function VivariumPage() {
  return <Suspense><Preview /></Suspense>;
}
