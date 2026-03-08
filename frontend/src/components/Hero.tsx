"use client";

import Link from "next/link";
import Image from "next/image";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { FadeInSection } from "@/components/FadeInSection";
import { FileText, CheckCircle, Users, Briefcase } from "lucide-react";

export function Hero() {
  const { t } = useTranslation();

  const trustItems = [
    { icon: FileText, label: t("hero.trust1", "Visa Assist") },
    { icon: CheckCircle, label: t("hero.trust2", "100% Success") },
    { icon: Users, label: t("hero.trust3", "Expert Team") },
    { icon: Briefcase, label: t("hero.trust4", "Job Support") },
  ];

  return (
    <section id="hero" className="relative py-32 md:py-48 flex items-center min-h-[85vh] bg-[#2C2825] overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 z-0">
        <Image
          src="https://images.unsplash.com/photo-1601710124519-705a3571e43c?auto=format&fit=crop&w=1920&q=80"
          alt="Seoul Palace Landscape Background"
          fill
          priority
          className="object-cover opacity-90 filter brightness-95 contrast-105 saturate-[0.85] object-center mix-blend-overlay"
        />
        {/* Dark overlay to ensure light text is readable and the image is visible */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#2C2825]/60 via-[#2C2825]/40 to-[#2C2825]/90" />
      </div>

      {/* Fade-out bottom gradient to match the next section's white background */}
      <div className="absolute bottom-0 left-0 right-0 h-48 md:h-72 bg-gradient-to-t from-white to-transparent z-0 pointer-events-none" />

      {/* Centered Content */}
      <div className="container relative z-10 mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto flex flex-col items-center text-center">
          <FadeInSection delay={100} direction="up">
            <span className="inline-block bg-white/10 backdrop-blur-md text-[#F5F3F0] border border-white/20 rounded-full px-5 py-2 text-sm font-medium mb-6">
              {t("hero.subtitle", "韓国ワーキングホリデー専門サポート")}
            </span>
          </FadeInSection>
          
          <FadeInSection delay={200} direction="up">
            <h1 className="text-[48px] md:text-[64px] font-bold leading-[1.2] mb-6 tracking-tight drop-shadow-md">
              <span className="block text-white mb-2">{t("hero.title", "韓国暮らし")}</span>
              <span className="block text-[#D1B075]">{t("hero.titleHighlight", "MOKUで一歩づつ")}</span>
            </h1>
          </FadeInSection>

          <FadeInSection delay={300} direction="up">
            <p className="text-lg text-white/90 font-medium leading-[1.65] max-w-2xl mx-auto mb-10 drop-shadow-md">
              {t("hero.description", "複雑なビザ申請から韓国での生活まで。\nあなたの夢を叶えるすべてのサポートを、真心を込めて提供します。").split('\n').map((line, i) => (
                <span key={i} className="block">{line}</span>
              ))}
            </p>
          </FadeInSection>

          <FadeInSection delay={400} direction="up">
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16 w-full">
              <Button asChild className="rounded-full px-9 py-6 bg-[#B8935F] text-white shadow-lg hover:bg-[#A38568] hover:shadow-xl text-base h-auto transition-all border border-[#B8935F]">
                <Link href="#inquiry">{t("hero.cta.primary", "Start Consultation")}</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-full px-9 py-6 border border-white/30 bg-white/10 backdrop-blur-md text-white hover:bg-white/20 hover:shadow-md text-base h-auto transition-all">
                <Link href="/guideline">{t("hero.cta.secondary", "Read Guideline")}</Link>
              </Button>
            </div>
          </FadeInSection>

          <FadeInSection delay={500} direction="up">
            <div className="flex flex-wrap justify-center gap-6 sm:gap-10 w-full mt-8">
              {trustItems.map((item, idx) => (
                <div key={idx} className="flex flex-col items-center gap-3 group cursor-pointer">
                  <div className="w-14 h-14 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center shadow-lg border border-white/30 transition-all duration-300 group-hover:bg-white/30 group-hover:-translate-y-1">
                    <item.icon className="w-6 h-6 text-[#D1B075] drop-shadow-sm" />
                  </div>
                  <span className="text-sm font-bold text-white tracking-wide drop-shadow-md">{item.label}</span>
                </div>
              ))}
            </div>
          </FadeInSection>
        </div>
      </div>
    </section>
  );
}
