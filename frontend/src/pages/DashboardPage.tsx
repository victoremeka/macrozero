import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles } from "lucide-react";

export function DashboardPage() {
  const { user, isLoading } = useAuth();

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
    <div className="min-h-screen bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950 flex flex-col items-center justify-center gap-8">
      {/* Greeting text */}
      <p className="text-gray-300 text-5xl text-center">
        👋 Hi {user.username}, we are cooking ....
      </p>

      {/* Centered square card */}
      <Card className="w-80 h-80 border-purple-500/10 bg-black/20 backdrop-blur-md">
        <CardContent className="p-6 h-full flex flex-col items-center justify-center text-center">
          <Avatar className="h-24 w-24 ring-0 mb-6">
            <AvatarImage src={user.avatar_url} alt={user.username} />
            <AvatarFallback className="bg-purple-500 text-white text-3xl font-bold">
              {user.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <h2 className="text-2xl font-bold text-white">
            {user.name || user.username}
          </h2>
        </CardContent>
      </Card>
    </div>
  );
}
