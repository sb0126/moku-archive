"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Pin, MessageSquare, Eye, ThumbsUp, Clock, User, Search, Edit2, Trash2, X, ChevronDown, ChevronUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ja, ko } from "date-fns/locale";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

import {
  PostResponse, PostCreateRequest, PostUpdateRequest,
  LikeToggleRequest, BulkLikesResponse, LikeStatusResponse, PostListResponse
} from "@/types/post";
import {
  CommentResponse, CommentCreateRequest, CommentUpdateRequest, CommentListResponse
} from "@/types/comment";

// -- Consts --
const CATEGORIES = ["all", "question", "info", "chat"];
const SEARCH_TYPES = ["title", "author", "content"];
const SORTS = ["newest", "oldest", "likes", "views", "comments"];

// -- Main Component --
export default function CommunityPage() {
  const { t, i18n } = useTranslation();
  const dateLocale = i18n.language === "ko" ? ko : ja;

  // -- State: Layout --
  const [visitorId, setVisitorId] = useState("");
  
  // -- State: List & Filters --
  const [posts, setPosts] = useState<PostResponse[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalPosts, setTotalPosts] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [searchType, setSearchType] = useState("title");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("newest");
  const [likesCount, setLikesCount] = useState<Record<string, number>>({});

  // -- State: Detail View --
  const [openPostId, setOpenPostId] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailComments, setDetailComments] = useState<CommentResponse[]>([]);
  const [detailLiked, setDetailLiked] = useState(false);
  const [commentInput, setCommentInput] = useState("");
  const [commentAuthor, setCommentAuthor] = useState("");
  const [commentPassword, setCommentPassword] = useState("");

  // -- State: Dialogs --
  const [isPostDialogOpen, setIsPostDialogOpen] = useState(false);
  const [postForm, setPostForm] = useState<Partial<PostCreateRequest>>({ category: "chat", experience: undefined });
  
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false);
  const [passwordTarget, setPasswordTarget] = useState<{ type: "post"|"comment", action: "edit"|"delete", id: string, content?: string } | null>(null);
  const [passwordInput, setPasswordInput] = useState("");

  // Initialize Visitor ID
  useEffect(() => {
    let id = localStorage.getItem("moku_visitor_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("moku_visitor_id", id);
    }
    setVisitorId(id);
  }, []);

  // Fetch Posts
  const fetchPosts = useCallback(async () => {
    setLoadingPosts(true);
    try {
      const query = new URLSearchParams({
        page: page.toString(),
        limit: "10",
        sort,
        searchType,
      });
      if (search) query.append("search", search);
      if (category !== "all") query.append("category", category);

      const res = await api.get<PostListResponse>(`/api/posts?${query.toString()}`);
      if (res.success) {
        setPosts(res.posts);
        setTotalPages(res.totalPages);
        setTotalPosts(res.total);
        
        // Fetch bulk likes when posts arrive
        if (res.posts.length > 0) {
          const ids = res.posts.map(p => p.id);
          const likesRes = await api.post<BulkLikesResponse>("/api/posts/likes/bulk", { postIds: ids });
          if (likesRes.success) {
            setLikesCount(prev => ({ ...prev, ...likesRes.likes }));
          }
        }
      }
    } catch (err: any) {
      toast.error(t("error.fetchPosts", "Failed to fetch posts") + ": " + err.message);
    } finally {
      setLoadingPosts(false);
    }
  }, [page, sort, search, searchType, category, t]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  // Fetch Detail (Comments & Likes Status & Increment View) — parallelized with Promise.all
  const openPostDetail = async (postId: string) => {
    if (openPostId === postId) {
        setOpenPostId(null);
        return;
    }
    
    setOpenPostId(postId);
    setLoadingDetail(true);
    try {
      // Run all three independent API calls in parallel (async-parallel rule)
      const [, commentRes, likeRes] = await Promise.all([
        // 1. Increment view (fire-and-forget result, but still await for error handling)
        api.post(`/api/posts/${postId}/view`),
        // 2. Fetch comments
        api.get<CommentListResponse>(`/api/posts/${postId}/comments`),
        // 3. Fetch like status for this visitor
        visitorId
          ? api.get<LikeStatusResponse>(`/api/posts/${postId}/likes?visitorId=${visitorId}`)
          : Promise.resolve(null),
      ]);

      // Update view count optimistically
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, views: p.views + 1 } : p));

      // Apply comment results
      if (commentRes.success) {
        setDetailComments(commentRes.comments);
      }

      // Apply like status results
      if (likeRes && likeRes.success) {
        setDetailLiked(likeRes.liked);
        setLikesCount(prev => ({ ...prev, [postId]: likeRes.likes }));
      }
    } catch (err: any) {
        toast.error(err.message);
    } finally {
        setLoadingDetail(false);
    }
  };

  // Helper formatting — memoized to avoid re-creation on every render (rerender-defer-reads rule)
  const relativeTime = useCallback((dateStr: string) => {
    try {
        return formatDistanceToNow(new Date(dateStr), { addSuffix: true, locale: dateLocale });
    } catch {
        return dateStr;
    }
  }, [dateLocale]);

  // --- Handlers ---
  const handleLikeToggle = async (postId: string) => {
    try {
        const res = await api.post<LikeStatusResponse>(`/api/posts/${postId}/like`, { visitorId });
        if (res.success) {
            setDetailLiked(res.liked);
            setLikesCount(prev => ({ ...prev, [postId]: res.likes }));
        }
    } catch (error: any) {
        toast.error(error.message || "Failed to toggle like");
    }
  };

  const handleCreatePost = async () => {
    if (!postForm.title || !postForm.content || !postForm.author || !postForm.password) {
        toast.error(t("validation.emptyFields", "Please fill in all required fields"));
        return;
    }
    try {
        await api.post("/api/posts", postForm);
        toast.success(t("success.postCreated", "Post created successfully"));
        setIsPostDialogOpen(false);
        setPostForm({ category: "chat", experience: undefined });
        setPage(1);
        fetchPosts();
    } catch (error: any) {
        toast.error(error.message);
    }
  };

  const handleCreateComment = async (postId: string) => {
    if (!commentInput || !commentAuthor || !commentPassword) {
        toast.error(t("validation.emptyFields", "Please fill in all required fields"));
        return;
    }
    try {
        const res = await api.post<any>(`/api/posts/${postId}/comments`, {
            content: commentInput,
            author: commentAuthor,
            password: commentPassword
        });
        if (res.success) {
            toast.success(t("success.commentCreated", "Comment added"));
            setCommentInput("");
            setCommentPassword("");
            setDetailComments([...detailComments, res.comment]);
            setPosts(prev => prev.map(p => p.id === postId ? { ...p, comments: res.commentCount } : p));
        }
    } catch (error: any) {
        toast.error(error.message);
    }
  };

  const executePasswordAction = async () => {
    if (!passwordTarget || !passwordInput) return;
    try {
        const { type, action, id, content } = passwordTarget;
        
        let verifyPath = type === "post" ? `/api/posts/${id}/verify-password` : `/api/comments/${id}/verify-password`;
        const verifyRes = await api.post<any>(verifyPath, { password: passwordInput });
        
        if (!verifyRes.success || !verifyRes.verified) {
            throw new Error(t("error.invalidPassword", "Invalid password"));
        }

        if (action === "delete") {
            const delPath = type === "post" ? `/api/posts/${id}` : `/api/comments/${id}`;
            await api.del(delPath, { password: passwordInput });
            toast.success(t("success.deleted", "Deleted successfully"));
            if (type === "post") {
                setPosts(prev => prev.filter(p => p.id !== id));
                setOpenPostId(null);
            } else {
                setDetailComments(prev => prev.filter(c => c.id !== id));
                setPosts(prev => prev.map(p => p.id === openPostId ? { ...p, comments: Math.max(0, p.comments - 1) } : p));
            }
        } else if (action === "edit") {
            const editPath = type === "post" ? `/api/posts/${id}` : `/api/comments/${id}`;
            const reqBody = type === "post" ? { content, password: passwordInput } : { content, password: passwordInput };
            const res = await api.put<any>(editPath, reqBody);
            toast.success(t("success.updated", "Updated successfully"));
            if (type === "post") {
                setPosts(prev => prev.map(p => p.id === id ? { ...p, content: content! } : p));
            } else {
                setDetailComments(prev => prev.map(c => c.id === id ? { ...c, content: content! } : c));
            }
        }
        setIsPasswordDialogOpen(false);
        setPasswordInput("");
        setPasswordTarget(null);
    } catch (e: any) {
        toast.error(e.message);
    }
  };

  const getCategoryColor = (cat: string | null) => {
    switch (cat) {
        case "question": return "bg-violet-50 text-violet-700 border-violet-200/60";
        case "info": return "bg-amber-50 text-amber-700 border-amber-200/60";
        case "chat": return "bg-rose-50 text-rose-600 border-rose-200/60";
        default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getExperienceBadge = (exp: "experienced" | "inexperienced" | null) => {
    if (!exp) return null;
    return exp === "experienced" ? (
        <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200/60 shrink-0">
            {t(`badge.experienced`, "Experienced")}
        </Badge>
    ) : (
        <Badge variant="outline" className="text-xs bg-sky-50 text-sky-700 border-sky-200/60 shrink-0">
            {t(`badge.inexperienced`, "First-timer")}
        </Badge>
    );
  };

  return (
    <div className="w-full space-y-6 pb-12">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between mb-8">
          <div>
              <h1 className="text-3xl font-bold tracking-tight">{t("title", "Community")}</h1>
              <p className="text-[#6B6660] mt-1">{t("subtitle", "Q&A, Information sharing, and open chat.")}</p>
          </div>
      </div>

      <Card className="bg-card w-full shadow-sm">
        <CardContent className="p-4 md:p-6 space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1 flex gap-2">
                  <Select value={searchType} onValueChange={setSearchType}>
                      <SelectTrigger className="w-[110px] shrink-0">
                          <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                          {SEARCH_TYPES.map(st => (
                              <SelectItem key={st} value={st}>{t(`searchType.${st}`, st)}</SelectItem>
                          ))}
                      </SelectContent>
                  </Select>
                  <div className="relative flex-1">
                      <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input 
                          placeholder={t("placeholder.search", "Search...")} 
                          className="pl-9" 
                          value={searchInput}
                          onChange={(e) => setSearchInput(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && setSearch(searchInput)}
                      />
                  </div>
              </div>
              <div className="flex gap-2 w-full md:w-auto">
                <Select value={category} onValueChange={(val) => { setCategory(val); setPage(1); }}>
                    <SelectTrigger className="w-full md:w-[130px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {CATEGORIES.map(c => (
                            <SelectItem key={c} value={c}>{t(`category.${c}`, c)}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <Select value={sort} onValueChange={(val) => { setSort(val); setPage(1); }}>
                    <SelectTrigger className="w-full md:w-[130px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {SORTS.map(s => (
                            <SelectItem key={s} value={s}>{t(`sort.${s}`, s)}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
              </div>
          </div>

          {/* List Area */}
          <div className="bg-white rounded-2xl border border-[#2C2825]/6 divide-y divide-[#2C2825]/6 mt-4">
              {loadingPosts ? (
                  Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-24 w-full rounded-none" />
                  ))
              ) : posts.length === 0 ? (
                  <div className="text-center py-12 text-[#6B6660]">
                      {t("empty", "No posts found.")}
                  </div>
              ) : (
                  posts.map((post) => {
                      const isOpen = openPostId === post.id;
                      const postLikes = likesCount[post.id] || 0;
                      
                      return (
                          <div key={post.id} className={`overflow-hidden transition-all duration-200 ease-in-out hover:bg-zinc-50/50 ${post.pinned ? "bg-amber-50 border-l-2 border-amber-400" : ""}`}>
                              {/* Post Row (Clickable) */}
                              <div 
                                  className="p-4 cursor-pointer flex flex-col gap-3"
                                  onClick={() => openPostDetail(post.id)}
                              >
                                  <div className="flex items-start justify-between gap-4">
                                      <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                                              {post.pinned && <Badge variant="secondary" className="bg-[#B8935F]/10 text-[#B8935F] hover:bg-[#B8935F]/20"><Pin className="w-3 h-3 mr-1" />{t("badge.pinned", "Best")}</Badge>}
                                              {post.category && <Badge variant="outline" className={`text-xs ${getCategoryColor(post.category)}`}>{t(`category.${post.category}`, post.category)}</Badge>}
                                              {getExperienceBadge(post.experience)}
                                          </div>
                                          <h3 className={`text-base font-semibold truncate break-words mb-1 tracking-tight ${isOpen ? "text-[#8A6420]" : "text-[#2C2825]"}`}>
                                              {post.title}
                                          </h3>
                                          <div className="flex items-center text-xs text-[#6B6660] gap-3">
                                              <span className="flex items-center gap-1 font-medium"><User className="w-3 h-3" />{post.author}</span>
                                              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{relativeTime(post.createdAt)}</span>
                                              <div className="flex items-center gap-3 ml-auto text-[#6B6660] font-medium">
                                                  <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5" />{post.views}</span>
                                                  <span className="flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5" />{postLikes}</span>
                                                  <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" />{post.comments}</span>
                                              </div>
                                          </div>
                                      </div>
                                      <div className="shrink-0 mt-1">
                                          {isOpen ? <ChevronUp className="w-5 h-5 text-muted-foreground" /> : <ChevronDown className="w-5 h-5 text-muted-foreground" />}
                                      </div>
                                  </div>
                              </div>

                              {/* Expanded Inline Detail */}
                              {isOpen && (
                                  <div className="p-4 pt-0 border-t border-border bg-muted/20">
                                      {loadingDetail ? (
                                          <div className="py-8 space-y-4">
                                              <Skeleton className="h-4 w-full" />
                                              <Skeleton className="h-4 w-5/6" />
                                              <Skeleton className="h-4 w-4/6" />
                                          </div>
                                      ) : (
                                          <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                                              <div className="bg-white rounded-2xl border border-[#2C2825]/6 p-8 md:p-10 text-sm whitespace-pre-wrap leading-relaxed shadow-sm">
                                                  {post.content}
                                              </div>
                                              
                                              {/* Actions container */}
                                              <div className="flex items-center justify-between mt-4">
                                                  <Button 
                                                      variant={detailLiked ? "default" : "outline"} 
                                                      size="sm" 
                                                      className="rounded-full shadow-sm hover:scale-105 transition-transform"
                                                      onClick={() => handleLikeToggle(post.id)}
                                                  >
                                                      <ThumbsUp className={`w-4 h-4 mr-2 ${detailLiked ? "fill-current" : ""}`} />
                                                      {t("action.like", "Like")} {postLikes > 0 && `(${postLikes})`}
                                                  </Button>
                                                  
                                                  <div className="flex items-center gap-2">
                                                      <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-destructive transition-colors shrink-0"
                                                          onClick={() => setPasswordTarget({ type: "post", action: "delete", id: post.id })}>
                                                          <Trash2 className="w-4 h-4 mr-1" />
                                                          <span className="hidden sm:inline">{t("action.delete", "Delete")}</span>
                                                      </Button>
                                                  </div>
                                              </div>

                                              {/* Comments Section */}
                                              <div className="mt-8 space-y-4">
                                                  <h4 className="font-semibold text-sm flex items-center gap-2">
                                                      {t("label.comments", "Comments")} 
                                                      <Badge variant="secondary" className="bg-primary/10 text-primary px-1.5">{post.comments}</Badge>
                                                  </h4>
                                                  
                                                  <div className="bg-background rounded-xl p-4 border border-border/50 space-y-4 shadow-sm">
                                                      {/* Comment List */}
                                                      <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                                          {detailComments.map((comment, idx) => (
                                                              <div key={comment.id} className={`group text-sm border border-[#2C2825]/6 rounded-lg p-4 bg-white ${idx !== 0 ? "mt-4" : ""}`}>
                                                                  <div className="flex justify-between items-start mb-1.5">
                                                                      <div className="font-semibold text-[#2C2825] flex items-center gap-2">
                                                                          {comment.author}
                                                                          <span className="text-xs font-normal text-[#6B6660]">{relativeTime(comment.createdAt)}</span>
                                                                      </div>
                                                                      <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10 hover:text-destructive"
                                                                          onClick={() => setPasswordTarget({ type: "comment", action: "delete", id: comment.id })}>
                                                                          <Trash2 className="w-3 h-3" />
                                                                      </Button>
                                                                  </div>
                                                                  <p className="text-muted-foreground whitespace-pre-wrap">{comment.content}</p>
                                                              </div>
                                                          ))}
                                                          {detailComments.length === 0 && (
                                                              <div className="text-center text-muted-foreground italic py-2 text-sm">{t("empty.comments", "No comments yet. Be the first!")}</div>
                                                          )}
                                                      </div>

                                                      {/* Comment Input */}
                                                      <div className="pt-4 border-t border-border mt-4">
                                                          <div className="flex flex-col sm:flex-row gap-3">
                                                              <Input 
                                                                  placeholder={t("placeholder.author", "Name")} 
                                                                  value={commentAuthor} onChange={e => setCommentAuthor(e.target.value)}
                                                                  className="sm:w-1/4 h-9"
                                                              />
                                                              <Input 
                                                                  type="password"
                                                                  placeholder={t("placeholder.password", "Password")} 
                                                                  value={commentPassword} onChange={e => setCommentPassword(e.target.value)}
                                                                  className="sm:w-1/4 h-9"
                                                              />
                                                          </div>
                                                          <div className="flex gap-2 mt-3 text-sm">
                                                              <Textarea 
                                                                  placeholder={t("placeholder.comment", "Write a comment...")} 
                                                                  value={commentInput} onChange={e => setCommentInput(e.target.value)}
                                                                  className="min-h-[40px] h-[40px] resize-none py-2 shrink"
                                                              />
                                                              <Button onClick={() => handleCreateComment(post.id)} className="shrink-0 h-[40px] font-medium" disabled={!commentInput || !commentAuthor || !commentPassword}>
                                                                  {t("action.submit", "Submit")}
                                                              </Button>
                                                          </div>
                                                      </div>
                                                  </div>
                                              </div>
                                          </div>
                                      )}
                                  </div>
                              )}
                          </div>
                      );
                  })
              )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2 mt-8">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-full shadow-sm">
                    {t("pagination.prev", "Prev")}
                  </Button>
                  <span className="text-sm font-medium mx-2 bg-[#B8935F] text-white w-8 h-8 flex items-center justify-center rounded-full shadow-sm">{page}</span>
                  <span className="text-sm text-[#6B6660]">/ {totalPages}</span>
                  <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="rounded-full shadow-sm">
                    {t("pagination.next", "Next")}
                  </Button>
              </div>
          )}
        </CardContent>
      </Card>

      {/* Write Post FAB */}
      <button 
        onClick={() => setIsPostDialogOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-[#B8935F] text-white rounded-full shadow-lg flex items-center justify-center hover:bg-[#8A6420] transition-colors z-50"
      >
        <Edit2 className="w-6 h-6" />
      </button>

      {/* --- Dialogs --- */}
      {/* Create Post */}
      <Dialog open={isPostDialogOpen} onOpenChange={setIsPostDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                  <DialogTitle>{t("dialog.newPost", "Write New Post")}</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                      <Select value={postForm.category} onValueChange={v => setPostForm({ ...postForm, category: v as any })}>
                          <SelectTrigger><SelectValue placeholder="Category" /></SelectTrigger>
                          <SelectContent>
                              <SelectItem value="chat">{t("category.chat", "Chat")}</SelectItem>
                              <SelectItem value="question">{t("category.question", "Question")}</SelectItem>
                              <SelectItem value="info">{t("category.info", "Info")}</SelectItem>
                          </SelectContent>
                      </Select>
                      <Select value={postForm.experience || "none"} onValueChange={v => setPostForm({ ...postForm, experience: v === "none" ? undefined : v as any })}>
                          <SelectTrigger><SelectValue placeholder="Experience (Optional)" /></SelectTrigger>
                          <SelectContent>
                              <SelectItem value="none">{t("experience.none", "None")}</SelectItem>
                              <SelectItem value="experienced">{t("experience.experienced", "Experienced")}</SelectItem>
                              <SelectItem value="inexperienced">{t("experience.inexperienced", "First-timer")}</SelectItem>
                          </SelectContent>
                      </Select>
                  </div>
                  <Input placeholder={t("placeholder.title", "Title")} value={postForm.title || ""} onChange={e => setPostForm({ ...postForm, title: e.target.value })} />
                  <div className="grid grid-cols-2 gap-4">
                      <Input placeholder={t("placeholder.author", "Nickname")} value={postForm.author || ""} onChange={e => setPostForm({ ...postForm, author: e.target.value })} />
                      <Input type="password" placeholder={t("placeholder.password", "Password")} value={postForm.password || ""} onChange={e => setPostForm({ ...postForm, password: e.target.value })} />
                  </div>
                  <Textarea placeholder={t("placeholder.content", "Content...")} className="min-h-[150px]" value={postForm.content || ""} onChange={e => setPostForm({ ...postForm, content: e.target.value })} />
              </div>
              <DialogFooter>
                  <Button variant="outline" onClick={() => setIsPostDialogOpen(false)}>{t("action.cancel", "Cancel")}</Button>
                  <Button onClick={handleCreatePost}>{t("action.submit", "Create")}</Button>
              </DialogFooter>
          </DialogContent>
      </Dialog>

      {/* Password Confirm Dialog */}
      <Dialog open={isPasswordDialogOpen || !!passwordTarget} onOpenChange={(open) => {
          setIsPasswordDialogOpen(open);
          if (!open) setPasswordTarget(null);
      }}>
          <DialogContent className="sm:max-w-[400px]">
              <DialogHeader>
                  <DialogTitle>{t("dialog.confirmPassword", "Enter Password")}</DialogTitle>
              </DialogHeader>
              <div className="py-4 space-y-4">
                  <p className="text-sm text-muted-foreground">{t("dialog.passwordDetail", "Please enter the password used when writing this item.")}</p>
                  <Input 
                      type="password" 
                      placeholder={t("placeholder.password", "Password")} 
                      value={passwordInput} 
                      onChange={e => setPasswordInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && executePasswordAction()}
                  />
              </div>
              <DialogFooter>
                  <Button variant="outline" onClick={() => { setIsPasswordDialogOpen(false); setPasswordTarget(null); }}>{t("action.cancel", "Cancel")}</Button>
                  <Button variant="destructive" onClick={executePasswordAction} disabled={!passwordInput}>
                      {t("action.confirm", "Confirm")}
                  </Button>
              </DialogFooter>
          </DialogContent>
      </Dialog>
    </div>
  );
}
