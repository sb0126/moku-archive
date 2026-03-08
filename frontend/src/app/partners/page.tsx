import { Metadata } from "next";
import { PartnersPage } from "@/components/PartnersPage";

export const metadata: Metadata = {
  title: "Partners | Moku",
  description: "Our dedicated partners to help you settle in Korea",
};

export const revalidate = 86400; // SSG + ISR 1 day

export default function Page() {
  return <PartnersPage />;
}
