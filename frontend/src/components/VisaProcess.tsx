"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FadeInSection } from "@/components/FadeInSection";
import { Send, FileText, CheckCircle, Plane, Home, Briefcase, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function VisaProcess() {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      id: "step1",
      icon: Send,
      title: t("process.step1.title", "1. Consultation"),
      desc: t("process.step1.desc", "Schedule an initial call to check your eligibility and create a tailored plan."),
      duration: t("process.step1.duration", "1-2 Days"),
      tip: t("process.step1.tip", "Gather basic information before the call.")
    },
    {
      id: "step2",
      icon: FileText,
      title: t("process.step2.title", "2. Documentation"),
      desc: t("process.step2.desc", "We assist with gathering, translating, and preparing all required documents."),
      duration: t("process.step2.duration", "1-2 Weeks"),
      tip: t("process.step2.tip", "We provide translation services for all documents.")
    },
    {
      id: "step3",
      icon: CheckCircle,
      title: t("process.step3.title", "3. Submit Application"),
      desc: t("process.step3.desc", "Submit your final application to the embassy with zero errors."),
      duration: t("process.step3.duration", "2-3 Weeks"),
      tip: t("process.step3.tip", "Embassy processing times may vary.")
    },
    {
      id: "step4",
      icon: Plane,
      title: t("process.step4.title", "4. Arrival in Korea"),
      desc: t("process.step4.desc", "Arrive in Korea safely with our pre-departure guidelines and checklist."),
      duration: t("process.step4.duration", "Day 1"),
      tip: t("process.step4.tip", "Airport pickup can be arranged.")
    },
    {
      id: "step5",
      icon: Home,
      title: t("process.step5.title", "5. Housing Setup"),
      desc: t("process.step5.desc", "Find safe and affordable housing depending on your budget and preferred location."),
      duration: t("process.step5.duration", "Week 1"),
      tip: t("process.step5.tip", "We partner with trusted local realtors.")
    },
    {
      id: "step6",
      icon: Briefcase,
      title: t("process.step6.title", "6. Job & Life"),
      desc: t("process.step6.desc", "Receive ongoing support for job hunting, banking, phone setup, and local life."),
      duration: t("process.step6.duration", "Ongoing"),
      tip: t("process.step6.tip", "Join our community events in Seoul.")
    },
  ];

  return (
    <section id="visa-process" className="bg-white py-28 md:py-36">
      <div className="container mx-auto px-6">
        <FadeInSection>
          <div className="text-center mb-10">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-[#2C2825] mb-4">
              {t("process.mainTitle", "Simple 6-Step Process")}
            </h2>
            <p className="text-[#6B6660] text-lg max-w-xl mx-auto">
              {t("process.mainDescription", "From your first inquiry to stepping off the plane in Seoul, we are with you every step.")}
            </p>
          </div>
        </FadeInSection>

        <div className="max-w-4xl mx-auto flex flex-col items-center">
          
          {/* Step Indicators */}
          <div className="flex flex-col md:flex-row gap-4 mb-8 w-full justify-center items-center">
            {steps.map((step, idx) => {
              const isActive = activeStep === idx;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(idx)}
                  className={cn(
                    "flex-shrink-0 flex items-center justify-center rounded-full transition-all duration-300 font-bold text-lg",
                    isActive 
                      ? "w-14 h-14 bg-[#B8935F] text-white shadow-lg" 
                      : "w-11 h-11 bg-[#FAFAF9] text-[#B8935F]/40 border border-[#B8935F]/20 hover:border-[#B8935F]/60"
                  )}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Content Card */}
          <div className="w-full max-w-lg mt-4">
            <FadeInSection key={activeStep}>
              <div className="relative z-10 bg-white min-h-[400px] rounded-2xl border border-[#2C2825]/6 p-8 md:p-10 flex flex-col shadow-sm">
                
                <div className="flex justify-between items-start mb-8">
                  <div className="w-20 h-20 bg-[#F5F3F0] rounded-xl border border-[#B8935F]/20 flex items-center justify-center">
                    {(() => {
                      const ActiveIcon = steps[activeStep].icon;
                      return <ActiveIcon className="w-10 h-10 text-[#8A6420]" />;
                    })()}
                  </div>
                  <span className="bg-[#F5F3F0] text-[#8A6420] border border-[#B8935F]/20 rounded-full px-4 py-1.5 text-sm font-medium whitespace-nowrap">
                    {steps[activeStep].duration}
                  </span>
                </div>

                <h3 className="text-2xl font-bold text-[#2C2825] mb-4">
                  {steps[activeStep].title}
                </h3>
                <p className="text-lg text-[#6B6660] leading-[1.65] flex-1">
                  {steps[activeStep].desc}
                </p>
              </div>

              {/* Bottom Tip */}
              <div className="relative z-0 bg-[#F5F3F0] rounded-2xl -mt-8 pt-14 pb-6 px-8 flex items-start gap-3 border border-[#2C2825]/6 shadow-sm mx-4">
                <CheckCircle2 className="w-5 h-5 text-[#8A6420] flex-shrink-0 mt-0.5" />
                <p className="text-[15px] font-medium text-[#2C2825]">
                  {steps[activeStep].tip}
                </p>
              </div>
            </FadeInSection>
          </div>
          
        </div>
      </div>
    </section>
  );
}
