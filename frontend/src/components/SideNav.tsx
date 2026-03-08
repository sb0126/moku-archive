"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

const SECTIONS = [
  { id: "visa-process", label: "Process" },
  { id: "archive", label: "Archive" },
  { id: "faq", label: "FAQ" },
  { id: "inquiry", label: "Contact" },
] as const;

export function SideNav() {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<string>("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-40% 0px -40% 0px" }
    );

    SECTIONS.forEach((section) => {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[45] hidden lg:flex items-center gap-6 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-full shadow-lg border border-[#2C2825]/5">
      {SECTIONS.map((section) => {
        const isActive = activeSection === section.id;
        return (
          <button
            key={section.id}
            onClick={() => scrollToSection(section.id)}
            className="group relative flex items-center justify-center p-2 cursor-pointer transition-all duration-300 focus:outline-none"
            aria-label={`Scroll to ${section.label}`}
          >
            <span
              className={cn(
                "absolute -top-10 px-3 py-1.5 rounded-lg bg-[#2C2825] text-white text-xs font-medium opacity-0 transition-all duration-200 whitespace-nowrap group-hover:opacity-100 group-hover:-translate-y-1 pointer-events-none shadow-md",
              )}
            >
              {t(`sidenav.${section.id.replace("-", "")}`, section.label)}
              <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#2C2825]" />
            </span>
            <div
              className={cn(
                "w-2.5 h-2.5 rounded-full transition-all duration-300",
                isActive
                  ? "bg-[#B8935F] scale-[1.3] shadow-sm shadow-[#B8935F]/20"
                  : "bg-[#2C2825]/20 group-hover:bg-[#B8935F] scale-100"
              )}
            />
          </button>
        );
      })}
    </div>
  );
}
