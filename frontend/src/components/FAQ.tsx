"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { FadeInSection } from "@/components/FadeInSection";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function FAQ() {
  const { t } = useTranslation();
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  // Fallback items. In a real scenario, map over an array of keys from i18n
  const faqItems = [
    {
      q: t("faq.item1.q", "Am I eligible for the H-1 visa?"),
      a: t("faq.item1.a", "You must be a citizen of a country that has a Working Holiday agreement with South Korea, typically between the ages of 18 and 30, and without dependents."),
    },
    {
      q: t("faq.item2.q", "How long does the application process take?"),
      a: t("faq.item2.a", "Typically, document preparation takes 1-2 weeks, and the embassy processing takes another 1-2 weeks. The entire process takes about a month."),
    },
    {
      q: t("faq.item3.q", "Do I need to speak Korean perfectly?"),
      a: t("faq.item3.a", "No, while basic Korean is helpful, the H-1 visa does not have a strict language requirement. We also provide initial settlement support to help you get started."),
    },
    {
      q: t("faq.item4.q", "Can you help me find housing in Korea?"),
      a: t("faq.item4.a", "Yes! Our settlement package includes assistance with finding safe and affordable housing depending on your budget and preferred location in Seoul."),
    },
  ];

  const handleToggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="bg-white py-28 md:py-36">
      <div className="container mx-auto px-6 max-w-3xl">
        <FadeInSection>
          <div className="text-center mb-16">
            <h2 className="text-[32px] md:text-[40px] font-bold tracking-tight text-[#2C2825] mb-4">
              {t("faq.title", "Frequently Asked Questions")}
            </h2>
            <p className="text-[#6B6660] text-lg">
              {t("faq.description", "Got questions? We've got answers. If you can't find what you're looking for, feel free to contact us.")}
            </p>
          </div>
        </FadeInSection>

        <div className="space-y-4 mb-16">
          {faqItems.map((item, idx) => (
            <FadeInSection key={idx} delay={idx * 100}>
              <div className="rounded-2xl border border-[#2C2825]/6 px-6 bg-white overflow-hidden transition-all hover:shadow-md hover:border-[#2C2825]/10">
                <button
                  type="button"
                  onClick={() => handleToggle(idx)}
                  className="w-full flex items-center justify-between py-6 text-left focus:outline-none group"
                  aria-expanded={openIndex === idx}
                >
                  <span className="font-semibold text-[17px] text-[#2C2825] group-hover:text-[#8A6420] transition-colors pr-8">
                    {item.q}
                  </span>
                  <ChevronDown
                    className={cn(
                      "w-5 h-5 text-[#6B6660] transition-transform duration-300 shrink-0",
                      openIndex === idx ? "rotate-180 text-[#8A6420]" : ""
                    )}
                  />
                </button>
                <div
                  className={cn(
                    "overflow-hidden transition-all duration-300 ease-in-out",
                    openIndex === idx ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                  )}
                >
                  <p className="text-[#6B6660] text-[15px] pb-6 leading-relaxed">
                    {item.a}
                  </p>
                </div>
              </div>
            </FadeInSection>
          ))}
        </div>

        <FadeInSection delay={400} className="flex justify-center">
          <Button asChild className="rounded-full px-10 py-6 bg-[#B8935F] text-white hover:bg-[#9E7030] text-[15px] font-semibold h-auto shadow-sm hover:shadow-md transition-all">
            <Link href="#inquiry">{t("faq.cta", "お問い合わせフォームへ")}</Link>
          </Button>
        </FadeInSection>
      </div>
    </section>
  );
}
