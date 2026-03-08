export interface PostResponse {
  id: string;
  numericId: number;
  title: string;
  author: string;
  content: string;
  views: number;
  comments: number;
  pinned: boolean;
  pinnedAt: string | null;
  experience: "experienced" | "inexperienced" | null;
  category: "question" | "info" | "chat" | null;
  createdAt: string;
  updatedAt: string;
}

export interface PostListResponse {
  success: boolean;
  posts: PostResponse[];
  count: number;
  total: number;
  totalPages: number;
  currentPage: number;
  limit: number;
}

export interface PostCreateRequest {
  author: string;
  title: string;
  content: string;
  password: string;
  experience?: "experienced" | "inexperienced";
  category?: "question" | "info" | "chat";
}

export interface PostUpdateRequest {
  title?: string;
  content?: string;
  password: string;
}

export interface PostDeleteRequest {
  password?: string;
  isAdmin?: boolean;
}

export interface LikeToggleRequest {
  visitorId: string;
}

export interface LikeResponse {
  success: boolean;
  liked: boolean;
  likes: number;
}

export interface LikeStatusResponse {
  success: boolean;
  likes: number;
  liked: boolean;
}

export interface BulkLikesResponse {
  success: boolean;
  likes: Record<string, number>;
}

export type PostSearchType = "title" | "author" | "content";
export type PostSortField = "newest" | "oldest" | "likes" | "views" | "comments";
export type PostCategoryFilter = "question" | "info" | "chat";
