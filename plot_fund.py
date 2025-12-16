"""
Rysuje wykresy dla wybranego funduszu:
- Notowania
- Stopy zwrotu dzienne z linią VaR 95% i średnią
- Maksymalne obsunięcie (drawdown)

Wejście: wyceny_csv/zlaczone_po_dacie.csv
Wyjścia PNG: wyceny_csv/{slug}_cena.png, {_}_zwroty_var.png, {_}_drawdown.png
"""

from pathlib import Path
import math
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "wyceny_csv" / "zlaczone_po_dacie.csv"
FUND_NAME = "PKO Obligacji Skarbowych Plus - fio"  # zmień na dowolną kolumnę
ANNUAL_FACTOR = 252


def to_float(val):
    if pd.isna(val):
        return None
    s = str(val).strip().replace(" ", "")
    if s == "":
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def load_series(name: str) -> pd.Series:
    df = pd.read_csv(DATA_PATH, sep=";", usecols=["Data", name], dtype=str)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])
    df[name] = df[name].map(to_float)
    s = df.set_index("Data")[name].dropna().sort_index()
    return s


def prepare_returns(prices: pd.Series) -> pd.Series:
    return prices.ffill().pct_change(fill_method=None).dropna()


def compute_drawdown(returns: pd.Series) -> pd.Series:
    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    return equity / peak - 1


def main():
    prices = load_series(FUND_NAME)
    if prices.empty:
        raise SystemExit(f"Brak danych dla kolumny: {FUND_NAME}")

    returns = prepare_returns(prices)
    drawdown = compute_drawdown(returns)
    var_95 = returns.quantile(0.05)

    # 1) Notowania
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(prices.index, prices.values, label="Notowania")
    ax.set_title(f"{FUND_NAME} - notowania")
    ax.set_xlabel("Data")
    ax.set_ylabel("Wartość")
    ax.grid(True, alpha=0.3)
    ax.legend()
    price_path = BASE_DIR / "wyceny_csv" / f"{FUND_NAME}_cena.png"
    fig.tight_layout()
    fig.savefig(price_path, dpi=160)
    plt.close(fig)

    # 2) Stopy zwrotu + VaR
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(returns.index, returns.values, label="Stopy zwrotu", color="steelblue", alpha=0.7)
    ax.axhline(var_95, color="red", linestyle="--", label=f"VaR 95%: {var_95:.4f}")
    ax.axhline(returns.mean(), color="green", linestyle=":", label=f"Średnia: {returns.mean():.4f}")
    ax.set_title(f"{FUND_NAME} - stopy zwrotu dzienne")
    ax.set_xlabel("Data")
    ax.set_ylabel("Zwrot dzienny")
    ax.grid(True, alpha=0.3)
    ax.legend()
    returns_path = BASE_DIR / "wyceny_csv" / f"{FUND_NAME}_zwroty_var.png"
    fig.tight_layout()
    fig.savefig(returns_path, dpi=160)
    plt.close(fig)

    # 3) Drawdown
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(drawdown.index, drawdown.values, color="darkorange", label="Drawdown")
    ax.set_title(f"{FUND_NAME} - maksymalne obsunięcia")
    ax.set_xlabel("Data")
    ax.set_ylabel("Obsunięcie")
    ax.grid(True, alpha=0.3)
    ax.legend()
    dd_path = BASE_DIR / "wyceny_csv" / f"{FUND_NAME}_drawdown.png"
    fig.tight_layout()
    fig.savefig(dd_path, dpi=160)
    plt.close(fig)

    print("Zapisano wykresy:")
    for p in (price_path, returns_path, dd_path):
        print(" -", p)


if __name__ == "__main__":
    main()
