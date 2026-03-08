export interface InquiryCreateRequest {
  name: string;
  email: string;
  phone: string;
  age: number;
  preferredDate: string;
  plan: string;
  message?: string;
}

export interface InquiryResponse {
  id: string;
  name: string;
  email: string;
  phone: string;
  age: number;
  preferredDate: string | null;
  plan: string | null;
  message: string;
  status: "pending" | "contacted" | "completed";
  adminNote: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface InquiryListResponse {
  success: boolean;
  inquiries: InquiryResponse[];
  count: number;
}
