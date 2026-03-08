"use client";

import * as React from "react";
import { useTranslation } from "react-i18next";
import { Globe } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("moku_language", lng);
  };

  const getLangCode = (lng: string) => {
    switch (lng) {
      case "ja": return "JP";
      case "ko": return "KR";
      case "en": return "EN";
      default: return "EN";
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="rounded-full border-[#2C2825]/15 hover:bg-[#F5F3F0] bg-transparent text-[#2C2825] h-10 px-4 flex items-center gap-2">
          <Globe className="h-4 w-4 text-[#B8935F]" />
          <span className="font-medium">{getLangCode(i18n.language)}</span>
          <span className="sr-only">Change Language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-white rounded-xl shadow-lg border border-[#2C2825]/8 min-w-[120px]">
        <DropdownMenuItem onClick={() => changeLanguage("ja")} className="hover:bg-[#F5F3F0] cursor-pointer focus:bg-[#F5F3F0]">
          JP(日本語)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => changeLanguage("ko")} className="hover:bg-[#F5F3F0] cursor-pointer focus:bg-[#F5F3F0]">
          KR(한국어)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => changeLanguage("en")} className="hover:bg-[#F5F3F0] cursor-pointer focus:bg-[#F5F3F0]">
          EN(English)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
