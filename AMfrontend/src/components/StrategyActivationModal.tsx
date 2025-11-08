import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Loader2, Rocket, DollarSign, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "./ui/alert";

interface StrategyActivationModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (amount: number) => Promise<void>;
  strategyName: string;
  isLoading?: boolean;
}

export function StrategyActivationModal({
  open,
  onClose,
  onConfirm,
  strategyName,
  isLoading = false,
}: StrategyActivationModalProps) {
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");

  const handleConfirm = async () => {
    const numAmount = parseFloat(amount);

    // Validation
    if (!amount || isNaN(numAmount)) {
      setError("Please enter a valid amount");
      return;
    }

    if (numAmount < 100) {
      setError("Minimum deposit is $100");
      return;
    }

    if (numAmount > 1000000) {
      setError("Maximum deposit is $1,000,000");
      return;
    }

    setError("");

    try {
      await onConfirm(numAmount);
      // Reset form on success
      setAmount("");
      setError("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to activate strategy");
    }
  };

  const handleAmountChange = (value: string) => {
    // Only allow numbers and decimal point
    if (value === "" || /^\d*\.?\d*$/.test(value)) {
      setAmount(value);
      setError("");
    }
  };

  const handleQuickAmount = (value: number) => {
    setAmount(value.toString());
    setError("");
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !isLoading && !open && onClose()}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-xl flex items-center justify-center">
              <Rocket className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <DialogTitle className="text-xl text-white">Deposit and Run</DialogTitle>
              <DialogDescription className="text-slate-400 text-sm">
                Activate {strategyName}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="amount" className="text-sm text-slate-300">
              Initial Deposit Amount (USDT)
            </Label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                id="amount"
                type="text"
                value={amount}
                onChange={(e) => handleAmountChange(e.target.value)}
                placeholder="Enter amount"
                className="pl-10 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                disabled={isLoading}
              />
            </div>
            <p className="text-xs text-slate-500">Minimum: $100 USDT</p>
          </div>

          {/* Quick Amount Buttons */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAmount(100)}
              disabled={isLoading}
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              $100
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAmount(500)}
              disabled={isLoading}
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              $500
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAmount(1000)}
              disabled={isLoading}
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              $1,000
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuickAmount(5000)}
              disabled={isLoading}
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              $5,000
            </Button>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="bg-red-500/10 border-red-500/50 text-red-400">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Info Box */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
            <p className="text-xs text-blue-300 leading-relaxed">
              <strong>Note:</strong> This is a simulated trading account. Your deposit will be used to execute trades in the simulation environment. No real funds will be transferred.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isLoading || !amount}
            className="flex-1 bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 text-white"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Activating...
              </>
            ) : (
              <>
                <Rocket className="w-4 h-4 mr-2" />
                Activate Strategy
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
