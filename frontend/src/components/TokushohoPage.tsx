"use client";

import { useTranslation } from "react-i18next";
import { Breadcrumb } from "@/components/Breadcrumb";

export function TokushohoPage() {
  const { t } = useTranslation();

  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-16 md:pt-20">
      <div className="container mx-auto px-6 max-w-4xl pb-16 mt-4">
        <Breadcrumb />
        
        <h1 className="text-4xl font-bold mb-8 mt-6 text-[#2C2825]">{t("tokushoho.title", "Act on Specified Commercial Transactions")}</h1>
        
        <div className="prose prose-zinc max-w-none text-[#6B6660] leading-relaxed">
          <table className="w-full text-left border-collapse border border-[#2C2825]/10 mt-8 bg-white rounded-lg overflow-hidden">
            <tbody>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] w-1/3 bg-zinc-50">{t("tokushoho.companyName.label", "Company Name")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.companyName.value", "Moku Agency")}</td>
              </tr>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] bg-zinc-50">{t("tokushoho.representative.label", "Representative")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.representative.value", "John Doe")}</td>
              </tr>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] bg-zinc-50">{t("tokushoho.address.label", "Address")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.address.value", "123 Seoul Street, Seoul, South Korea")}</td>
              </tr>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] bg-zinc-50">{t("tokushoho.contact.label", "Contact")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.contact.value", "support@moku.com / +82-10-0000-0000")}</td>
              </tr>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] bg-zinc-50">{t("tokushoho.price.label", "Price")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.price.value", "Displayed on the service page")}</td>
              </tr>
              <tr className="border-b border-[#2C2825]/10">
                <th className="p-4 font-semibold text-[#2C2825] bg-zinc-50">{t("tokushoho.payment.label", "Payment Methods")}</th>
                <td className="p-4 bg-white text-[#6B6660]">{t("tokushoho.payment.value", "Credit Card, Bank Transfer")}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
