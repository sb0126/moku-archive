export interface CommentResponse {
  id: string;
  postId: string;
  parentId?: string | null;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface CommentCreateRequest {
  author: string;
  content: string;
  password: string;
  parentId?: string | null;
}

export interface CommentUpdateRequest {
  content: string;
  password: string;
}

export interface CommentListResponse {
  success: boolean;
  comments: CommentResponse[];
  count: number;
}
