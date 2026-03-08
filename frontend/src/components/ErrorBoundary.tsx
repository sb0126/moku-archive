"use client";

import React, { Component, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryClass extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return <ErrorBoundaryFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}

function ErrorBoundaryFallback({ error }: { error?: Error }) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6 text-center">
      <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
      <h2 className="text-2xl font-semibold mb-2 text-foreground">
        {t("boundary.title", "Oops, something went wrong")}
      </h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        {t("boundary.message", "We're sorry for the inconvenience. Please try refreshing the page or contact support if the problem persists.")}
      </p>
      {process.env.NODE_ENV === "development" && error && (
        <pre className="bg-muted p-4 rounded text-left text-sm text-muted-foreground max-w-2xl overflow-auto mb-6">
          {error.message}
        </pre>
      )}
      <Button onClick={() => window.location.reload()} className="bg-primary hover:bg-primary/90">
        {t("boundary.retry", "Refresh Page")}
      </Button>
    </div>
  );
}

export function ErrorBoundary({ children }: Props) {
  return <ErrorBoundaryClass>{children}</ErrorBoundaryClass>;
}
