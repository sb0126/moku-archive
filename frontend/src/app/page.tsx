import { Suspense } from "react";
import Script from "next/script";
import { Metadata } from "next";
import { Hero } from "@/components/Hero";
import { VisaProcess } from "@/components/VisaProcess";
import { ArchiveListPreview } from "@/components/ArchiveListPreview";
import { FAQ } from "@/components/FAQ";
import { InquiryForm } from "@/components/InquiryForm";
import { ArchiveSkeleton } from "@/components/SkeletonLoaders";
import { ArticleListResponse } from "@/types/article";
import { SideNav } from "@/components/SideNav";
import { ScrollToTop } from "@/components/ScrollToTop";

export const metadata: Metadata = {
  title: "Moku | Korea H-1 Working Holiday Agency",
  description: "Expert consultation, seamless document preparation, and local settlement support tailored specifically for your peace of mind in South Korea.",
};

// Next.js ISR configuration
export const revalidate = 3600; // 1 hour

async function getPreviewArticles() {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/articles?limit=4`, {
      next: { revalidate: 300 }, // Archive previews can revalidate more often (5min)
    });
    if (!res.ok) return { articles: [] };
    const data: ArticleListResponse = await res.json();
    return data;
  } catch (error) {
    console.error("Failed to fetch archive previews:", error);
    return { articles: [] };
  }
}

export default async function HomePage() {
  const { articles } = await getPreviewArticles();

  const generateJsonLd = () => {
    return {
      __html: JSON.stringify([
        {
          "@context": "https://schema.org",
          "@type": "Organization",
          "name": "Moku",
          "url": "https://moku.com",
          "logo": "https://moku.com/logo.png",
          "description": "Professional agency for Korea H-1 Working Holiday visa.",
          "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "availableLanguage": ["Japanese", "Korean", "English"]
          }
        },
        {
          "@context": "https://schema.org",
          "@type": "ProfessionalService",
          "name": "Moku Visa Consultation",
          "image": "https://moku.com/logo.png",
          "address": {
            "@type": "PostalAddress",
            "addressLocality": "Seoul",
            "addressCountry": "KR"
          },
          "url": "https://moku.com",
          "telephone": "+82-10-0000-0000"
        },
        {
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "Am I eligible for the H-1 visa?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "You must be a citizen of a country that has a Working Holiday agreement with South Korea, typically between the ages of 18 and 30, and without dependents."
              }
            },
            {
              "@type": "Question",
              "name": "How long does the application process take?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Typically, document preparation takes 1-2 weeks, and the embassy processing takes another 1-2 weeks. The entire process takes about a month."
              }
            }
          ]
        }
      ])
    };
  };

  return (
    <>
      <Script id="json-ld" type="application/ld+json" dangerouslySetInnerHTML={generateJsonLd()} />
      
      <SideNav />

      <Hero />
      <VisaProcess />
      
      <Suspense fallback={<section className="py-24 container mx-auto px-6"><ArchiveSkeleton /></section>}>
        <ArchiveListPreview articles={articles} />
      </Suspense>
      
      <FAQ />
      <InquiryForm />

      <ScrollToTop />
    </>
  );
}
