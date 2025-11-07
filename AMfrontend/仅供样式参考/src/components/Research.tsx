import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
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
  Database,
  TrendingUp,
  BarChart3,
  Code,
  CheckCircle2,
  ArrowRight
} from "lucide-react";

type MessageType = 
  | 'user-message'
  | 'thinking'
  | 'routing-decision'
  | 'planning-decision'
  | 'agent-subprocess'
  | 'final-answer';

type ToolCall = {
  name: string;
  params: any;
  result: any;
};

type AgentSubprocess = {
  agentName: string;
  agentType: 'macro' | 'onchain' | 'general';
  status: 'running' | 'completed';
  analysisPhase: {
    status: 'running' | 'completed';
    tools: ToolCall[];
    result: string;
  };
  decisionPhase?: {
    status: 'running' | 'completed';
    content: string;
  };
};

type Message = {
  id: string;
  type: MessageType;
  role: 'user' | 'assistant' | 'system';
  content: string;
  rawJson?: any;
  timestamp: Date;
  isTemporary?: boolean;
  includeInHistory?: boolean;
  agentSubprocesses?: AgentSubprocess[];
};

const AGENT_ICONS = {
  macro: TrendingUp,
  onchain: Database,
  general: BarChart3,
};

const AGENT_COLORS = {
  macro: 'text-blue-400',
  onchain: 'text-purple-400',
  general: 'text-cyan-400',
};

export function Research() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const simulateComplexQuery = async (userMessage: string) => {
    setIsProcessing(true);
    const messageId = Date.now().toString();

    // Step 1: Show thinking
    const thinkingMsg: Message = {
      id: `thinking-${messageId}`,
      type: 'thinking',
      role: 'assistant',
      content: 'AI思考中...',
      timestamp: new Date(),
      isTemporary: true,
      includeInHistory: false,
    };
    setMessages(prev => [...prev, thinkingMsg]);

    await new Promise(resolve => setTimeout(resolve, 1500));

    // Step 2: SuperAgent routing decision
    const routingMsg: Message = {
      id: `routing-${messageId}`,
      type: 'routing-decision',
      role: 'assistant',
      content: '我将转交给Planning Agent处理这个复杂的金融问题',
      rawJson: {
        agent: 'SuperAgent',
        decision: 'route_to_planning',
        reason: '该问题涉及宏观经济分析和链上数据，需要多个专业agent协作',
        confidence: 0.95,
      },
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: false,
    };
    setMessages(prev => prev.filter(m => !m.isTemporary).concat(routingMsg));

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Step 3: Planning decision
    const planningMsg: Message = {
      id: `planning-${messageId}`,
      type: 'planning-decision',
      role: 'assistant',
      content: '任务涉及宏观经济、链上数据，需要宏观经济Agent和链上数据Agent参与分析，再由通用分析Agent总结结论',
      rawJson: {
        agent: 'PlanningAgent',
        task_decomposition: {
          analysis_agents: ['宏观经济Agent', '链上数据Agent'],
          synthesis_agent: '通用分析Agent',
          execution_mode: 'parallel',
        },
        estimated_time: '15-20s',
      },
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: false,
    };
    setMessages(prev => [...prev, planningMsg]);

    await new Promise(resolve => setTimeout(resolve, 800));

    // Step 4: Agent subprocesses
    const subprocessMsg: Message = {
      id: `subprocess-${messageId}`,
      type: 'agent-subprocess',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: false,
      agentSubprocesses: [
        {
          agentName: '宏观经济Agent',
          agentType: 'macro',
          status: 'running',
          analysisPhase: {
            status: 'running',
            tools: [],
            result: '',
          },
        },
        {
          agentName: '链上数据Agent',
          agentType: 'onchain',
          status: 'running',
          analysisPhase: {
            status: 'running',
            tools: [],
            result: '',
          },
        },
      ],
    };
    setMessages(prev => [...prev, subprocessMsg]);

    // Simulate macro agent analysis
    await new Promise(resolve => setTimeout(resolve, 2000));
    setMessages(prev => prev.map(m => {
      if (m.id === `subprocess-${messageId}` && m.agentSubprocesses) {
        const updated = [...m.agentSubprocesses];
        updated[0] = {
          ...updated[0],
          analysisPhase: {
            status: 'completed',
            tools: [
              {
                name: 'get_fed_rate',
                params: { date_range: '2024-2025' },
                result: { current_rate: 4.5, trend: 'stable' },
              },
              {
                name: 'get_inflation_data',
                params: { country: 'US' },
                result: { cpi: 3.2, trend: 'decreasing' },
              },
            ],
            result: '美联储利率维持在4.5%，通胀率为3.2%且呈下降趋势，宏观环境对加密市场相对友好。',
          },
          decisionPhase: {
            status: 'running',
            content: '',
          },
        };
        return { ...m, agentSubprocesses: updated };
      }
      return m;
    }));

    // Simulate onchain agent analysis
    await new Promise(resolve => setTimeout(resolve, 1800));
    setMessages(prev => prev.map(m => {
      if (m.id === `subprocess-${messageId}` && m.agentSubprocesses) {
        const updated = [...m.agentSubprocesses];
        updated[1] = {
          ...updated[1],
          analysisPhase: {
            status: 'completed',
            tools: [
              {
                name: 'get_whale_activity',
                params: { timeframe: '7d' },
                result: { whale_accumulation: true, volume_change: '+23%' },
              },
              {
                name: 'get_exchange_flows',
                params: { exchanges: ['Binance', 'Coinbase'] },
                result: { net_outflow: 45000, trend: 'bullish' },
              },
            ],
            result: '近7天鲸鱼地址累积BTC，交易所净流出45000 BTC，链上数据显示看涨信号。',
          },
          decisionPhase: {
            status: 'running',
            content: '',
          },
        };
        return { ...m, agentSubprocesses: updated };
      }
      return m;
    }));

    // Complete decision phases
    await new Promise(resolve => setTimeout(resolve, 1500));
    setMessages(prev => prev.map(m => {
      if (m.id === `subprocess-${messageId}` && m.agentSubprocesses) {
        const updated = m.agentSubprocesses.map(agent => ({
          ...agent,
          status: 'completed' as const,
          decisionPhase: {
            status: 'completed' as const,
            content: `基于${agent.agentType === 'macro' ? '宏观经济' : '链上'}数据分析，提供决策支持。`,
          },
        }));
        return { ...m, agentSubprocesses: updated };
      }
      return m;
    }));

    // Add general analysis agent
    await new Promise(resolve => setTimeout(resolve, 1000));
    setMessages(prev => prev.map(m => {
      if (m.id === `subprocess-${messageId}` && m.agentSubprocesses) {
        return {
          ...m,
          agentSubprocesses: [
            ...m.agentSubprocesses,
            {
              agentName: '通用分析Agent',
              agentType: 'general' as const,
              status: 'running' as const,
              analysisPhase: {
                status: 'running' as const,
                tools: [],
                result: '',
              },
            },
          ],
        };
      }
      return m;
    }));

    await new Promise(resolve => setTimeout(resolve, 2000));
    setMessages(prev => prev.map(m => {
      if (m.id === `subprocess-${messageId}` && m.agentSubprocesses) {
        const updated = [...m.agentSubprocesses];
        const lastIdx = updated.length - 1;
        updated[lastIdx] = {
          ...updated[lastIdx],
          status: 'completed',
          analysisPhase: {
            status: 'completed',
            tools: [
              {
                name: 'synthesize_data',
                params: { sources: ['macro_agent', 'onchain_agent'] },
                result: { correlation: 0.87, confidence: 'high' },
              },
            ],
            result: '综合宏观经济和链上数据，当前市场环境积极，两类数据相关性高达0.87。',
          },
          decisionPhase: {
            status: 'completed',
            content: '综合分析显示，当前是较好的投资时机，建议适度增加BTC配置。',
          },
        };
        return { ...m, agentSubprocesses: updated };
      }
      return m;
    }));

    // Step 5: Final answer
    await new Promise(resolve => setTimeout(resolve, 1000));
    const finalMsg: Message = {
      id: `final-${messageId}`,
      type: 'final-answer',
      role: 'assistant',
      content: `## 综合分析结果

基于多维度分析，我为您提供以下见解：

**宏观环境分析**
- 美联储利率维持在4.5%，政策立场相对稳定
- 通胀率为3.2%且呈下降趋势，为市场提供良好支撑
- 宏观环境对加密货币市场相对友好

**链上数据分析**
- 鲸鱼地址近7天持续累积BTC，显示机构信心
- 交易所净流出45000 BTC，供应收缩信号明显
- 链上活跃度上升23%，市场参与度提高

**投资建议**
综合以上数据，当前市场环境积极，多项指标显示看涨信号。建议：
1. 适度增加BTC配置，目标配置比例25-30%
2. 关注后续美联储政策动向
3. 持续监控链上数据变化

*本分析基于当前数据，投资有风险，请谨慎决策。*`,
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: true,
    };
    setMessages(prev => [...prev, finalMsg]);
    setIsProcessing(false);
  };

  const simulateSimpleQuery = async (userMessage: string) => {
    setIsProcessing(true);
    const messageId = Date.now().toString();

    // Show thinking
    const thinkingMsg: Message = {
      id: `thinking-${messageId}`,
      type: 'thinking',
      role: 'assistant',
      content: 'AI思考中...',
      timestamp: new Date(),
      isTemporary: true,
      includeInHistory: false,
    };
    setMessages(prev => [...prev, thinkingMsg]);

    await new Promise(resolve => setTimeout(resolve, 1000));

    // SuperAgent direct answer
    const routingMsg: Message = {
      id: `routing-${messageId}`,
      type: 'routing-decision',
      role: 'assistant',
      content: '我可以直接回答这个问题',
      rawJson: {
        agent: 'SuperAgent',
        decision: 'direct_answer',
        reason: '问题属于基础知识范畴，无需调用专业agent',
        confidence: 0.98,
      },
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: false,
    };
    setMessages(prev => prev.filter(m => !m.isTemporary).concat(routingMsg));

    await new Promise(resolve => setTimeout(resolve, 800));

    const finalMsg: Message = {
      id: `final-${messageId}`,
      type: 'final-answer',
      role: 'assistant',
      content: '比特币（Bitcoin）是第一个去中心化的加密货币，由中本聪在2009年创建。它基于区块链技术，通过点对点网络实现无需中介的价值传输。比特币总量上限为2100万枚，通过挖矿产生新币，并通过工作量证明（PoW）机制保证网络安全。',
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: true,
    };
    setMessages(prev => [...prev, finalMsg]);
    setIsProcessing(false);
  };

  const handleSendMessage = () => {
    if (!input.trim() || isProcessing) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      type: 'user-message',
      role: 'user',
      content: input,
      timestamp: new Date(),
      isTemporary: false,
      includeInHistory: true,
    };

    setMessages(prev => [...prev, userMsg]);
    const query = input.toLowerCase();
    setInput("");

    // Determine if complex or simple query
    if (query.includes('分析') || query.includes('市场') || query.includes('投资') || query.includes('策略')) {
      simulateComplexQuery(input);
    } else {
      simulateSimpleQuery(input);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] md:h-[calc(100vh-5rem)] flex flex-col">
      {/* Header */}
      <div className="mb-3">
        <h1 className="text-white text-xl flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-400" />
          Research Hub
        </h1>
        <p className="text-slate-400 text-xs">AI驱动的金融研究助手</p>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 bg-slate-900/50 border-slate-700/50 backdrop-blur-sm flex flex-col overflow-hidden min-h-0">
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-full flex items-center justify-center">
                    <Brain className="w-8 h-8 text-cyan-400" />
                  </div>
                  <h3 className="text-white mb-2">开始您的研究</h3>
                  <p className="text-slate-400 text-sm max-w-md mx-auto">
                    询问任何关于加密货币、宏观经济或市场分析的问题
                  </p>
                  <div className="mt-6 flex flex-wrap gap-2 justify-center">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700"
                      onClick={() => setInput("比特币是什么？")}
                    >
                      比特币是什么？
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700"
                      onClick={() => setInput("分析当前市场环境和投资建议")}
                    >
                      分析当前市场环境
                    </Button>
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <MessageComponent key={message.id} message={message} />
              ))}
              <div ref={scrollRef} />
            </div>
          </ScrollArea>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700/50 flex-shrink-0">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="输���您的问题..."
              disabled={isProcessing}
              className="bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500"
            />
            <Button
              onClick={handleSendMessage}
              disabled={isProcessing || !input.trim()}
              className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function MessageComponent({ message }: { message: Message }) {
  if (message.type === 'user-message') {
    return <UserMessage message={message} />;
  }
  if (message.type === 'thinking') {
    return <ThinkingMessage />;
  }
  if (message.type === 'routing-decision') {
    return <RoutingDecisionMessage message={message} />;
  }
  if (message.type === 'planning-decision') {
    return <PlanningDecisionMessage message={message} />;
  }
  if (message.type === 'agent-subprocess') {
    return <AgentSubprocessMessage message={message} />;
  }
  if (message.type === 'final-answer') {
    return <FinalAnswerMessage message={message} />;
  }
  return null;
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] bg-gradient-to-r from-blue-600 to-blue-500 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm">
        <p className="text-sm">{message.content}</p>
      </div>
    </div>
  );
}

function ThinkingMessage() {
  return (
    <div className="flex items-center gap-2 text-slate-400 text-sm">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span>AI思考中...</span>
    </div>
  );
}

function RoutingDecisionMessage({ message }: { message: Message }) {
  const [showJson, setShowJson] = useState(false);

  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center flex-shrink-0 mt-1">
        <Network className="w-4 h-4 text-purple-400" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline" className="text-xs border-purple-500/50 text-purple-400">
            SuperAgent
          </Badge>
        </div>
        <p className="text-sm text-slate-300 mb-2">{message.content}</p>
        {message.rawJson && (
          <Collapsible open={showJson} onOpenChange={setShowJson}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-slate-400 hover:text-slate-300">
                {showJson ? <ChevronDown className="w-3 h-3 mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                查看原始JSON
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <pre className="mt-2 p-3 bg-slate-950/50 border border-slate-800 rounded-lg text-xs text-slate-300 overflow-x-auto">
                {JSON.stringify(message.rawJson, null, 2)}
              </pre>
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </div>
  );
}

function PlanningDecisionMessage({ message }: { message: Message }) {
  const [showJson, setShowJson] = useState(false);

  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center flex-shrink-0 mt-1">
        <Brain className="w-4 h-4 text-cyan-400" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline" className="text-xs border-cyan-500/50 text-cyan-400">
            Planning Agent
          </Badge>
        </div>
        <p className="text-sm text-slate-300 mb-2">{message.content}</p>
        {message.rawJson && (
          <Collapsible open={showJson} onOpenChange={setShowJson}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-slate-400 hover:text-slate-300">
                {showJson ? <ChevronDown className="w-3 h-3 mr-1" /> : <ChevronRight className="w-3 h-3 mr-1" />}
                查看原始JSON
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <pre className="mt-2 p-3 bg-slate-950/50 border border-slate-800 rounded-lg text-xs text-slate-300 overflow-x-auto">
                {JSON.stringify(message.rawJson, null, 2)}
              </pre>
            </CollapsibleContent>
          </Collapsible>
        )}
      </div>
    </div>
  );
}

function AgentSubprocessMessage({ message }: { message: Message }) {
  return (
    <div className="space-y-3">
      {message.agentSubprocesses?.map((subprocess, idx) => (
        <AgentSubprocessCard key={idx} subprocess={subprocess} />
      ))}
    </div>
  );
}

function AgentSubprocessCard({ subprocess }: { subprocess: AgentSubprocess }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const Icon = AGENT_ICONS[subprocess.agentType];
  const colorClass = AGENT_COLORS[subprocess.agentType];

  return (
    <Card className="bg-slate-800/30 border-slate-700/50">
      <CardHeader className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full bg-slate-700/50 flex items-center justify-center ${colorClass}`}>
              <Icon className="w-3.5 h-3.5" />
            </div>
            <CardTitle className="text-sm text-white">{subprocess.agentName}</CardTitle>
            {subprocess.status === 'completed' && (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
            {subprocess.status === 'running' && (
              <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0 text-slate-400 hover:text-slate-300"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="p-3 pt-0 space-y-3">
          {/* Analysis Phase */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs border-blue-500/50 text-blue-400">
                分析阶段
              </Badge>
              {subprocess.analysisPhase.status === 'completed' && (
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              )}
              {subprocess.analysisPhase.status === 'running' && (
                <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />
              )}
            </div>
            
            {subprocess.analysisPhase.tools.length > 0 && (
              <div className="space-y-1.5">
                {subprocess.analysisPhase.tools.map((tool, idx) => (
                  <div key={idx} className="bg-slate-900/50 border border-slate-700/50 rounded p-2">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Code className="w-3 h-3 text-purple-400" />
                      <span className="text-xs text-purple-400 font-mono">{tool.name}</span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-0.5">
                      <div>参数: {JSON.stringify(tool.params)}</div>
                      <div>结果: {JSON.stringify(tool.result)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {subprocess.analysisPhase.result && (
              <p className="text-sm text-slate-300 bg-slate-900/30 border border-slate-700/30 rounded p-2">
                {subprocess.analysisPhase.result}
              </p>
            )}
          </div>

          {/* Decision Phase */}
          {subprocess.decisionPhase && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs border-green-500/50 text-green-400">
                  决策阶段
                </Badge>
                {subprocess.decisionPhase.status === 'completed' && (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                )}
                {subprocess.decisionPhase.status === 'running' && (
                  <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />
                )}
              </div>
              
              {subprocess.decisionPhase.content && (
                <p className="text-sm text-slate-300 bg-slate-900/30 border border-slate-700/30 rounded p-2">
                  {subprocess.decisionPhase.content}
                </p>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

function FinalAnswerMessage({ message }: { message: Message }) {
  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0 mt-1">
        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
      </div>
      <div className="flex-1 max-w-[85%]">
        <Badge variant="outline" className="text-xs border-emerald-500/50 text-emerald-400 mb-2">
          最终答案
        </Badge>
        <div className="prose prose-sm prose-invert max-w-none">
          <div className="text-sm text-slate-300 whitespace-pre-line bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
            {message.content}
          </div>
        </div>
      </div>
    </div>
  );
}
