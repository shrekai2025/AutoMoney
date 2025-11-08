import { Card, CardContent } from "./ui/card";
import { Shield, LogIn } from "lucide-react";
import { GoogleAuth } from "./GoogleAuth";

interface LoginPlaceholderProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

export function LoginPlaceholder({ title, description, icon: Icon }: LoginPlaceholderProps) {
  return (
    <div className="flex items-center justify-center min-h-[500px]">
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm max-w-md w-full">
        <CardContent className="pt-12 pb-12 px-8 text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-2xl flex items-center justify-center">
            <Icon className="w-10 h-10 text-purple-400" />
          </div>

          <h2 className="text-white text-2xl font-semibold mb-3">{title}</h2>
          <p className="text-slate-400 text-sm mb-8 leading-relaxed">
            {description}
          </p>

          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-2 text-slate-500 text-xs">
              <Shield className="w-4 h-4" />
              <span>Sign in with your Google account to continue</span>
            </div>

            <div className="w-full flex justify-center">
              <GoogleAuth />
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-700/50">
            <div className="flex items-start gap-3 text-left">
              <LogIn className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-white text-sm font-medium mb-1">Why sign in?</h3>
                <ul className="text-slate-400 text-xs space-y-1">
                  <li>• Access personalized AI-powered insights</li>
                  <li>• Track your portfolio and strategies</li>
                  <li>• Get real-time market analysis</li>
                  <li>• Deploy and manage AI trading squads</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
