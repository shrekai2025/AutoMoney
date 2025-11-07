import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Wallet, ExternalLink, Copy, Check } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import { toast } from "sonner";

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: any[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
      isMetaMask?: boolean;
    };
  }
}

export function WalletConnect() {
  const [address, setAddress] = useState<string | null>(null);
  const [balance, setBalance] = useState<string>("0");
  const [isConnecting, setIsConnecting] = useState(false);
  const [copied, setCopied] = useState(false);

  // Check if wallet is already connected on mount
  useEffect(() => {
    checkIfWalletIsConnected();
  }, []);

  // Listen for account changes
  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected wallet
          setAddress(null);
          setBalance("0");
        } else {
          setAddress(accounts[0]);
          getBalance(accounts[0]);
        }
      };

      window.ethereum.on("accountsChanged", handleAccountsChanged);

      return () => {
        if (window.ethereum) {
          window.ethereum.removeListener("accountsChanged", handleAccountsChanged);
        }
      };
    }
  }, []);

  const checkIfWalletIsConnected = async () => {
    if (typeof window.ethereum !== "undefined") {
      try {
        const accounts = await window.ethereum.request({
          method: "eth_accounts",
        });
        if (accounts.length > 0) {
          setAddress(accounts[0]);
          getBalance(accounts[0]);
        }
      } catch (error) {
        console.error("Error checking wallet connection:", error);
      }
    }
  };

  const getBalance = async (address: string) => {
    try {
      const balanceHex = await window.ethereum?.request({
        method: "eth_getBalance",
        params: [address, "latest"],
      });
      // Convert from Wei to ETH
      const balanceEth = parseInt(balanceHex, 16) / 1e18;
      setBalance(balanceEth.toFixed(4));
    } catch (error) {
      console.error("Error fetching balance:", error);
    }
  };

  const connectWallet = async () => {
    if (typeof window.ethereum === "undefined") {
      toast.error("MetaMask not detected", {
        description: "Please install MetaMask to connect your wallet.",
      });
      window.open("https://metamask.io/download/", "_blank");
      return;
    }

    setIsConnecting(true);
    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });
      setAddress(accounts[0]);
      getBalance(accounts[0]);
      toast.success("Wallet Connected", {
        description: `Connected to ${shortenAddress(accounts[0])}`,
      });
    } catch (error: any) {
      console.error("Error connecting wallet:", error);
      if (error.code === 4001) {
        toast.error("Connection Rejected", {
          description: "You rejected the connection request.",
        });
      } else {
        toast.error("Connection Failed", {
          description: "Failed to connect to MetaMask.",
        });
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setAddress(null);
    setBalance("0");
    toast.success("Wallet Disconnected");
  };

  const shortenAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address);
      setCopied(true);
      toast.success("Address Copied");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const openInEtherscan = () => {
    if (address) {
      window.open(`https://etherscan.io/address/${address}`, "_blank");
    }
  };

  if (!address) {
    return (
      <Button
        onClick={connectWallet}
        disabled={isConnecting}
        className="h-7 px-3 text-xs bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 shadow-lg shadow-blue-500/30"
      >
        <Wallet className="w-3.5 h-3.5 mr-1.5" />
        {isConnecting ? "Connecting..." : "Connect Wallet"}
      </Button>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="h-7 px-2 text-xs bg-slate-800/50 border-slate-700 text-white hover:bg-slate-700 hover:border-slate-600"
        >
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            <span className="hidden sm:inline font-mono">{shortenAddress(address)}</span>
            <Wallet className="w-3.5 h-3.5 sm:hidden" />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 bg-slate-900 border-slate-700" align="end">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-white">Wallet Connected</span>
            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-2 py-0">
              Active
            </Badge>
          </div>

          {/* Balance */}
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
            <div className="text-xs text-slate-400 mb-1">Balance</div>
            <div className="text-xl text-white font-mono">{balance} ETH</div>
          </div>

          {/* Address */}
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
            <div className="text-xs text-slate-400 mb-2">Address</div>
            <div className="flex items-center gap-2">
              <code className="text-xs text-slate-300 font-mono flex-1 truncate">
                {address}
              </code>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2">
            <Button
              onClick={copyAddress}
              variant="outline"
              className="w-full h-8 text-xs bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 mr-1.5" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 mr-1.5" />
                  Copy Address
                </>
              )}
            </Button>
            <Button
              onClick={openInEtherscan}
              variant="outline"
              className="w-full h-8 text-xs bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white"
            >
              <ExternalLink className="w-3 h-3 mr-1.5" />
              View on Etherscan
            </Button>
            <Button
              onClick={disconnectWallet}
              variant="outline"
              className="w-full h-8 text-xs bg-red-900/20 border-red-500/50 text-red-400 hover:bg-red-900/30 hover:text-red-300"
            >
              Disconnect Wallet
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
