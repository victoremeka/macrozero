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
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

        <div className="relative z-20 max-w-6xl mx-auto px-6 text-center">
        {/* Main heading with enhanced styling */}
        <h1 className="relative text-6xl md:text-8xl font-black mb-6 tracking-tight">
          <span className="bg-gradient-to-r from-white via-purple-200 to-cyan-300 bg-clip-text text-transparent drop-shadow-2xl">
            MacroZero
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto mb-4 font-light leading-relaxed">
          Multi-agent system that understands your codebase, automate GitHub workflows,
          and remember every fix
        </p>

        <br />
        <Button
          onClick={login}
          disabled={isLoading}
          size="lg"
          className="w-[20rem] bg-[#24292e] hover:bg-[#1b1f23] text-white border border-gray-600 hover:border-gray-500 transition-all duration-200"
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
