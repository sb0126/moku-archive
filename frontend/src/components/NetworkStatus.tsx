"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function NetworkStatus() {
  const [isOnline, setIsOnline] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className={cn(
      "fixed top-0 left-0 right-0 z-[100] bg-destructive text-destructive-foreground text-sm font-medium py-2 px-4 flex items-center justify-center gap-2 transition-all duration-300 transform translate-y-0"
    )}>
      <WifiOff className="h-4 w-4" />
      <span>{t("network.offline", "You are currently offline. Please check your internet connection.")}</span>
    </div>
  );
}
