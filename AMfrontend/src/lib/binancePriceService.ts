/**
 * Binance Real-time Price Service
 * 使用 Binance REST API 获取实时加密货币价格
 */

interface BinanceTickerResponse {
  symbol: string;
  price: string;
}

class BinancePriceService {
  private baseUrl = 'https://api.binance.com/api/v3';
  private priceCache: Map<string, { price: number; timestamp: number }> = new Map();
  private cacheDuration = 2000; // 缓存2秒，避免频繁请求

  /**
   * 获取单个交易对的当前价格
   * @param symbol - 交易对符号 (例如: 'BTC', 'ETH')
   * @returns 当前价格
   */
  async getPrice(symbol: string): Promise<number> {
    const normalizedSymbol = this.normalizeSymbol(symbol);

    // 检查缓存
    const cached = this.priceCache.get(normalizedSymbol);
    if (cached && Date.now() - cached.timestamp < this.cacheDuration) {
      return cached.price;
    }

    try {
      const response = await fetch(
        `${this.baseUrl}/ticker/price?symbol=${normalizedSymbol.toUpperCase()}`
      );

      if (!response.ok) {
        throw new Error(`Binance API error: ${response.status}`);
      }

      const data: BinanceTickerResponse = await response.json();
      const price = parseFloat(data.price);

      // 更新缓存
      this.priceCache.set(normalizedSymbol, {
        price,
        timestamp: Date.now(),
      });

      return price;
    } catch (error) {
      console.error(`[BinancePriceService] Error fetching price for ${symbol}:`, error);

      // 如果有缓存，返回缓存的价格（即使过期）
      if (cached) {
        console.warn(`[BinancePriceService] Using stale cache for ${symbol}`);
        return cached.price;
      }

      throw error;
    }
  }

  /**
   * 批量获取多个交易对的价格
   * @param symbols - 交易对符号数组
   * @returns 价格映射 { symbol: price }
   */
  async getPrices(symbols: string[]): Promise<Record<string, number>> {
    const normalizedSymbols = symbols.map(s => this.normalizeSymbol(s));

    try {
      // 使用 ticker/price 接口批量获取（不传 symbol 参数）
      const response = await fetch(`${this.baseUrl}/ticker/price`);

      if (!response.ok) {
        throw new Error(`Binance API error: ${response.status}`);
      }

      const data: BinanceTickerResponse[] = await response.json();

      // 创建价格映射
      const priceMap: Record<string, number> = {};

      data.forEach(ticker => {
        const normalizedSymbol = ticker.symbol.toLowerCase();
        if (normalizedSymbols.includes(normalizedSymbol)) {
          const price = parseFloat(ticker.price);
          priceMap[normalizedSymbol] = price;

          // 更新缓存
          this.priceCache.set(normalizedSymbol, {
            price,
            timestamp: Date.now(),
          });
        }
      });

      return priceMap;
    } catch (error) {
      console.error('[BinancePriceService] Error fetching prices:', error);
      throw error;
    }
  }

  /**
   * 标准化交易对符号
   * BTC -> btcusdt
   * ETH -> ethusdt
   */
  private normalizeSymbol(symbol: string): string {
    const clean = symbol.toUpperCase().replace(/[^A-Z]/g, '');

    // 如果已经包含 USDT，直接返回小写
    if (clean.endsWith('USDT')) {
      return clean.toLowerCase();
    }

    // 否则添加 USDT
    return `${clean}usdt`.toLowerCase();
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.priceCache.clear();
  }
}

// 导出单例
export const binancePriceService = new BinancePriceService();
