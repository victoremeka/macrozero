import { Button } from "@/components/ui/button";
import { BackgroundBeams } from "./ui/background-beams";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";

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
    <div className="h-screen w-full rounded-md bg-neutral-950 relative flex flex-col items-center justify-center antialiased">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h1 className="relative z-10 text-4xl md:text-7xl bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 to-neutral-600 text-center font-sans font-bold mb-6">
          MacroZero
        </h1>
        <p className="text-neutral-400 max-w-2xl mx-auto text-lg md:text-xl text-center relative z-10 mb-8 leading-relaxed">
          Multi-agent system that summarizes GitHub bugs, drafts PRs, reviews
          code, and recalls past fixes.
        </p>
        <Button
          className="relative z-10 px-8 py-3 text-lg font-medium"
          onClick={handleGetStarted}
        >
          {isAuthenticated ? `Continue as ${user?.username}` : "Get Started"}
        </Button>
      </div>
      <BackgroundBeams />
    </div>
  );
}
