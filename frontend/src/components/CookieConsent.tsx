"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

export function CookieConsent() {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
    const consent = localStorage.getItem("moku_cookie_consent");
    if (!consent) {
      const timer = setTimeout(() => setIsVisible(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("moku_cookie_consent", "true");
    setIsVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem("moku_cookie_consent", "false");
    setIsVisible(false);
  };

  if (!hasMounted) return null;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: "100%", opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: "100%", opacity: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="fixed bottom-6 left-0 right-0 z-[60] px-4 md:px-6 flex justify-center pointer-events-none"
        >
          <div className="bg-white rounded-2xl shadow-xl border border-[#2C2825]/8 p-4 sm:p-6 flex flex-col md:flex-row items-center justify-between gap-6 md:gap-12 w-full max-w-4xl pointer-events-auto">
            <p className="text-sm text-[#2C2825]/80 leading-relaxed flex-1">
              {t(
                "cookie.message",
                "We use cookies to enhance your browsing experience, serve personalized ads or content, and analyze our traffic. By clicking 'Accept All', you consent to our use of cookies."
              )}
            </p>
            <div className="flex gap-3 shrink-0">
              <Button 
                variant="outline" 
                onClick={handleDecline}
                className="bg-[#F5F3F0] hover:bg-[#E8E5E1] text-[#2C2825] border-0 rounded-lg px-6"
              >
                {t("cookie.decline", "Decline")}
              </Button>
              <Button 
                onClick={handleAccept} 
                className="bg-[#B8935F] hover:bg-[#A38568] text-white rounded-lg px-6 border-0"
              >
                {t("cookie.accept", "Accept All")}
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
