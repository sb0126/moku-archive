"use client";

import { useTranslation } from "react-i18next";
import { Breadcrumb } from "@/components/Breadcrumb";

export function GuidelinePage() {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto px-6 py-16 md:py-20 min-h-screen max-w-4xl">
      <Breadcrumb />
      
      <h1 className="text-4xl font-bold mb-8 mt-6 text-[#2C2825]">{t("guideline.title", "H-1 Working Holiday Guideline")}</h1>
      
      <div className="prose prose-zinc dark:prose-invert max-w-none">
        <section className="mb-10">
          <h2 className="text-2xl font-semibold mb-4 text-foreground">{t("guideline.eligibility.title", "Eligibility")}</h2>
          <p className="text-muted-foreground leading-relaxed">
            {t("guideline.eligibility.description", "You must be a citizen of a country that has a Working Holiday agreement with South Korea, typically between the ages of 18 and 30, and without dependents.")}
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold mb-4 text-foreground">{t("guideline.documents.title", "Required Documents")}</h2>
          <ul className="list-disc pl-5 text-muted-foreground space-y-2">
            <li>{t("guideline.documents.item1", "Valid passport and one passport-size photo")}</li>
            <li>{t("guideline.documents.item2", "Visa Application Form")}</li>
            <li>{t("guideline.documents.item3", "Travel itinerary and return flight ticket")}</li>
            <li>{t("guideline.documents.item4", "Proof of financial support (bank statement)")}</li>
            <li>{t("guideline.documents.item5", "Criminal background check")}</li>
            <li>{t("guideline.documents.item6", "Medical certificate")}</li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="text-2xl font-semibold mb-4 text-foreground">{t("guideline.process.title", "Application Process")}</h2>
          <p className="text-muted-foreground leading-relaxed mb-4">
            {t("guideline.process.description", "Submit your documents to the nearest Korean embassy or consulate in your home country.")}
          </p>
        </section>
      </div>
    </div>
  );
}
