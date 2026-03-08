"use client";

import { useTranslation } from "react-i18next";
import { Breadcrumb } from "@/components/Breadcrumb";

export function TermsPage() {
  const { t } = useTranslation();

  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-16 md:pt-20">
      <div className="container mx-auto px-6 max-w-4xl pb-16 mt-4">
        <Breadcrumb />
        
        <h1 className="text-4xl font-bold mb-8 mt-6 text-[#2C2825]">{t("terms.title", "Terms of Service")}</h1>
        
        <div className="prose prose-zinc max-w-none text-[#6B6660] leading-relaxed">
          <p>{t("terms.intro", "By using the Moku service, you agree to these terms.")}</p>

          <h2 className="text-2xl font-semibold mb-4 mt-10 text-[#2C2825]">{t("terms.service.title", "Service Description")}</h2>
          <p>{t("terms.service.content", "Moku provides consultation and support for the Korea H-1 Working Holiday visa.")}</p>
          
          <h2 className="text-2xl font-semibold mb-4 mt-10 text-[#2C2825]">{t("terms.liability.title", "Limitation of Liability")}</h2>
          <p>{t("terms.liability.content", "Moku is not responsible for visa rejections by the embassy.")}</p>
        </div>
      </div>
    </div>
  );
}
