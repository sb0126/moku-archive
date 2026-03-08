import { Metadata } from "next";
import { PrivacyPage } from "@/components/PrivacyPage";

export const metadata: Metadata = {
  title: "Privacy Policy | Moku",
  description: "Moku Privacy Policy",
};

export default function Page() {
  return <PrivacyPage />;
}
