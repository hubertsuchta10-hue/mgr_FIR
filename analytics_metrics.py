"""
Oblicza dzienne stopy zwrotu i metryki ryzyka/zwrotu dla ostatnich 5 lat i ostatniego roku.
- Wejście: wyceny_csv/zlaczone_po_dacie.csv (separator ';', przecinek jako separator dziesiętny)
- Wyjście: wyceny_csv/analiza_wyceny.xlsx z arkuszami: zwroty_5l, metryki_5l, metryki_1l
"""

from pathlib import Path
import math
import pandas as pd

# Parametry
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "wyceny_csv" / "zlaczone_po_dacie.csv"
OUT_XLSX = BASE_DIR / "wyceny_csv" / "analiza_wyceny.xlsx"
RISK_FREE_ANNUAL = 0.045  # roczna stopa wolna od ryzyka
ANNUAL_FACTOR = 252  # liczba sesji do annualizacji


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


def load_prices():
    df = pd.read_csv(DATA_PATH, sep=";", dtype=str)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])
    df = df.set_index("Data")
    # konwersja kolumn na float
    for col in df.columns:
        df[col] = df[col].map(to_float)
    df = df.sort_index()
    return df


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.ffill().pct_change(fill_method=None)


def compute_series_metrics(series: pd.Series) -> dict | None:
    r = series.dropna()
    if len(r) < 2:
        return None

    mean_r = r.mean()
    std_r = r.std()
    excess = r - RISK_FREE_ANNUAL / ANNUAL_FACTOR
    excess_mean = excess.mean()

    sharpe = None
    if std_r and not math.isnan(std_r) and std_r != 0:
        sharpe = excess_mean / std_r * math.sqrt(ANNUAL_FACTOR)

    downside = excess[excess < 0]
    sortino = None
    downside_std = downside.std()
    if downside_std and not math.isnan(downside_std) and downside_std != 0:
        sortino = excess_mean / downside_std * math.sqrt(ANNUAL_FACTOR)

    vol = std_r * math.sqrt(ANNUAL_FACTOR) if std_r == std_r else None

    cum_return = (1 + r).prod() - 1
    days_span = (r.index.max() - r.index.min()).days
    annual_return = None
    if days_span > 0:
        years = days_span / 365.25
        annual_return = (1 + cum_return) ** (1 / years) - 1

    equity = (1 + r).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1
    max_dd = drawdown.min()

    var_95 = r.quantile(0.05)
    es_95 = r[r <= var_95].mean()

    return {
        "liczba_obserwacji": len(r),
        "srednia_dzienna": mean_r,
        "odch_std_dziennie": std_r,
        "odch_std_roczne": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "var_95": var_95,
        "es_95": es_95,
        "calkowity_zwrot": cum_return,
        "srednioroczna_stopazwrotu": annual_return,
    }


def metrics_for_period(returns: pd.DataFrame, start_date: pd.Timestamp) -> pd.DataFrame:
    window = returns.loc[returns.index >= start_date]
    rows = []
    for col in window.columns:
        metrics = compute_series_metrics(window[col])
        if metrics:
            metrics["nazwa"] = col
            rows.append(metrics)
    return pd.DataFrame(rows).set_index("nazwa").sort_index()


def main():
    prices = load_prices()
    rets = daily_returns(prices)

    max_date = rets.index.max()
    start_5y = max_date - pd.DateOffset(years=5)
    start_1y = max_date - pd.DateOffset(years=1)

    rets_5y = rets.loc[rets.index >= start_5y]
    metrics_5y = metrics_for_period(rets, start_5y)
    metrics_1y = metrics_for_period(rets, start_1y)

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        rets_5y.to_excel(writer, sheet_name="zwroty_5l")
        metrics_5y.to_excel(writer, sheet_name="metryki_5l")
        metrics_1y.to_excel(writer, sheet_name="metryki_1l")

    print(
        f"Zapisano: {OUT_XLSX} (zwroty_5l: {len(rets_5y)} wierszy, metryki kolumn: {len(metrics_5y)})"
    )


if __name__ == "__main__":
    main()
