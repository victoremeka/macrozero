import { Button } from "@/components/ui/button";
import { BackgroundBeams } from "./ui/background-beams";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export function Hero() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate("/dashboard");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="h-screen w-full bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950 relative flex flex-col items-center justify-center antialiased overflow-hidden">
      {/* Animated grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />

      {/* Hero content */}
      <div className="relative z-20 max-w-6xl mx-auto px-6 text-center">
        {/* Main heading with enhanced styling */}
        <h1 className="relative text-6xl md:text-8xl font-black mb-6 tracking-tight">
          <span className="bg-gradient-to-r from-white via-purple-200 to-cyan-300 bg-clip-text text-transparent drop-shadow-2xl">
            MacroZero
          </span>
        </h1>

        {/* Subheading with better hierarchy */}
        <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto mb-4 font-light leading-relaxed">
          Multi-agent system that understand your codebase, automate GitHub workflows,
          and remember every fix
        </p>

        <br />


        {/* CTA Button with enhanced design */}
        <Button
          size="lg"
          className="group relative px-8 py-4 text-lg font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 border-0 shadow-2xl shadow-purple-500/25 transition-all duration-300 hover:shadow-purple-500/40 hover:scale-105"
          onClick={handleGetStarted}
        >
          {isAuthenticated ? (
            <>
              Continue as {user?.username}
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </>
          ) : (
            <>
              Start Building
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </Button>

      </div>

      <BackgroundBeams />

      {/* Additional floating elements for visual interest */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
    </div>
  );
}
