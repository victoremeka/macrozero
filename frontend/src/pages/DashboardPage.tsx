import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LogOut,
  Github,
  Sparkles,
} from "lucide-react";

export function DashboardPage() {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950">
        <div className="text-center">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
            <Sparkles className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-purple-400" />
          </div>
          <p className="text-gray-300 text-lg">Initializing MacroZero...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950">
        <Card className="w-full max-w-md border-red-500/20 bg-red-950/20 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-red-400">Access Denied</CardTitle>
            <p className="text-gray-300">Authentication required to continue</p>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950 relative">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] opacity-30" />

      <div className="relative z-10 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <header className="flex items-center justify-between mb-12">
            <div>
              <h1 className="text-4xl font-black bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent mb-2">
                MacroZero
              </h1>
              <p className="text-gray-400">
                Welcome back, {user.name || user.username}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={logout}
              className="border-gray-600 hover:border-red-500 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </header>

          {/* User Profile Card */}
          <Card className="mb-8 border-purple-500/20 bg-gradient-to-r from-purple-950/40 to-blue-950/40 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-6">
                  <Avatar className="h-16 w-16 ring-2 ring-purple-500/50">
                    <AvatarImage src={user.avatar_url} alt={user.username} />
                    <AvatarFallback className="bg-purple-500 text-white text-xl font-bold">
                      {user.username.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      {user.name || user.username}
                    </h2>
                    <p className="text-purple-300 flex items-center gap-2">
                      <Github className="w-4 h-4" />@{user.username}
                    </p>
                    {user.email && (
                      <p className="text-gray-400 text-sm">{user.email}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-medium">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                    Connected
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    ID: {user.github_id}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

        </div>
      </div>

      {/* Floating background elements */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/5 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse delay-1000" />
    </div>
  );
}
