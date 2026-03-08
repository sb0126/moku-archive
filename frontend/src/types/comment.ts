export interface CommentResponse {
  id: string;
  postId: string;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface CommentCreateRequest {
  author: string;
  content: string;
  password: string;
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
