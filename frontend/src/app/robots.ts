import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: "/admin" },
      { userAgent: "Googlebot", allow: "/" },
      { userAgent: "Yeti", allow: "/" },
    ],
    sitemap: "https://moku.com/sitemap.xml",
    host: "https://moku.com",
  };
}
