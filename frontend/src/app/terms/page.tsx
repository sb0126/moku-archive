import { Metadata } from "next";
import { TermsPage } from "@/components/TermsPage";

export const metadata: Metadata = {
  title: "Terms of Service | Moku",
  description: "Moku Terms of Service",
};

export default function Page() {
  return <TermsPage />;
}
