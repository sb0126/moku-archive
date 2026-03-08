"use client";

import { useTranslation } from "react-i18next";
import { Breadcrumb } from "@/components/Breadcrumb";

export function PrivacyPage() {
  const { t } = useTranslation();

  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-16 md:pt-20">
      <div className="container mx-auto px-6 max-w-4xl pb-16 mt-4">
        <Breadcrumb />
        
        <h1 className="text-4xl font-bold mb-8 mt-6 text-[#2C2825]">{t("privacy.title", "Privacy Policy")}</h1>
        
        <div className="prose prose-zinc max-w-none text-[#6B6660] leading-relaxed">
          <p>{t("privacy.intro", "This is the privacy policy for Moku.")}</p>
          
          <h2 className="text-2xl font-semibold mb-4 mt-10 text-[#2C2825]">{t("privacy.dataCollection.title", "Data Collection")}</h2>
          <p>{t("privacy.dataCollection.content", "We collect minimal personal data required for consultation.")}</p>
          
          <h2 className="text-2xl font-semibold mb-4 mt-10 text-[#2C2825]">{t("privacy.dataUsage.title", "Data Usage")}</h2>
          <p>{t("privacy.dataUsage.content", "Collected data is solely used to assist with the H-1 visa application process.")}</p>
        </div>
      </div>
    </div>
  );
}
