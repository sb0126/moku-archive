export interface AdminLoginResponse {
  success: boolean;
  authenticated: boolean;
  token: string;
}

export interface AdminStats {
  totalInquiries: number;
  pendingInquiries: number;
  contactedInquiries: number;
  completedInquiries: number;
  totalPosts: number;
  totalViews: number;
  totalComments: number;
}

export interface AdminStatsResponse {
  success: boolean;
  stats: AdminStats;
}
