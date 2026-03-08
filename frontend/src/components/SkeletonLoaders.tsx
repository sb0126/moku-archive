import { Skeleton } from "@/components/ui/skeleton";

export function PageSkeleton() {
  return (
    <div className="container mx-auto px-6 py-12 flex flex-col gap-6">
      <Skeleton className="h-10 w-1/3 mb-4 rounded-md" />
      <Skeleton className="h-6 w-full rounded-md" />
      <Skeleton className="h-6 w-5/6 rounded-md" />
      <Skeleton className="h-6 w-4/6 rounded-md" />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    </div>
  );
}

export function PostListSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-4 border border-[#2C2825]/8 rounded-xl bg-white shadow-sm">
          <Skeleton className="h-10 w-10 sm:h-12 sm:w-12 rounded-full shrink-0" />
          <div className="flex-1 space-y-3 w-full sm:w-auto">
            <Skeleton className="h-5 w-3/4 rounded-md" />
            <Skeleton className="h-4 w-1/4 rounded-md" />
          </div>
          <div className="flex items-center gap-2 self-end sm:self-auto">
            <Skeleton className="h-8 w-16 rounded-full shrink-0" />
            <Skeleton className="h-8 w-16 rounded-full shrink-0" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ArticleCardSkeleton() {
  return (
    <div className="flex flex-col gap-3 group">
      <Skeleton className="h-48 md:h-64 w-full rounded-2xl" />
      <div className="flex gap-2 mt-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>
      <Skeleton className="h-6 w-3/4 rounded-md mt-1" />
      <Skeleton className="h-4 w-full rounded-md mt-2" />
      <Skeleton className="h-4 w-5/6 rounded-md" />
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="p-6 bg-white rounded-2xl border border-[#2C2825]/8 shadow-sm flex flex-col gap-4">
      <Skeleton className="h-5 w-1/2 rounded-md" />
      <Skeleton className="h-10 w-1/3 rounded-md" />
    </div>
  );
}

export function InquiryListSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex justify-between items-center p-4 border border-[#2C2825]/8 rounded-xl bg-white">
          <div className="space-y-2 flex-1">
            <Skeleton className="h-5 w-1/2 rounded-md" />
            <Skeleton className="h-4 w-1/4 rounded-md" />
          </div>
          <Skeleton className="h-6 w-20 rounded-full shrink-0 ml-4" />
        </div>
      ))}
    </div>
  );
}

export function PostDetailSkeleton() {
  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <Skeleton className="h-6 w-24 mb-6 rounded-full" />
      <Skeleton className="h-12 w-3/4 mb-4 rounded-md" />
      <div className="flex gap-4 mb-12 items-center">
        <Skeleton className="h-10 w-10 rounded-full shrink-0" />
        <Skeleton className="h-5 w-24 rounded-md" />
        <Skeleton className="h-5 w-32 rounded-md" />
      </div>
      
      <div className="space-y-4">
        <Skeleton className="h-4 w-full rounded-md" />
        <Skeleton className="h-4 w-full rounded-md" />
        <Skeleton className="h-4 w-5/6 rounded-md" />
        <Skeleton className="h-4 w-full rounded-md" />
        <Skeleton className="h-64 w-full rounded-xl my-8" />
        <Skeleton className="h-4 w-4/6 rounded-md" />
        <Skeleton className="h-4 w-full rounded-md" />
      </div>
    </div>
  );
}

export function ArchiveSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8">
      <div className="w-full">
        <ArticleCardSkeleton />
      </div>
      <div className="flex flex-col gap-5">
        <ArticleCardSkeleton />
        <ArticleCardSkeleton />
        <ArticleCardSkeleton />
      </div>
    </div>
  );
}
