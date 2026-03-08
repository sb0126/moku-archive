export interface SiteConfig {
  gaMeasurementId: string;
  verification: {
    google: string | null;
    naver: string | null;
  };
}
