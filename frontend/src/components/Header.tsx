"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import { Menu, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Header() {
  const { t } = useTranslation();
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = React.useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  React.useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = "hidden";
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === "Escape") setIsMobileMenuOpen(false);
      };

      const handleTab = (e: KeyboardEvent) => {
        if (e.key === "Tab") {
          const focusableElements = document.querySelectorAll(
            '#mobile-nav-overlay a[href], #mobile-nav-overlay button, #mobile-nav-overlay textarea, #mobile-nav-overlay input[type="text"], #mobile-nav-overlay input[type="radio"], #mobile-nav-overlay input[type="checkbox"], #mobile-nav-overlay select'
          );
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement?.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement?.focus();
              e.preventDefault();
            }
          }
        }
      };

      document.addEventListener("keydown", handleEscape);
      document.addEventListener("keydown", handleTab);
      return () => {
        document.body.style.overflow = "";
        document.removeEventListener("keydown", handleEscape);
        document.removeEventListener("keydown", handleTab);
      };
    } else {
      document.body.style.overflow = "";
    }
  }, [isMobileMenuOpen]);

  const navLinks = [
    { href: "/archive", label: t("header.archive", "アーカイブ") },
    { href: "/community", label: t("header.community", "コミュニティ") },
    { href: "/partners", label: t("header.partners", "提携パートナー") },
    { href: "/guideline", label: t("header.guideline", "ガイドライン") },
  ];

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled ? "bg-white/90 backdrop-blur-md shadow-sm border-b border-[#2C2825]/5" : "bg-transparent",
        "h-16 lg:h-20 flex items-center"
      )}
    >
      <div className={cn("container mx-auto px-6 w-full flex items-center justify-between transition-transform duration-300", !isScrolled && "lg:-translate-y-1.5")}>
        {/* Left: Logo */}
        <div className="flex flex-1 items-center justify-start">
          <Link href="/" className="text-xl lg:text-2xl font-bold text-[#9E7030] tracking-tight">
            MOKU
          </Link>
        </div>

        {/* Center: Desktop Nav Links */}
        <nav className="hidden lg:flex items-center justify-center gap-5 xl:gap-8">
          {navLinks.map((link) => {
            const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
            return (
              <Link 
                key={link.href} 
                href={link.href} 
                className={cn(
                  "text-sm font-medium transition-colors hover:text-[#8A6420]",
                  isActive ? "text-[#8A6420]" : "text-[#2C2825]/70"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: Desktop Actions */}
        <div className="hidden lg:flex flex-1 items-center justify-end gap-3 xl:gap-4">
          <LanguageSwitcher />
          <Button asChild className="bg-[#B8935F] hover:bg-[#A38568] text-white rounded-full px-6 border-0 shrink-0">
            <Link href="/#inquiry">{t("header.consultation", "無料相談")}</Link>
          </Button>
        </div>

        {/* Mobile Toggle */}
        <div className="lg:hidden flex flex-1 items-center justify-end gap-4">
          <LanguageSwitcher />
          <Button variant="ghost" size="icon" className="text-[#2C2825]" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
            {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
        </div>
      </div>

      {/* Mobile Nav Overlay */}
      {isMobileMenuOpen && (
        <div id="mobile-nav-overlay" className="lg:hidden fixed inset-0 top-[64px] z-[40] bg-white/95 backdrop-blur-md flex flex-col p-6 gap-4 animate-in fade-in slide-in-from-top-4 duration-300">
          {navLinks.map((link) => {
            const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "py-3 px-4 text-lg font-medium rounded-xl transition-colors hover:bg-black/5 hover:text-[#8A6420]",
                  isActive ? "bg-black/5 text-[#8A6420]" : "text-[#2C2825]/80"
                )}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="mt-auto pb-8">
            <Button asChild className="w-full bg-[#B8935F] hover:bg-[#A38568] text-white rounded-full py-6 text-lg border-0">
              <Link href="/#inquiry" onClick={() => setIsMobileMenuOpen(false)}>
                {t("header.consultation", "無料相談")}
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
