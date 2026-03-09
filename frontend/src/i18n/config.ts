"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ja from "./locales/ja";
import ko from "./locales/ko";
import en from "./locales/en";

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ja: { translation: ja },
      ko: { translation: ko },
      en: { translation: en },
    },
    lng: "ja", // Force Japanese for SSR and initial hydration
    fallbackLng: "ja",
    supportedLngs: ["ja", "ko", "en"],
    defaultNS: "translation",
    keySeparator: false, // Ensure that dots in keys are treated literally
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
