/**
 * Launch Strategy Modal - 启动策略实例弹窗
 */

import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Loader2, Rocket, X } from "lucide-react";
import {
  fetchStrategyDefinitions,
  createStrategyInstance,
  type StrategyDefinition,
} from "../lib/strategyInstanceApi";
import { toast } from "sonner";

interface LaunchStrategyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (portfolioId: string) => void;
}

export function LaunchStrategyModal({
  open,
  onOpenChange,
  onSuccess,
}: LaunchStrategyModalProps) {
  const [definitions, setDefinitions] = useState<StrategyDefinition[]>([]);
  const [loadingDefinitions, setLoadingDefinitions] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<string>("");
  const [instanceName, setInstanceName] = useState("");
  const [instanceDescription, setInstanceDescription] = useState("");
  const [initialBalance, setInitialBalance] = useState("1000");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [riskLevel, setRiskLevel] = useState<string>("medium");

  // Load strategy definitions when modal opens
  useEffect(() => {
    if (open) {
      loadDefinitions();
    }
  }, [open]);

  async function loadDefinitions() {
    try {
      setLoadingDefinitions(true);
      const data = await fetchStrategyDefinitions();
      console.log("Loaded strategy definitions:", data);
      setDefinitions(data.filter((d) => d.is_active));

      if (data.length === 0) {
        console.warn("No strategy definitions found in database");
      }
    } catch (err: any) {
      console.error("Failed to load strategy definitions:", err);
      console.error("Error details:", {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
      });

      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      toast.error("Failed to load strategy templates", {
        description: errorMsg,
      });
    } finally {
      setLoadingDefinitions(false);
    }
  }

  const selectedDefinition = definitions.find(
    (d) => d.id.toString() === selectedDefinitionId
  );

  async function handleLaunch() {
    if (!selectedDefinitionId) {
      toast.error("Please select a strategy template");
      return;
    }

    const balance = parseFloat(initialBalance);
    if (isNaN(balance) || balance <= 0) {
      toast.error("Please enter a valid initial balance");
      return;
    }

    try {
      setCreating(true);

      const result = await createStrategyInstance({
        strategy_definition_id: parseInt(selectedDefinitionId),
        instance_name: instanceName || undefined,
        instance_description: instanceDescription || undefined,
        initial_balance: balance,
        tags: tags.length > 0 ? tags : undefined,
        risk_level: riskLevel,
      });

      toast.success("Strategy Instance Launched!", {
        description: `${result.instance_name} created with $${balance} initial balance`,
      });

      // Reset form
      setSelectedDefinitionId("");
      setInstanceName("");
      setInstanceDescription("");
      setInitialBalance("1000");
      setTags([]);
      setTagInput("");
      setRiskLevel("medium");

      // Close modal and notify parent
      onOpenChange(false);
      if (onSuccess) {
        onSuccess(result.portfolio_id);
      }
    } catch (err: any) {
      console.error("Failed to create strategy instance:", err);
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Failed to launch strategy instance";
      toast.error("Launch Failed", {
        description: errorMessage,
      });
    } finally {
      setCreating(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-800 text-white">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Rocket className="w-6 h-6 text-purple-400" />
            Launch Strategy Instance
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Create a new trading strategy instance from a template
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Strategy Template Selection */}
          <div className="space-y-2">
            <Label htmlFor="strategy-template" className="text-white">
              Strategy Template *
            </Label>
            {loadingDefinitions ? (
              <div className="flex items-center gap-2 text-slate-400 py-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading templates...
              </div>
            ) : definitions.length === 0 ? (
              <div className="text-sm text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-lg p-3">
                No strategy templates available. Please contact admin to add templates.
              </div>
            ) : (
              <Select
                value={selectedDefinitionId}
                onValueChange={setSelectedDefinitionId}
              >
                <SelectTrigger
                  id="strategy-template"
                  className="bg-slate-800 border-slate-700 text-white"
                >
                  <SelectValue placeholder="Select a strategy template" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {definitions.map((def) => (
                    <SelectItem
                      key={def.id}
                      value={def.id.toString()}
                      className="text-white hover:bg-slate-700"
                    >
                      <div>
                        <div className="font-medium">{def.display_name}</div>
                        <div className="text-xs text-slate-400">
                          {def.trade_symbol} • {def.trade_channel}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Show selected template details */}
            {selectedDefinition && (
              <div className="mt-2 p-3 bg-slate-800/50 rounded-lg border border-slate-700 text-sm">
                <div className="font-medium text-white mb-1">
                  {selectedDefinition.display_name}
                </div>
                {selectedDefinition.description && (
                  <p className="text-slate-400 text-xs mb-2">
                    {selectedDefinition.description}
                  </p>
                )}
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-2 py-1 bg-slate-700 text-slate-300 rounded">
                    Symbol: {selectedDefinition.trade_symbol}
                  </span>
                  <span className="px-2 py-1 bg-slate-700 text-slate-300 rounded">
                    Channel: {selectedDefinition.trade_channel}
                  </span>
                  <span className="px-2 py-1 bg-slate-700 text-slate-300 rounded">
                    Rebalance: {selectedDefinition.rebalance_period_minutes}min
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Instance Name */}
          <div className="space-y-2">
            <Label htmlFor="instance-name" className="text-white">
              Instance Name (Optional)
            </Label>
            <Input
              id="instance-name"
              value={instanceName}
              onChange={(e) => setInstanceName(e.target.value)}
              placeholder="e.g., My BTC Strategy v1"
              className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
            />
            <p className="text-xs text-slate-500">
              Leave empty to auto-generate based on template name
            </p>
          </div>

          {/* Instance Description */}
          <div className="space-y-2">
            <Label htmlFor="instance-description" className="text-white">
              Description (Optional)
            </Label>
            <Textarea
              id="instance-description"
              value={instanceDescription}
              onChange={(e) => setInstanceDescription(e.target.value)}
              placeholder="Describe your strategy goals or notes..."
              rows={3}
              className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 resize-none"
            />
          </div>

          {/* Initial Balance */}
          <div className="space-y-2">
            <Label htmlFor="initial-balance" className="text-white">
              Initial Balance (USDT) *
            </Label>
            <Input
              id="initial-balance"
              type="number"
              min="0"
              step="0.01"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
              placeholder="1000"
              className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
            />
            <p className="text-xs text-slate-500">
              Minimum recommended: $100 USDT
            </p>
          </div>

          {/* Strategy Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags" className="text-white">
              Strategy Tags (Optional)
            </Label>
            <div className="space-y-2">
              <div className="flex gap-2">
                <Input
                  id="tags"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && tagInput.trim()) {
                      e.preventDefault();
                      if (!tags.includes(tagInput.trim())) {
                        setTags([...tags, tagInput.trim()]);
                      }
                      setTagInput("");
                    }
                  }}
                  placeholder="e.g., Macro-Driven, Low-Medium Risk"
                  className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                />
                <Button
                  type="button"
                  onClick={() => {
                    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
                      setTags([...tags, tagInput.trim()]);
                      setTagInput("");
                    }
                  }}
                  variant="outline"
                  className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
                >
                  Add
                </Button>
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-purple-600/20 border border-purple-500/30 text-purple-300 rounded text-sm"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => setTags(tags.filter((_, i) => i !== index))}
                        className="hover:bg-purple-600/30 rounded-full p-0.5"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Press Enter or click Add to add tags (e.g., Macro-Driven, BTC/ETH, Low-Medium Risk)
            </p>
          </div>

          {/* Risk Level */}
          <div className="space-y-2">
            <Label htmlFor="risk-level" className="text-white">
              Risk Level
            </Label>
            <Select value={riskLevel} onValueChange={setRiskLevel}>
              <SelectTrigger
                id="risk-level"
                className="bg-slate-800 border-slate-700 text-white"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="low" className="text-white hover:bg-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Low Risk
                  </div>
                </SelectItem>
                <SelectItem value="medium" className="text-white hover:bg-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                    Medium Risk
                  </div>
                </SelectItem>
                <SelectItem value="high" className="text-white hover:bg-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500"></span>
                    High Risk
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-slate-500">
              Risk tolerance level for this strategy instance
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            onClick={() => onOpenChange(false)}
            variant="outline"
            className="bg-slate-800 border-slate-700 hover:bg-slate-700 text-white"
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleLaunch}
            disabled={creating || !selectedDefinitionId || definitions.length === 0}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Launching...
              </>
            ) : (
              <>
                <Rocket className="w-4 h-4 mr-2" />
                Launch Instance
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
