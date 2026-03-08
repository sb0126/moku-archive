"use client";

import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import { useTranslation } from "react-i18next";
import { usePathname } from "next/navigation";
import * as React from "react";
import Script from "next/script";

export function Breadcrumb() {
  const { t } = useTranslation();
  const pathname = usePathname();

  const generateBreadcrumbs = React.useCallback(() => {
    const asPathWithoutQuery = pathname.split("?")[0];
    const asPathNestedRoutes = asPathWithoutQuery.split("/").filter((v) => v.length > 0);

    const crumblist = asPathNestedRoutes.map((subpath, idx) => {
      const href = "/" + asPathNestedRoutes.slice(0, idx + 1).join("/");
      return { href, label: subpath.charAt(0).toUpperCase() + subpath.slice(1) };
    });

    return [{ href: "/", label: t("breadcrumb.home", "Home") }, ...crumblist];
  }, [pathname, t]);

  const breadcrumbs = generateBreadcrumbs();

  if (breadcrumbs.length <= 1) return null;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": breadcrumbs.map((crumb, idx) => ({
      "@type": "ListItem",
      "position": idx + 1,
      "name": crumb.label === t("breadcrumb.home", "Home") ? "Home" : crumb.label,
      "item": `https://moku.com${crumb.href}`,
    })),
  };

  return (
    <>
      <Script
        id={`breadcrumb-jsonld-${pathname}`}
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <nav aria-label="Breadcrumb" className="my-6">
        <ol className="flex items-center space-x-2 text-sm text-muted-foreground">
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            return (
              <li key={crumb.href} className="flex items-center">
                {idx === 0 ? (
                  <Link href={crumb.href} className="text-[#2C2825]/60 hover:text-[#8A6420] transition-colors flex items-center">
                    <Home className="h-4 w-4" />
                    <span className="sr-only">{crumb.label}</span>
                  </Link>
                ) : (
                  <Link
                    href={crumb.href}
                    className={`transition-colors ${isLast ? "text-[#2C2825] font-medium pointer-events-none" : "text-[#2C2825]/60 hover:text-[#8A6420]"}`}
                  >
                    {t(`breadcrumb.${crumb.label.toLowerCase()}`, crumb.label)}
                  </Link>
                )}
                {!isLast && <ChevronRight className="h-4 w-4 mx-2 text-[#2C2825]/30" />}
              </li>
            );
          })}
        </ol>
      </nav>
    </>
  );
}
