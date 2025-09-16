import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, Loader2, Github } from "lucide-react";
import { API_BASE_URL } from "../../lib/auth";
import axios from "axios";

export function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      // Handle OAuth errors from GitHub
      if (error) {
        setStatus("error");
        setErrorMessage(
          errorDescription || "GitHub authentication was cancelled or failed"
        );
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        setStatus("error");
        setErrorMessage("Missing authorization code or state parameter");
        return;
      }

      try {
        // The backend will handle the OAuth exchange and set the cookie
        const callbackUrl = `${API_BASE_URL}/auth/callback`;

        const response = await axios.post(callbackUrl, { code, state }, {
          headers: {
            "Content-Type": "application/json",
          },
          withCredentials: true, // Include cookies
        });

        if (response.status === 200) {
          // If the response is successful, refresh the user context
          await refreshUser();
          setStatus("success");
          navigate("/dashboard");
        } else {
          // If the response is not successful, extract the error message
          const errorData = response.data;
          setStatus("error");
          setErrorMessage(errorData.message || "Unknown error");
        }
      } catch (error) {
        console.error("Callback processing error:", error);
        setStatus("error");
        setErrorMessage("Network error during authentication");
      }
    };

    handleCallback();
  }, [searchParams, navigate, refreshUser]);

  const handleRetry = () => {
    // Redirect back to login
    navigate("/login");
  };

  const renderContent = () => {
    switch (status) {
      case "loading":
        return (
          <div className="text-center py-8">
            <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Authenticating
            </h2>
            <p className="text-gray-400">
              Processing your GitHub authentication...
            </p>
          </div>
        );

      case "success":
        return (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Authentication Successful!
            </h2>
            <p className="text-gray-400 mb-4">
              Redirecting to your dashboard...
            </p>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-emerald-500 h-2 rounded-full animate-pulse"
                style={{ width: "100%" }}
              ></div>
            </div>
          </div>
        );

      case "error":
        return (
          <div className="text-center py-8">
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">
              Authentication Failed
            </h2>
            <Alert className="border-red-500/20 bg-red-950/20 mb-6">
              <XCircle className="h-4 w-4" />
              <AlertDescription className="text-red-400">
                {errorMessage}
              </AlertDescription>
            </Alert>
            <Button
              onClick={handleRetry}
              className="bg-[#24292e] hover:bg-[#1b1f23] text-white border border-gray-600 hover:border-gray-500"
            >
              <Github className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-950 via-neutral-950 to-blue-950 p-4 relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:24px_24px] opacity-30" />
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-black bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent mb-2">
            MacroZero
          </h1>
        </div>

        <Card className="border-gray-700/50 bg-gray-900/40 backdrop-blur-xl shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-lg font-semibold text-white flex items-center justify-center gap-2">
              <Github className="w-5 h-5" />
              GitHub Authentication
            </CardTitle>
          </CardHeader>
          <CardContent>{renderContent()}</CardContent>
        </Card>
      </div>
    </div>
  );
}
