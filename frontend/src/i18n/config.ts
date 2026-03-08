"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import ja from "./locales/ja";
import ko from "./locales/ko";
import en from "./locales/en";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ja: { translation: ja },
      ko: { translation: ko },
      en: { translation: en },
    },
    fallbackLng: "ja",
    supportedLngs: ["ja", "ko", "en"],
    defaultNS: "translation",
    keySeparator: false, // Ensure that dots in keys are treated literally
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: "moku_language",
      caches: ["localStorage"],
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
