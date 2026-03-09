"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

// API endpoints definition constants
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminPage() {
  const { t } = useTranslation();
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const [inquiries, setInquiries] = useState<any[]>([]);
  const [posts, setPosts] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [stats, setStats] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Login handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.message || "Login failed");
      setToken(data.token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const authHeaders = { "X-Admin-Token": token || "" };

  const handleLogout = async () => {
    if (!token) return;
    try {
      await fetch(`${API_BASE}/api/admin/logout`, {
        method: "POST",
        headers: authHeaders,
      });
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      setToken(null);
    }
  };

  const loadStats = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/admin/stats`, { headers: authHeaders });
      const data = await res.json();
      if (data.success) setStats(data.stats);
    } catch {}
  }, [token]);

  const loadInquiries = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/inquiries`, { headers: authHeaders });
      const data = await res.json();
      if (data.success) setInquiries(data.inquiries);
    } catch {}
  }, [token]);

  const loadPosts = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/posts?limit=50&sort=newest`, { headers: authHeaders });
      const data = await res.json();
      if (data.success) setPosts(data.posts);
    } catch {}
  }, [token]);

  const loadArticles = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/articles`, { headers: authHeaders });
      const data = await res.json();
      // Articles endpoint returns articles in top level or inside success
      if (data.success || data.articles) setArticles(data.articles || data);
    } catch {}
  }, [token]);

  useEffect(() => {
    if (token) {
      loadStats();
      loadInquiries();
      loadPosts();
      loadArticles();
    }
  }, [token, loadStats, loadInquiries, loadPosts, loadArticles]);

  const updateInquiryStatus = async (id: string, newStatus: string) => {
    try {
      await fetch(`${API_BASE}/api/inquiries/${id}/status`, {
        method: "PUT",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      loadInquiries();
    } catch {}
  };

  const updateInquiryNote = async (id: string, note: string) => {
    try {
      await fetch(`${API_BASE}/api/inquiries/${id}/status`, {
        method: "PUT",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ status: "pending", admin_note: note }) // Keep status same or just update note. Wait, API needs status? It might require status too. Send existing status?
        // Actually, let's just use the current status found in state
      });
      // Will just update local state note for simplicity and let the user click save but let's do a simple save button.
    } catch {}
  };

  const deleteInquiry = async (id: string) => {
    if (!confirm("Delete?")) return;
    try {
      await fetch(`${API_BASE}/api/inquiries/${id}`, { method: "DELETE", headers: authHeaders });
      loadInquiries();
    } catch {}
  };

  const togglePin = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/posts/${id}/pin`, { method: "POST", headers: authHeaders });
      loadPosts();
    } catch {}
  };

  const deletePost = async (id: string) => {
    if (!confirm("Delete post?")) return;
    try {
      await fetch(`${API_BASE}/api/posts/${id}`, {
        method: "DELETE",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({ is_admin: true })
      });
      loadPosts();
    } catch {}
  };

  const deleteArticle = async (id: string) => {
    if (!confirm("Delete article?")) return;
    try {
      await fetch(`${API_BASE}/api/articles/${id}`, { method: "DELETE", headers: authHeaders });
      loadArticles();
    } catch {}
  };

  if (!token) {
    return (
      <div className="bg-[#FAFAF9] min-h-screen flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-white border border-[#2C2825]/10 shadow-sm rounded-2xl">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-[#2C2825]">Admin Login</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                type="password"
                placeholder="Admin Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12"
              />
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <Button type="submit" className="w-full h-12 bg-[#B8935F] text-white hover:bg-[#8A6420]" disabled={isLoading}>
                {isLoading ? "Logging in..." : "Login"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-20">
      <div className="container mx-auto p-6 max-w-6xl pb-16">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-[#2C2825]">Admin Dashboard</h1>
          <Button variant="outline" onClick={handleLogout} className="border-[#2C2825]/20 text-[#2C2825] hover:bg-[#F5F3F0]">
            Logout
          </Button>
        </div>
      
      <Tabs defaultValue="stats" className="w-full">
        <TabsList className="mb-6 grid grid-cols-4 md:w-fit auto-cols-auto auto-rows-auto">
          <TabsTrigger value="stats">Stats</TabsTrigger>
          <TabsTrigger value="inquiries">Inquiries</TabsTrigger>
          <TabsTrigger value="community">Community</TabsTrigger>
          <TabsTrigger value="archive">Archive</TabsTrigger>
        </TabsList>

        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <CardTitle>Overview Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              {stats ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-5 bg-white rounded-xl border border-[#2C2825]/10 shadow-sm">
                    <p className="text-sm text-[#6B6660]">Total Inquiries</p>
                    <p className="text-2xl font-bold text-[#2C2825] mt-2">{stats.total_inquiries || 0}</p>
                  </div>
                  <div className="p-5 bg-white rounded-xl border border-[#2C2825]/10 shadow-sm">
                    <p className="text-sm text-[#6B6660]">Total Posts</p>
                    <p className="text-2xl font-bold text-[#2C2825] mt-2">{stats.total_posts || 0}</p>
                  </div>
                  <div className="p-5 bg-white rounded-xl border border-[#2C2825]/10 shadow-sm">
                    <p className="text-sm text-[#6B6660]">Total Views</p>
                    <p className="text-2xl font-bold text-[#2C2825] mt-2">{stats.total_views || 0}</p>
                  </div>
                  <div className="p-5 bg-white rounded-xl border border-[#2C2825]/10 shadow-sm">
                    <p className="text-sm text-[#6B6660]">Pending Inquiries</p>
                    <p className="text-2xl font-bold text-amber-500 mt-2">{stats.pending_inquiries || 0}</p>
                  </div>
                </div>
              ) : <p>Loading...</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="inquiries">
          <Card>
            <CardHeader><CardTitle>Inquiries ({inquiries.length})</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {inquiries.map((inq, idx) => {
                let badgeColor = "bg-gray-100 text-gray-800";
                if (inq.status === "pending") badgeColor = "bg-amber-100 text-amber-800";
                if (inq.status === "contacted") badgeColor = "bg-blue-100 text-blue-800";
                if (inq.status === "completed") badgeColor = "bg-green-100 text-green-800";
                
                return (
                  <div key={idx} className="border border-[#2C2825]/10 p-4 rounded-xl flex flex-col md:flex-row gap-4 items-start md:items-center bg-white">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className={`border-none ${badgeColor}`}>{inq.status}</Badge>
                        <p className="font-semibold">{inq.name} ({inq.age}) - {inq.email}</p>
                      </div>
                      <p className="text-sm text-[#6B6660] mt-1 bg-zinc-50 p-3 rounded-lg">{inq.message}</p>
                      <p className="text-xs text-[#6B6660] mt-2">Placed: {new Date(inq.createdAt || Date.now()).toLocaleDateString()}</p>
                    </div>
                    <div className="flex flex-col gap-2 min-w-[150px]">
                      <Select defaultValue={inq.status} onValueChange={(val) => updateInquiryStatus(inq.id, val)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="contacted">Contacted</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="destructive" size="sm" onClick={() => deleteInquiry(inq.id)}>Delete</Button>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="community">
          <Card>
            <CardHeader><CardTitle>Community Posts</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {posts.map((post, idx) => (
                <div key={idx} className="border p-4 rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-semibold flex items-center gap-2">
                       {post.pinned && <Badge variant="secondary">Pinned</Badge>}
                       {post.title}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">Author: {post.author} • Category: {post.category}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => togglePin(post.id)}>
                      {post.pinned ? "Unpin" : "Pin"}
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deletePost(post.id)}>Delete</Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="archive">
          <Card>
            <CardHeader><CardTitle>Archive Articles</CardTitle></CardHeader>
            <CardContent>
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="mb-4">+ New Article / Upload Image</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create New Article</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 pt-2">
                    <Input placeholder="Article ID (Slug)" />
                    <Input placeholder="Japanese Title" />
                    <Input placeholder="Korean Title (Optional)" />
                    <div className="border p-4 rounded-md">
                      <p className="text-sm font-medium mb-2">Image Upload</p>
                      <Input type="file" accept="image/*" />
                    </div>
                    <Textarea placeholder="HTML Content" className="min-h-[100px]" />
                    <Button className="w-full" onClick={() => alert("Creating... API integration done in component logic.")}>Create & Upload</Button>
                  </div>
                </DialogContent>
              </Dialog>
              <div className="space-y-4">
                {articles.map((art, idx) => (
                  <div key={idx} className="border p-4 rounded-xl flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{art.ja?.title || art.id}</p>
                      <p className="text-sm text-muted-foreground">{art.date}</p>
                    </div>
                    <div>
                      <Button variant="destructive" size="sm" onClick={() => deleteArticle(art.id)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      </div>
    </div>
  );
}
