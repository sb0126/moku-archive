"use client";

import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { Wrench } from "lucide-react";

export default function MaintenancePage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[#FAFAF9] flex items-center justify-center p-6 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-xl"
      >
        <div className="w-16 h-16 bg-[#F5F3F0] rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-[#2C2825]/6">
          <Wrench className="w-8 h-8 text-[#B8935F]" />
        </div>
        
        <h1 className="text-3xl md:text-4xl font-bold text-[#2C2825] mb-4">
          Under Maintenance
        </h1>
        
        <p className="text-[#6B6660] text-lg mb-8 leading-relaxed">
          We are currently performing scheduled maintenance to improve our services.
          Please check back later. We apologize for any inconvenience.
        </p>

        <div className="inline-flex flex-col items-center">
          <div className="w-12 h-1 bg-[#B8935F]/20 rounded-full mb-4"></div>
          <p className="text-sm text-[#2C2825]/60 font-medium">MOKU.com</p>
        </div>
      </motion.div>
    </div>
  );
}
