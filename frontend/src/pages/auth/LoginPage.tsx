import { BackgroundBeams } from "@/components/ui/background-beams";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { Github } from "lucide-react";

export function LoginPage() {
  const { login, isLoading } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950 p-4 relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] opacity-30" />
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo and branding */}
        <div className="text-center mb-8">
          <h1 className="relative text-6xl md:text-8xl font-black mb-6 tracking-tight">
            <span className="bg-gradient-to-r from-white via-purple-200 to-cyan-300 bg-clip-text text-transparent drop-shadow-2xl">
              MacroZero
            </span>
          </h1>
          <p className="text-gray-400">
            Multi-agent system that summarizes GitHub bugs, drafts PRs, reviews
            code, and recalls past fixes.
          </p>
        </div>
        <Button
          onClick={login}
          disabled={isLoading}
          size="lg"
          className="w-full bg-[#24292e] hover:bg-[#1b1f23] text-white border border-gray-600 hover:border-gray-500 transition-all duration-200"
        >
          <Github className="mr-3 h-5 w-5" />
          {isLoading ? (
            <span className="flex items-center">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
              Signing in...
            </span>
          ) : (
            "Continue with GitHub"
          )}
        </Button>
      </div>
      <BackgroundBeams />
    </div>
  );
}
