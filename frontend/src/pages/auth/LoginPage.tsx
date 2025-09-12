import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { Github } from "lucide-react";

export function LoginPage() {
  const { login, isLoading } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">
            Welcome to MacroZero
          </CardTitle>
          <CardDescription>
            Sign in with your GitHub account to get started
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={login}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            <Github className="mr-2 h-5 w-5" />
            {isLoading ? "Signing in..." : "Continue with GitHub"}
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            By signing in, you agree to our terms of service and privacy policy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
