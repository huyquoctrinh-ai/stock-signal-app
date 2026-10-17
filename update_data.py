"""Tải giá bằng vnstock, tính điểm tín hiệu, ghi data/data.json cho trang web."""
import csv, json, os, time, datetime as dt
import pandas as pd
from vnstock import Vnstock

START, TODAY, PAUSE = "2024-06-01", dt.date.today().isoformat(), 3.2  # ~20 lệnh/phút (mức khách)

def fetch(sym, index=False):
    for src in ("VCI", "KBS"):  # nguồn đầu lỗi thì thử nguồn sau
        try:
            df = Vnstock().stock(symbol=sym, source=src).quote.history(start=START, end=TODAY, interval="1D")
            df = df.rename(columns={"time": "date"})
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            if not index and df["close"].max() < 1000:  # vnstock hay trả giá theo nghìn đồng
                df[["open", "high", "low", "close"]] *= 1000
            time.sleep(PAUSE)
            return df.sort_values("date").reset_index(drop=True)
        except Exception as e:
            print(sym, src, "lỗi:", e); time.sleep(PAUSE)
    return None

def ind(df):
    c = df.close
    for n in (20, 50, 200): df[f"ma{n}"] = c.rolling(n).mean()
    m = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    df["h"] = m - m.ewm(span=9, adjust=False).mean()
    lo, hi = df.low.rolling(14).min(), df.high.rolling(14).max()
    df["k"] = (c - lo) / (hi - lo) * 100; df["dk"] = df.k.rolling(3).mean()
    df["va"] = df.volume.rolling(20).mean()
    df["hh20"] = df.high.rolling(20).max().shift(1)
    return df

def score(df, i, mk, rs):
    r, p = df.iloc[i], df.iloc[i - 1]
    b = lambda x: 1 if x else 0
    liq = r.va * r.close >= 5e9  # giá trị giao dịch TB 20 phiên từ 5 tỷ đồng
    cross = p.k <= p.dk and r.k > r.dk and r.k < 80
    sw = (15*b(r.close > r.ma20) + 10*b(r.ma20 > r.ma50) + 15*b(r.h > 0) + 10*b(p.h <= 0 < r.h)
          + 10*b(cross) - 10*b(r.k > 90) + 15*b(r.volume > 1.2*r.va) + 15*b(r.close >= r.hh20) + 10*b(mk))
    lt = (20*b(r.close > r.ma50) + 20*b(r.ma50 > r.ma200) + 15*b(r.close >= 0.85*df.close.iloc[max(0, len(df)+i-249):len(df)+i+1].max())
          + 15*b(rs) + 10*b(r.ma200 > df.ma200.iloc[i-20]) + 10*b(liq) + 10*b(mk))
    flags = [mk, r.close > r.ma20 > r.ma50, r.h > 0 or cross, r.volume > 1.2*r.va, liq]
    return max(0, min(100, sw)), max(0, min(100, lt)), "".join(str(b(x)) for x in flags)

def pattern(r, p):
    if r.close >= r.hh20: return "Breakout"
    if r.close > r.ma50 and abs(r.close / r.ma20 - 1) < 0.02: return "Hồi về MA20"
    if r.close < r.ma50 and r.h > p.h and r.k > r.dk: return "Đảo chiều sớm"
    if r.close < r.ma50 < r.ma200: return "Xu hướng giảm"
    return "Đi ngang"

syms = {r["ma"].strip().upper(): r["nganh"].strip() for r in csv.DictReader(open("symbols.csv", encoding="utf-8"))}
wl = [l.strip().upper() for l in open("watchlist.txt", encoding="utf-8") if l.strip()]
for w in wl: syms.setdefault(w, "Chưa phân ngành")

MK, mk_ok, vr = {"t": "Chưa có dữ liệu", "c": "mu", "vn": ""}, False, None
vn = fetch("VNINDEX", True)
if vn is not None and len(vn) > 200:
    vn = ind(vn); r = vn.iloc[-1]; mk_ok = bool(r.close > r.ma50); vr = r.close / vn.close.iloc[-127] - 1
    t, c = ("Thuận lợi", "up") if mk_ok and r.ma50 > r.ma200 else ("Trung tính", "wa") if mk_ok else ("Rủi ro cao", "dn")
    num = f"{r.close:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    chg = f"{(r.close / vn.close.iloc[-2] - 1) * 100:+.2f}".replace(".", ",")
    MK = {"t": t, "c": c, "vn": f"VN-Index {num} ({chg}%)"}

out, asof = [], ""
for s, sec in syms.items():
    df = fetch(s)
    if df is None or len(df) < 60: print("bỏ qua", s); continue
    df = ind(df); r, p = df.iloc[-1], df.iloc[-2]
    rs = vr is not None and len(df) > 127 and (r.close / df.close.iloc[-127] - 1) > vr
    sw, lt, f = score(df, -1, mk_ok, rs); sw0, lt0, _ = score(df, -2, mk_ok, rs)
    w = []
    if r.va * r.close < 5e9: w.append("Thanh khoản thấp (dưới 5 tỷ đồng mỗi phiên).")
    if r.close < r.ma200: w.append("Giá dưới MA200, xu hướng dài hạn còn giảm. Dùng vị thế nhỏ.")
    out.append({"s": s, "n": s, "sec": sec, "sw": int(sw), "lt": int(lt), "pt": pattern(r, p), "f": f,
                "nw": bool((sw >= 55 > sw0) or (lt >= 55 > lt0)), "w": " ".join(w),
                "d": [[x.date, round(x.open), round(x.high), round(x.low), round(x.close), int(x.volume)] for x in df.tail(320).itertuples()]})
    asof = max(asof, df.date.iloc[-1])

os.makedirs("data", exist_ok=True)
json.dump({"asof": asof, "market": MK, "watchlist": wl, "stocks": out}, open("data/data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("Đã ghi", len(out), "mã, đến phiên", asof)
