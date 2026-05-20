"""Universo de tickers US líquidos cubiertos por la app."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TickerInfo:
    symbol: str
    name: str
    category: str   # 'index', 'tech', 'financials', 'consumer', 'energy', 'commodity'


UNIVERSE: list[TickerInfo] = [
    # Índices y ETFs líquidos (más liquid options del mercado)
    TickerInfo("SPY", "SPDR S&P 500", "index"),
    TickerInfo("QQQ", "Invesco Nasdaq 100", "index"),
    TickerInfo("IWM", "iShares Russell 2000", "index"),
    TickerInfo("DIA", "SPDR Dow Jones", "index"),
    # Mega cap tech
    TickerInfo("AAPL", "Apple", "tech"),
    TickerInfo("MSFT", "Microsoft", "tech"),
    TickerInfo("NVDA", "NVIDIA", "tech"),
    TickerInfo("GOOGL", "Alphabet", "tech"),
    TickerInfo("AMZN", "Amazon", "tech"),
    TickerInfo("META", "Meta Platforms", "tech"),
    TickerInfo("TSLA", "Tesla", "tech"),
    TickerInfo("AMD", "AMD", "tech"),
    TickerInfo("NFLX", "Netflix", "tech"),
    # Financials
    TickerInfo("JPM", "JPMorgan", "financials"),
    TickerInfo("BAC", "Bank of America", "financials"),
    TickerInfo("GS", "Goldman Sachs", "financials"),
    TickerInfo("BRK-B", "Berkshire Hathaway B", "financials"),
    # Consumer
    TickerInfo("WMT", "Walmart", "consumer"),
    TickerInfo("DIS", "Disney", "consumer"),
    TickerInfo("KO", "Coca-Cola", "consumer"),
    # Energy
    TickerInfo("XOM", "Exxon Mobil", "energy"),
    TickerInfo("CVX", "Chevron", "energy"),
    # Commodity ETFs
    TickerInfo("GLD", "SPDR Gold", "commodity"),
    TickerInfo("SLV", "iShares Silver", "commodity"),
    TickerInfo("USO", "United States Oil", "commodity"),
]

HEADER_STRIP_TICKERS = ["SPY", "QQQ", "IWM", "^VIX", "^TNX", "GLD", "BTC-USD"]


def find_ticker(symbol: str) -> TickerInfo | None:
    for t in UNIVERSE:
        if t.symbol == symbol.upper():
            return t
    return None
