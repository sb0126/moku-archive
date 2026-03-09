"use client";

import { I18nextProvider } from "react-i18next";
import i18n from "@/i18n/config";
import { ReactNode, useEffect, useState } from "react";

export function I18nProvider({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Defer language switch until after hydration is complete
    const savedLang = localStorage.getItem("moku_language");
    if (savedLang && i18n.language !== savedLang) {
      i18n.changeLanguage(savedLang).then(() => setMounted(true));
    } else if (!savedLang) {
      const browserLang = navigator.language.split('-')[0];
      if (['ja', 'ko', 'en'].includes(browserLang) && i18n.language !== browserLang) {
        i18n.changeLanguage(browserLang).then(() => {
          localStorage.setItem("moku_language", browserLang);
          setMounted(true);
        });
      } else {
        setMounted(true);
      }
    } else {
      setMounted(true);
    }
  }, []);

  return (
    <I18nextProvider i18n={i18n}>
      <div suppressHydrationWarning={!mounted}>
        {children}
      </div>
    </I18nextProvider>
  );
}
