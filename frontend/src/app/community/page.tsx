"use client";

import React from "react";
import CommunityPage from "@/components/CommunityPage";
import { Breadcrumb } from "@/components/Breadcrumb";

export default function CommunityRoute() {
  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-16 md:pt-20">
      <div className="container mx-auto px-4 max-w-5xl pb-16 mt-4">
        <Breadcrumb />
        <CommunityPage />
      </div>
    </div>
  );
}
