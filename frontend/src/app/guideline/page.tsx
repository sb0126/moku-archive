import { Metadata } from "next";
import { GuidelinePage } from "@/components/GuidelinePage";

export const metadata: Metadata = {
  title: "Guideline | Moku",
  description: "Korea H-1 Working Holiday Guideline",
};

export default function Page() {
  return <GuidelinePage />;
}
