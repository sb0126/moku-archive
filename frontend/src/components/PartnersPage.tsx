"use client";

import { useTranslation } from "react-i18next";
import { Handshake, Building2, Globe2 } from "lucide-react";

export function PartnersPage() {
  const { t } = useTranslation();

  const partners = [
    { name: "Partner 1", nameKey: "partners.list.partner1.title", desc: "partners.list.partner1.desc", icon: Handshake },
    { name: "Partner 2", nameKey: "partners.list.partner2.title", desc: "partners.list.partner2.desc", icon: Building2 },
    { name: "Partner 3", nameKey: "partners.list.partner3.title", desc: "partners.list.partner3.desc", icon: Globe2 },
  ];

  return (
    <div className="bg-[#FAFAF9] min-h-screen py-16 md:py-20">
      <div className="container mx-auto px-6 max-w-6xl">
        <h1 className="text-4xl font-bold mb-8 text-center text-[#2C2825]">{t("partners.title", "Our Partners")}</h1>
        <p className="text-center text-[#6B6660] mb-12 max-w-2xl mx-auto">
          {t("partners.description", "We work with selected partners to provide the best experience for your Korean Working Holiday.")}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {partners.map((p, idx) => {
            const Icon = p.icon;
            return (
              <div key={idx} className="bg-white rounded-2xl p-8 shadow-sm border border-[#2C2825]/6 hover:shadow-md transition-shadow">
                <Icon className="w-12 h-12 text-[#B8935F] mb-6" />
                <h3 className="text-xl font-semibold mb-2 text-[#2C2825]">{t(p.nameKey, p.name)}</h3>
                <p className="text-[#6B6660] text-sm leading-relaxed">{t(p.desc, "Partner description goes here.")}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
