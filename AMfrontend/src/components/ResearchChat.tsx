import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import {
  Send,
  Loader2,
  ChevronDown,
  ChevronRight,
  Network,
  Brain,
  TrendingUp,
  CheckCircle2,
  Database,
  BarChart3,
  Sparkles,
  Clock,
  Copy,
  Check,
  MessageSquare,
} from "lucide-react";
import { getAuth } from "firebase/auth";
import { useAuth } from "../contexts/AuthContext";
import { LoginPlaceholder } from "./LoginPlaceholder";

// Add CSS animation for spinner
const spinnerStyle = `
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  .spinner {
    animation: spin 1s linear infinite;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = spinnerStyle;
  document.head.appendChild(styleSheet);
}

// Type definitions
type ProcessStep = {
  id: string;
  type: "status" | "super_agent_decision" | "planning_result" | "agent_result";
  data: any;
  timestamp: string;
};

interface Message {
  role: "user" | "assistant";
  content?: string;
  timestamp: string;
  processSteps?: ProcessStep[];
  metadata?: any;
}

const AGENT_ICONS: Record<string, any> = {
  macro_agent: TrendingUp,
  ta_agent: BarChart3,
  onchain_agent: Database,
};

const AGENT_COLORS: Record<string, string> = {
  macro_agent: "text-blue-400",
  ta_agent: "text-purple-400",
  onchain_agent: "text-cyan-400",
};

const AGENT_NAMES: Record<string, string> = {
  macro_agent: "宏观经济分析",
  ta_agent: "技术分析",
  onchain_agent: "链上数据分析",
};

const EXAMPLE_QUESTIONS = [
  { text: "现在适合买BTC吗？", icon: TrendingUp, color: "from-blue-500 to-cyan-500" },
  { text: "分析当前BTC市场趋势", icon: BarChart3, color: "from-purple-500 to-pink-500" },
  { text: "宏观经济对加密货币的影响", icon: Database, color: "from-emerald-500 to-teal-500" },
  { text: "市场恐慌指数说明什么？", icon: Sparkles, color: "from-orange-500 to-red-500" },
];

const ResearchChat = () => {
  const { isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentProcessSteps, setCurrentProcessSteps] = useState<ProcessStep[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 将所有 Hooks 移到条件返回之前，确保每次渲染时 Hooks 调用顺序一致
  useEffect(() => {
    if (isAuthenticated) {
      scrollToBottom();
    }
  }, [messages, currentProcessSteps, isAuthenticated]);

  // Auto-resize textarea
  useEffect(() => {
    if (!isAuthenticated || !textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
  }, [inputMessage, isAuthenticated]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isProcessing) return;

    const userMessage = inputMessage;
    setInputMessage("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // Add user message
    const newUserMessage: Message = {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newUserMessage]);

    // Reset states
    setIsProcessing(true);
    setCurrentProcessSteps([]);

    try {
      // Get Firebase auth token
      const auth = getAuth();
      const user = auth.currentUser;
      let token = "";

      if (user) {
        try {
          token = await user.getIdToken();
        } catch (error) {
          console.error("Error getting Firebase token:", error);
        }
      }

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch("/api/v1/research/chat", {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          message: userMessage,
          chat_history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();
      let processSteps: ProcessStep[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.substring(6);
            try {
              const event = JSON.parse(jsonStr);

              if (event.type === "done") {
                setIsProcessing(false);
              } else if (event.type === "final_answer") {
                const assistantMessage: Message = {
                  role: "assistant",
                  content: event.data.answer || event.data,
                  timestamp: event.data.timestamp || new Date().toISOString(),
                  processSteps: processSteps,
                  metadata: event.data,
                };
                setMessages((prev) => [...prev, assistantMessage]);
                setCurrentProcessSteps([]);
              } else {
                const newStep: ProcessStep = {
                  id: crypto.randomUUID(),
                  type: event.type,
                  data: event.data,
                  timestamp: event.data.timestamp || new Date().toISOString(),
                };
                processSteps.push(newStep);
                setCurrentProcessSteps((prev) => [...prev, newStep]);
              }
            } catch (e) {
              console.error("Error parsing SSE event:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "抱歉，处理请求时发生错误，请稍后重试。",
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsProcessing(false);
    }
  };

  const handleExampleClick = (question: string) => {
    setInputMessage(question);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full p-4 gap-4">
      {/* Header */}
      <div className="flex-shrink-0">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-xl flex items-center justify-center">
            <Brain className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-white text-xl font-semibold">Research Chat</h2>
            <p className="text-slate-400 text-xs">AI驱动的多维度加密货币市场研究平台</p>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 bg-slate-900/50 border-slate-700/50 backdrop-blur-sm flex flex-col overflow-hidden min-h-0">
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-4 sm:p-6 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-8 sm:py-12">
                  <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl flex items-center justify-center">
                    <Brain className="w-8 h-8 sm:w-10 sm:h-10 text-cyan-400" />
                  </div>
                  <h3 className="text-white text-lg sm:text-xl mb-3 font-medium">开始您的市场研究</h3>
                  <p className="text-slate-400 text-sm max-w-md mx-auto mb-8">
                    询问任何关于加密货币、宏观经济或市场分析的问题，AI将为您提供多维度的专业分析
                  </p>

                  {/* Example Questions Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
                    {EXAMPLE_QUESTIONS.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleExampleClick(q.text)}
                        className="group relative overflow-hidden bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 rounded-xl p-4 text-left transition-all duration-200 hover:scale-105"
                      >
                        <div className={`absolute inset-0 bg-gradient-to-br ${q.color} opacity-0 group-hover:opacity-10 transition-opacity`}></div>
                        <div className="relative flex items-center gap-3">
                          <div className={`w-8 h-8 bg-gradient-to-br ${q.color} rounded-lg flex items-center justify-center opacity-80`}>
                            <q.icon className="w-4 h-4 text-white" />
                          </div>
                          <span className="text-slate-300 text-sm font-medium">{q.text}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((message, idx) => (
                <MessageComponent key={idx} message={message} />
              ))}

              {/* Show current processing steps */}
              {isProcessing && currentProcessSteps.length > 0 && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                  <ProcessStepsDisplay steps={currentProcessSteps} isLive={true} />
                </div>
              )}

              {/* Show thinking indicator */}
              {isProcessing && currentProcessSteps.length === 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'rgb(148, 163, 184)', fontSize: '0.875rem' }}>
                  <Loader2 className="spinner" style={{ width: '16px', height: '16px' }} />
                  <span>AI思考中...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700/50 flex-shrink-0 bg-slate-900/30">
          <div className="flex gap-2 items-end">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入您的问题... (Shift + Enter 换行)"
                disabled={isProcessing}
                rows={1}
                className="min-h-[44px] max-h-[120px] resize-none bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 pr-12 py-3"
              />
              <div className="absolute right-2 bottom-2 text-xs text-slate-500">
                {inputMessage.length > 0 && `${inputMessage.length} 字符`}
              </div>
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={isProcessing || !inputMessage.trim()}
              size="lg"
              className="h-[44px] px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isProcessing ? (
                <Loader2 className="spinner" style={{ width: '20px', height: '20px' }} />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            按 Enter 发送，Shift + Enter 换行
          </p>
        </div>
      </Card>
    </div>
  );
};

function MessageComponent({ message }: { message: Message }) {
  if (message.role === "user") {
    return <UserMessage message={message} />;
  }
  return <AssistantMessage message={message} />;
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
      <div style={{ maxWidth: '85%' }}>
        <div style={{
          background: 'linear-gradient(to right, rgb(37, 99, 235), rgb(59, 130, 246))',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '16px',
          borderTopRightRadius: '4px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}>
          <p style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
            {message.content}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px', paddingLeft: '4px', justifyContent: 'flex-end' }}>
          <Clock className="w-3 h-3 text-slate-500" />
          <span style={{ fontSize: '0.75rem', color: 'rgb(100, 116, 139)' }}>
            {new Date(message.timestamp).toLocaleTimeString(undefined, {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: Message }) {
  const [showProcessSteps, setShowProcessSteps] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      {/* Process Steps (collapsible) */}
      {message.processSteps && message.processSteps.length > 0 && (
        <Collapsible open={showProcessSteps} onOpenChange={setShowProcessSteps}>
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-3 text-xs text-slate-400 hover:text-slate-300 hover:bg-slate-800/50 transition-colors"
            >
              {showProcessSteps ? (
                <ChevronDown className="w-3 h-3 mr-1.5" />
              ) : (
                <ChevronRight className="w-3 h-3 mr-1.5" />
              )}
              {showProcessSteps ? "隐藏" : "查看"}分析过程
              <Badge variant="outline" className="ml-2 text-xs border-slate-600 text-slate-400">
                {message.processSteps.length} 步骤
              </Badge>
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="animate-in slide-in-from-top-2 duration-200">
            <ProcessStepsDisplay steps={message.processSteps} isLive={false} />
          </CollapsibleContent>
        </Collapsible>
      )}

      {/* Final Answer */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '12px',
          background: 'linear-gradient(to bottom right, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: '4px'
        }}>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div style={{ flex: 1, maxWidth: '85%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Badge variant="outline" className="text-xs border-emerald-500/50 text-emerald-400 bg-emerald-500/10">
              最终答案
            </Badge>
            <span style={{ fontSize: '0.75rem', color: 'rgb(100, 116, 139)' }}>
              {new Date(message.timestamp).toLocaleTimeString(undefined, {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
          <div style={{ position: 'relative' }} className="group">
            <div style={{
              fontSize: '0.875rem',
              color: 'rgb(203, 213, 225)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              background: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '12px',
              padding: '16px',
              lineHeight: '1.5'
            }}>
              {message.content}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="absolute top-2 right-2 h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-400" />
              )}
            </Button>
          </div>

          {/* Key Insights */}
          {message.metadata?.key_insights && message.metadata.key_insights.length > 0 && (
            <div style={{
              marginTop: '12px',
              padding: '16px',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Sparkles className="w-4 h-4 text-blue-400" />
                <p style={{ fontSize: '0.75rem', color: 'rgb(96, 165, 250)', fontWeight: 500 }}>关键洞察</p>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {message.metadata.key_insights.map((insight: string, i: number) => (
                  <li key={i} style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <span style={{ color: 'rgb(96, 165, 250)', marginTop: '2px' }}>•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Summary (if available) */}
          {message.metadata?.summary && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: 'rgba(30, 41, 59, 0.3)',
              border: '1px solid rgba(51, 65, 85, 0.3)',
              borderRadius: '8px'
            }}>
              <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '4px' }}>总结</p>
              <p style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)' }}>{message.metadata.summary}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProcessStepsDisplay({ steps, isLive }: { steps: ProcessStep[]; isLive: boolean }) {
  return (
    <div className="space-y-2 pl-0 sm:pl-11">
      {steps.map((step, idx) => {
        const isLatest = isLive && idx === steps.length - 1;
        const animationClass = isLatest ? "animate-in fade-in slide-in-from-top-2 duration-200" : "";
        const isCompleted = !isLatest; // If not the latest step, it's completed

        if (step.type === "status") {
          return <StatusStep key={step.id} step={step} className={animationClass} isCompleted={isCompleted} />;
        }
        if (step.type === "super_agent_decision") {
          return <SuperAgentDecisionStep key={step.id} step={step} className={animationClass} />;
        }
        if (step.type === "planning_result") {
          return <PlanningResultStep key={step.id} step={step} className={animationClass} />;
        }
        if (step.type === "agent_result") {
          return <AgentResultStep key={step.id} step={step} className={animationClass} />;
        }
        return null;
      })}
    </div>
  );
}

function StatusStep({ step, className, isCompleted }: { step: ProcessStep; className?: string; isCompleted?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
      {isCompleted ? (
        <CheckCircle2 style={{ width: '16px', height: '16px', color: 'rgb(34, 197, 94)', flexShrink: 0 }} />
      ) : (
        <Loader2 className="spinner" style={{ width: '16px', height: '16px', color: 'rgb(148, 163, 184)', flexShrink: 0 }} />
      )}
      <span style={{ fontSize: '0.875rem', color: isCompleted ? 'rgb(100, 116, 139)' : 'rgb(148, 163, 184)' }}>
        {step.data.message || step.data}
      </span>
    </div>
  );
}

function SuperAgentDecisionStep({ step, className }: { step: ProcessStep; className?: string }) {
  return (
    <Card className={`bg-slate-800/40 border-slate-700/50 ${className || ""}`}>
      <CardContent style={{ padding: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            background: 'linear-gradient(to bottom right, rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.2))',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            marginTop: '2px'
          }}>
            <Network className="w-3 h-3 text-purple-400" />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'rgb(203, 213, 225)' }}>SuperAgent 路由决策</span>
              {step.data.decision && (
                <Badge variant="outline" className="text-xs border-purple-500/50 text-purple-400 bg-purple-500/10">
                  {step.data.decision === "COMPLEX_ANALYSIS" ? "复杂分析" : "直接回答"}
                </Badge>
              )}
              {step.data.confidence && (
                <Badge variant="outline" className="text-xs border-slate-600 text-slate-400">
                  {(step.data.confidence * 100).toFixed(0)}%
                </Badge>
              )}
            </div>
            <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', lineHeight: '1.5' }}>{step.data.reasoning}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PlanningResultStep({ step, className }: { step: ProcessStep; className?: string }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <Card className={`bg-slate-800/40 border-slate-700/50 ${className || ""}`}>
      <CardContent style={{ padding: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <div style={{
            width: '20px',
            height: '20px',
            background: 'linear-gradient(to bottom right, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2))',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            marginTop: '2px'
          }}>
            <Brain className="w-3 h-3 text-cyan-400" />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'rgb(203, 213, 225)' }}>PlanningAgent 任务规划</span>
              {showDetails ? (
                <ChevronDown
                  className="w-3.5 h-3.5 text-slate-400 cursor-pointer hover:text-slate-300"
                  style={{ marginLeft: 'auto' }}
                  onClick={() => setShowDetails(false)}
                />
              ) : (
                <ChevronRight
                  className="w-3.5 h-3.5 text-slate-400 cursor-pointer hover:text-slate-300"
                  style={{ marginLeft: 'auto' }}
                  onClick={() => setShowDetails(true)}
                />
              )}
            </div>
            {step.data.task_breakdown?.analysis_phase && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <p style={{ fontSize: '0.75rem', color: 'rgb(100, 116, 139)' }}>选择的分析维度：</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {step.data.task_breakdown.analysis_phase.map((task: any, idx: number) => (
                    <Badge key={idx} variant="outline" className="text-xs border-cyan-500/50 text-cyan-400 bg-cyan-500/10">
                      {AGENT_NAMES[task.agent] || task.agent}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {showDetails && step.data.reasoning && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(51, 65, 85, 0.3)' }}>
                <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', lineHeight: '1.5' }}>{step.data.reasoning}</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AgentResultStep({ step, className }: { step: ProcessStep; className?: string }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const agentKey = step.data.agent_name || "default";
  const Icon = AGENT_ICONS[agentKey] || BarChart3;
  const colorClass = AGENT_COLORS[agentKey] || "text-slate-400";

  const getSignalColor = (signal: string) => {
    switch (signal?.toUpperCase()) {
      case "BULLISH":
        return "border-emerald-500/50 text-emerald-400 bg-emerald-500/10";
      case "BEARISH":
        return "border-red-500/50 text-red-400 bg-red-500/10";
      case "NEUTRAL":
        return "border-yellow-500/50 text-yellow-400 bg-yellow-500/10";
      default:
        return "border-slate-500/50 text-slate-400 bg-slate-500/10";
    }
  };

  const getAgentGradient = (agent: string) => {
    if (agent === 'macro_agent') return 'linear-gradient(to bottom right, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.2))';
    if (agent === 'ta_agent') return 'linear-gradient(to bottom right, rgba(168, 85, 247, 0.2), rgba(147, 51, 234, 0.2))';
    return 'linear-gradient(to bottom right, rgba(6, 182, 212, 0.2), rgba(8, 145, 178, 0.2))';
  };

  return (
    <Card className={`bg-slate-800/40 border-slate-700/50 ${className || ""}`}>
      <CardHeader style={{ padding: '12px', paddingBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <div style={{
              width: '24px',
              height: '24px',
              background: getAgentGradient(agentKey),
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Icon className={`w-3.5 h-3.5 ${colorClass}`} />
            </div>
            <CardTitle style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)' }}>
              {AGENT_NAMES[agentKey] || agentKey}
            </CardTitle>
            {step.data.signal && (
              <Badge variant="outline" className={`text-xs ${getSignalColor(step.data.signal)}`} style={{ marginLeft: 'auto' }}>
                {step.data.signal}
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0 text-slate-400 hover:text-slate-300"
            style={{ marginLeft: '8px' }}
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent style={{ padding: '12px', paddingTop: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Summary */}
          {step.data.reasoning && (
            <div>
              <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '6px' }}>分析结论</p>
              <p style={{
                fontSize: '0.875rem',
                color: 'rgb(203, 213, 225)',
                background: 'rgba(15, 23, 42, 0.4)',
                border: '1px solid rgba(51, 65, 85, 0.3)',
                borderRadius: '8px',
                padding: '12px',
                lineHeight: '1.5'
              }}>
                {step.data.reasoning}
              </p>
            </div>
          )}

          {/* Confidence */}
          {step.data.confidence && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'rgb(100, 116, 139)' }}>信心度:</span>
              <Badge variant="outline" className="text-xs border-slate-600 text-slate-300">
                {(step.data.confidence * 100).toFixed(0)}%
              </Badge>
            </div>
          )}

          {/* Agent-specific Data Display */}
          {agentKey === 'ta_agent' && step.data.technical_indicators && (
            <TechnicalIndicatorsDisplay data={step.data} />
          )}

          {agentKey === 'macro_agent' && step.data.key_factors && (
            <MacroIndicatorsDisplay data={step.data} />
          )}

          {agentKey === 'onchain_agent' && step.data.onchain_metrics && (
            <OnChainIndicatorsDisplay data={step.data} />
          )}

          {/* Full Conversation */}
          {(step.data.prompt_sent || step.data.llm_response) && (
            <div style={{ borderTop: '1px solid rgba(51, 65, 85, 0.3)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Prompt Sent */}
              {step.data.prompt_sent && (
                <Collapsible open={showPrompt} onOpenChange={setShowPrompt}>
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-slate-800/50"
                    >
                      {showPrompt ? <ChevronDown className="w-3 h-3 mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                      查看发送的提示词
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="animate-in slide-in-from-top-2 duration-200">
                    <div className="mt-2 p-3 bg-blue-950/30 border border-blue-800/30 rounded-lg">
                      <p className="text-xs text-blue-400 mb-2">📤 发送给 LLM</p>
                      <pre className="text-xs text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto font-mono leading-relaxed">
                        {step.data.prompt_sent}
                      </pre>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              )}

              {/* LLM Response */}
              {step.data.llm_response && (
                <Collapsible open={showResponse} onOpenChange={setShowResponse}>
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-slate-800/50"
                    >
                      {showResponse ? <ChevronDown className="w-3 h-3 mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                      查看 LLM 完整响应
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="animate-in slide-in-from-top-2 duration-200">
                    <div className="mt-2 p-3 bg-emerald-950/30 border border-emerald-800/30 rounded-lg">
                      <p className="text-xs text-emerald-400 mb-2">📥 LLM 返回</p>
                      <pre className="text-xs text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto font-mono leading-relaxed">
                        {step.data.llm_response}
                      </pre>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

// Technical Indicators Display Component for TAAgent
function TechnicalIndicatorsDisplay({ data }: { data: any }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{
        background: 'rgba(168, 85, 247, 0.05)',
        border: '1px solid rgba(168, 85, 247, 0.2)',
        borderRadius: '8px',
        padding: '12px'
      }}>
        <p style={{ fontSize: '0.75rem', color: 'rgb(168, 85, 247)', marginBottom: '8px', fontWeight: 500 }}>
          📊 技术指标数据
        </p>

        {/* EMA Indicators */}
        {data.technical_indicators.ema && (
          <div style={{ marginBottom: '12px' }}>
            <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '6px' }}>均线系统 (EMA)</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.75rem' }}>
              {data.technical_indicators.ema.ema_9 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>EMA 9:</span>
                  <span style={{ color: 'rgb(203, 213, 225)' }}>${data.technical_indicators.ema.ema_9.value.toFixed(2)}</span>
                </div>
              )}
              {data.technical_indicators.ema.ema_20 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>EMA 20:</span>
                  <span style={{ color: 'rgb(203, 213, 225)' }}>${data.technical_indicators.ema.ema_20.value.toFixed(2)}</span>
                </div>
              )}
              {data.technical_indicators.ema.ema_50 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>EMA 50:</span>
                  <span style={{ color: 'rgb(203, 213, 225)' }}>${data.technical_indicators.ema.ema_50.value.toFixed(2)}</span>
                </div>
              )}
              {data.technical_indicators.ema.ema_200 && data.technical_indicators.ema.ema_200.value > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>EMA 200:</span>
                  <span style={{ color: 'rgb(203, 213, 225)' }}>${data.technical_indicators.ema.ema_200.value.toFixed(2)}</span>
                </div>
              )}
            </div>
            {data.technical_indicators.ema.trend && (
              <div style={{ marginTop: '6px', padding: '4px 8px', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '4px', fontSize: '0.75rem' }}>
                <span style={{ color: 'rgb(148, 163, 184)' }}>趋势: </span>
                <span style={{ color: 'rgb(203, 213, 225)' }}>{data.technical_indicators.ema.trend}</span>
              </div>
            )}
          </div>
        )}

        {/* RSI */}
        {data.technical_indicators.rsi && (
          <div style={{ marginBottom: '12px' }}>
            <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '6px' }}>相对强弱指标 (RSI)</p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, padding: '8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>当前值:</span>
                  <span style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.technical_indicators.rsi.value.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgb(148, 163, 184)' }}>状态:</span>
                  <Badge variant="outline" className="text-xs border-purple-500/50 text-purple-400 bg-purple-500/10">
                    {data.technical_indicators.rsi.status}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MACD */}
        {data.technical_indicators.macd && (
          <div style={{ marginBottom: '12px' }}>
            <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '6px' }}>MACD 指标</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <span style={{ color: 'rgb(148, 163, 184)' }}>MACD:</span>
                <span style={{ color: 'rgb(203, 213, 225)' }}>{data.technical_indicators.macd.macd.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <span style={{ color: 'rgb(148, 163, 184)' }}>Signal:</span>
                <span style={{ color: 'rgb(203, 213, 225)' }}>{data.technical_indicators.macd.signal.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', gridColumn: 'span 2' }}>
                <span style={{ color: 'rgb(148, 163, 184)' }}>Histogram:</span>
                <span style={{ color: data.technical_indicators.macd.histogram >= 0 ? 'rgb(52, 211, 153)' : 'rgb(248, 113, 113)', fontWeight: 500 }}>
                  {data.technical_indicators.macd.histogram.toFixed(2)}
                </span>
              </div>
            </div>
            {data.technical_indicators.macd.status && (
              <div style={{ marginTop: '6px', padding: '4px 8px', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '4px', fontSize: '0.75rem' }}>
                <span style={{ color: 'rgb(148, 163, 184)' }}>状态: </span>
                <span style={{ color: 'rgb(203, 213, 225)' }}>{data.technical_indicators.macd.status}</span>
              </div>
            )}
          </div>
        )}

        {/* Bollinger Bands */}
        {data.technical_indicators.bollinger_bands && (
          <div>
            <p style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)', marginBottom: '6px' }}>布林带 (Bollinger Bands)</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '0.75rem' }}>
              <div style={{ padding: '6px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>上轨</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>${data.technical_indicators.bollinger_bands.upper.toFixed(2)}</div>
              </div>
              <div style={{ padding: '6px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>中轨</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>${data.technical_indicators.bollinger_bands.middle.toFixed(2)}</div>
              </div>
              <div style={{ padding: '6px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>下轨</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>${data.technical_indicators.bollinger_bands.lower.toFixed(2)}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Support and Resistance Levels */}
      {(data.support_levels || data.resistance_levels) && (
        <div style={{
          background: 'rgba(168, 85, 247, 0.05)',
          border: '1px solid rgba(168, 85, 247, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(168, 85, 247)', marginBottom: '8px', fontWeight: 500 }}>
            📍 关键价位
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {data.support_levels && data.support_levels.length > 0 && (
              <div>
                <p style={{ fontSize: '0.75rem', color: 'rgb(52, 211, 153)', marginBottom: '6px' }}>支撑位</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {data.support_levels.map((level: number, i: number) => (
                    <div key={i} style={{
                      padding: '4px 8px',
                      background: 'rgba(52, 211, 153, 0.1)',
                      border: '1px solid rgba(52, 211, 153, 0.2)',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: 'rgb(52, 211, 153)'
                    }}>
                      ${level.toFixed(2)}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {data.resistance_levels && data.resistance_levels.length > 0 && (
              <div>
                <p style={{ fontSize: '0.75rem', color: 'rgb(248, 113, 113)', marginBottom: '6px' }}>阻力位</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {data.resistance_levels.map((level: number, i: number) => (
                    <div key={i} style={{
                      padding: '4px 8px',
                      background: 'rgba(248, 113, 113, 0.1)',
                      border: '1px solid rgba(248, 113, 113, 0.2)',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: 'rgb(248, 113, 113)'
                    }}>
                      ${level.toFixed(2)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Patterns */}
      {data.key_patterns && data.key_patterns.length > 0 && (
        <div style={{
          background: 'rgba(168, 85, 247, 0.05)',
          border: '1px solid rgba(168, 85, 247, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(168, 85, 247)', marginBottom: '8px', fontWeight: 500 }}>
            🔍 关键形态
          </p>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.key_patterns.map((pattern: string, i: number) => (
              <li key={i} style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <span style={{ color: 'rgb(168, 85, 247)', marginTop: '2px' }}>•</span>
                <span>{pattern}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Trend Analysis */}
      {data.trend_analysis && (
        <div style={{
          background: 'rgba(168, 85, 247, 0.05)',
          border: '1px solid rgba(168, 85, 247, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(168, 85, 247)', marginBottom: '8px', fontWeight: 500 }}>
            📈 趋势分析
          </p>
          <p style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', lineHeight: '1.5' }}>
            {data.trend_analysis}
          </p>
        </div>
      )}
    </div>
  );
}

// Macro Indicators Display Component for MacroAgent
function MacroIndicatorsDisplay({ data }: { data: any }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Market Context Data */}
      {data.market_context && (
        <div style={{
          background: 'rgba(59, 130, 246, 0.05)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(59, 130, 246)', marginBottom: '8px', fontWeight: 500 }}>
            📊 市场数据
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.75rem' }}>
            {/* BTC Price */}
            {data.market_context.btc_price && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>BTC价格</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>${data.market_context.btc_price.toLocaleString()}</span>
                  {data.market_context.price_change_24h != null && (
                    <span style={{
                      color: data.market_context.price_change_24h >= 0 ? 'rgb(52, 211, 153)' : 'rgb(248, 113, 113)',
                      fontSize: '0.7rem'
                    }}>
                      {data.market_context.price_change_24h >= 0 ? '+' : ''}{data.market_context.price_change_24h.toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* DXY Index */}
            {data.market_context.dxy_index != null && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>美元指数 (DXY)</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.market_context.dxy_index.toFixed(2)}</div>
              </div>
            )}

            {/* Fed Rate */}
            {data.market_context.fed_rate != null && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>联邦基金利率</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.market_context.fed_rate.toFixed(2)}%</div>
              </div>
            )}

            {/* M2 Growth */}
            {data.market_context.m2_growth != null && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>M2增速</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.market_context.m2_growth.toFixed(2)}%</div>
              </div>
            )}

            {/* Treasury Yield */}
            {data.market_context.treasury_yield != null && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>10年期国债收益率</div>
                <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.market_context.treasury_yield.toFixed(2)}%</div>
              </div>
            )}

            {/* Fear & Greed Index */}
            {data.market_context.fear_greed_value != null && (
              <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
                <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>恐慌贪婪指数</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{data.market_context.fear_greed_value}</span>
                  {data.market_context.fear_greed_classification && (
                    <Badge variant="outline" className="text-xs border-slate-600 text-slate-400">
                      {data.market_context.fear_greed_classification}
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Factors */}
      {data.key_factors && data.key_factors.length > 0 && (
        <div style={{
          background: 'rgba(59, 130, 246, 0.05)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(59, 130, 246)', marginBottom: '8px', fontWeight: 500 }}>
            🔑 关键因素
          </p>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.key_factors.map((factor: string, i: number) => (
              <li key={i} style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <span style={{ color: 'rgb(59, 130, 246)', marginTop: '2px' }}>•</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk Assessment */}
      {data.risk_assessment && (
        <div style={{
          background: 'rgba(59, 130, 246, 0.05)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(59, 130, 246)', marginBottom: '8px', fontWeight: 500 }}>
            ⚠️ 风险评估
          </p>
          <p style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', lineHeight: '1.5' }}>
            {data.risk_assessment}
          </p>
        </div>
      )}
    </div>
  );
}

// OnChain Indicators Display Component for OnChainAgent
function OnChainIndicatorsDisplay({ data }: { data: any }) {
  const metrics = data.onchain_metrics || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Network Activity */}
      <div style={{
        background: 'rgba(6, 182, 212, 0.05)',
        border: '1px solid rgba(6, 182, 212, 0.2)',
        borderRadius: '8px',
        padding: '12px'
      }}>
        <p style={{ fontSize: '0.75rem', color: 'rgb(6, 182, 212)', marginBottom: '8px', fontWeight: 500 }}>
          🔗 网络活跃度
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.75rem' }}>
          {/* Active Addresses */}
          {metrics.active_addresses != null && (
            <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
              <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>活跃地址数</div>
              <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.active_addresses.toLocaleString()}</div>
            </div>
          )}

          {/* Daily Transactions */}
          {metrics.daily_transactions != null && (
            <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
              <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>日均交易数</div>
              <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.daily_transactions.toLocaleString()}</div>
            </div>
          )}

          {/* Hash Rate */}
          {metrics.hash_rate_eh != null && (
            <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
              <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>算力</div>
              <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.hash_rate_eh.toFixed(2)} EH/s</div>
            </div>
          )}

          {/* Transaction Fees */}
          {metrics.transaction_fees_sat_vb != null && (
            <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px' }}>
              <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>交易费用</div>
              <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.transaction_fees_sat_vb} sat/vB</div>
            </div>
          )}
        </div>
      </div>

      {/* Network Health & Congestion */}
      <div style={{
        background: 'rgba(6, 182, 212, 0.05)',
        border: '1px solid rgba(6, 182, 212, 0.2)',
        borderRadius: '8px',
        padding: '12px'
      }}>
        <p style={{ fontSize: '0.75rem', color: 'rgb(6, 182, 212)', marginBottom: '8px', fontWeight: 500 }}>
          💊 网络健康状态
        </p>

        {/* Network Health Status */}
        {data.network_health && (
          <div style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'rgb(148, 163, 184)' }}>状态:</span>
              <Badge
                variant="outline"
                className={`text-xs ${
                  data.network_health === 'HEALTHY'
                    ? 'border-emerald-500/50 text-emerald-400 bg-emerald-500/10'
                    : data.network_health === 'CONGESTED'
                    ? 'border-red-500/50 text-red-400 bg-red-500/10'
                    : 'border-yellow-500/50 text-yellow-400 bg-yellow-500/10'
                }`}
              >
                {data.network_health === 'HEALTHY' ? '健康' : data.network_health === 'CONGESTED' ? '拥堵' : '一般'}
              </Badge>
            </div>
          </div>
        )}

        {/* Mempool TX Count */}
        {metrics.mempool_tx_count != null && (
          <div style={{ padding: '6px 8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', fontSize: '0.75rem' }}>
            <div style={{ color: 'rgb(148, 163, 184)', marginBottom: '2px' }}>待确认交易</div>
            <div style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.mempool_tx_count.toLocaleString()}</div>
          </div>
        )}
      </div>

      {/* Valuation Metrics */}
      {metrics.nvt_ratio != null && (
        <div style={{
          background: 'rgba(6, 182, 212, 0.05)',
          border: '1px solid rgba(6, 182, 212, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(6, 182, 212)', marginBottom: '8px', fontWeight: 500 }}>
            📊 估值指标
          </p>
          <div style={{ padding: '8px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '4px', fontSize: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'rgb(148, 163, 184)' }}>简化版 NVT 比率:</span>
              <span style={{ color: 'rgb(203, 213, 225)', fontWeight: 500 }}>{metrics.nvt_ratio.toFixed(2)}</span>
            </div>
            <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'rgb(100, 116, 139)' }}>
              参考范围: 40-150 (数值越高可能估值越高)
            </div>
          </div>
        </div>
      )}

      {/* Key Observations */}
      {data.key_observations && data.key_observations.length > 0 && (
        <div style={{
          background: 'rgba(6, 182, 212, 0.05)',
          border: '1px solid rgba(6, 182, 212, 0.2)',
          borderRadius: '8px',
          padding: '12px'
        }}>
          <p style={{ fontSize: '0.75rem', color: 'rgb(6, 182, 212)', marginBottom: '8px', fontWeight: 500 }}>
            🔍 关键观察
          </p>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.key_observations.map((observation: string, i: number) => (
              <li key={i} style={{ fontSize: '0.875rem', color: 'rgb(203, 213, 225)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <span style={{ color: 'rgb(6, 182, 212)', marginTop: '2px' }}>•</span>
                <span>{observation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ResearchChat;
