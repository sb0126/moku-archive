import Script from "next/script";

async function getGaId() {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/config`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const data = await res.json();
      const val = data.find((c: any) => c.key === "ga_measurement_id")?.value;
      if (val) return val;
    }
  } catch (e) {
    // fallback
  }
  return "G-Q0M3KVC4JW";
}

export async function GoogleAnalytics() {
  const gaId = await getGaId();
  
  if (!gaId) return null;

  return (
    <>
      <Script strategy="afterInteractive" src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`} />
      <Script
        id="gtag-init"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${gaId}', {
              page_path: window.location.pathname,
            });
          `,
        }}
      />
    </>
  );
}
