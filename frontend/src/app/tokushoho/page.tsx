import { Metadata } from "next";
import { TokushohoPage } from "@/components/TokushohoPage";

export const metadata: Metadata = {
  title: "Specified Commercial Transactions | Moku",
  description: "Notation based on the Act on Specified Commercial Transactions",
};

export default function Page() {
  return <TokushohoPage />;
}
