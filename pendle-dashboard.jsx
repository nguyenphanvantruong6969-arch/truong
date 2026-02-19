import { useState, useEffect } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from "recharts";

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────
const fmt = (n, d = 2) =>
  n == null ? "—" : n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtUSD = (n) => (n == null ? "—" : `$${fmt(n)}`);
const fmtPct = (n) =>
  n == null ? "—" : `${n >= 0 ? "+" : ""}${fmt(n)}%`;

const todayStr = () => new Date().toISOString().split("T")[0];
const daysBetween = (a, b) => Math.max(0, (new Date(b) - new Date(a)) / 86400000);

// APR = (profit / invested) / days * 365  [returns %]
const calcAPR = (profit, invested, days) => {
  if (!invested || !days) return 0;
  return (profit / invested / days) * 365 * 100;
};

// ROE accrued so far on a regular position
const calcPositionROE = (pos) => {
  const now = new Date();
  const buy = new Date(pos.buyDate);
  const mat = new Date(pos.maturityDate);
  const totalDays = daysBetween(pos.buyDate, pos.maturityDate);
  if (totalDays <= 0)
    return { earned: 0, earnedPct: 0, progress: 100, daysLeft: 0, totalDays: 0, totalExpectedPct: 0, elapsed: 0, apr: 0, totalExpectedEarned: 0 };
  const elapsed = Math.min((now - buy) / 86400000, totalDays);
  const daysLeft = Math.max(0, (mat - now) / 86400000);
  const progress = Math.min(100, (elapsed / totalDays) * 100);
  const totalExpectedPct = (pos.yieldRate / 100) * (totalDays / 365) * 100;
  const totalExpectedEarned = (pos.amount * totalExpectedPct) / 100;
  const earnedPct = totalExpectedPct * (elapsed / totalDays);
  const earned = (pos.amount * earnedPct) / 100;
  const apr = calcAPR(totalExpectedEarned, pos.amount, totalDays);
  return { earned, earnedPct, progress, daysLeft, totalDays, totalExpectedPct, elapsed, apr, totalExpectedEarned };
};

// Carry Trade calc
const calcCarry = (ct) => {
  const totalDays = daysBetween(ct.buyDate, ct.maturityDate);
  if (totalDays <= 0)
    return { spread: 0, netEarned: 0, netEarnedPct: 0, borrowCost: 0, lendIncome: 0, progress: 0, daysLeft: 0, elapsed: 0, apr: 0, totalNetEarned: 0, totalDays: 0 };
  const now = new Date();
  const buy = new Date(ct.buyDate);
  const mat = new Date(ct.maturityDate);
  const elapsed = Math.min((now - buy) / 86400000, totalDays);
  const daysLeft = Math.max(0, (mat - now) / 86400000);
  const progress = Math.min(100, (elapsed / totalDays) * 100);
  const spread = ct.lendRate - ct.borrowRate;
  const lendIncome = ct.amount * (ct.lendRate / 100) * (totalDays / 365);
  const borrowCost = ct.amount * (ct.borrowRate / 100) * (totalDays / 365);
  const totalNetEarned = lendIncome - borrowCost;
  const netEarned = totalNetEarned * (elapsed / totalDays);
  const netEarnedPct = ct.amount > 0 ? (netEarned / ct.amount) * 100 : 0;
  const apr = calcAPR(totalNetEarned, ct.amount, totalDays);
  return { spread, netEarned, netEarnedPct, borrowCost, lendIncome, progress, daysLeft, elapsed, apr, totalNetEarned, totalDays };
};

// Dashboard portfolio: only regular positions (NOT carry)
const calcPortfolio = (positions) => {
  if (!positions.length) return { totalInvested: 0, totalEarned: 0, portfolioPct: 0, activeCount: 0 };
  const active = positions.filter((p) => new Date(p.maturityDate) > new Date());
  const totalInvested = positions.reduce((s, p) => s + p.amount, 0);
  const totalEarned = positions.reduce((s, p) => s + calcPositionROE(p).earned, 0);
  const portfolioPct = totalInvested > 0 ? (totalEarned / totalInvested) * 100 : 0;
  return { totalInvested, totalEarned, portfolioPct, activeCount: active.length };
};

const positionStatus = (maturityDate) => {
  const d = daysBetween(todayStr(), maturityDate);
  if (new Date(maturityDate) <= new Date()) return "matured";
  if (d <= 7) return "warning";
  return "active";
};
const STATUS_COLOR = { active: "#00ffc8", matured: "#444", warning: "#ffaa00" };
const PIE_COLORS = ["#00ffc8", "#00b8ff", "#a78bfa", "#ffaa00", "#34d399", "#38bdf8", "#f472b6"];
const CT_PIE_COLORS = ["#ff6b9d", "#f87171", "#fb923c", "#fbbf24"];

// ─────────────────────────────────────────────────────────────────────────────
// STORAGE
// ─────────────────────────────────────────────────────────────────────────────
const KEYS = { positions: "pendle:v2:pos", carries: "pendle:v2:ct", snapshots: "pendle:v2:snaps" };
const loadData = async (key) => {
  try { const r = await window.storage.get(key); return r ? JSON.parse(r.value) : null; } catch { return null; }
};
const saveData = async (key, data) => {
  try { await window.storage.set(key, JSON.stringify(data)); } catch {}
};

// ─────────────────────────────────────────────────────────────────────────────
// BLANK FORMS
// ─────────────────────────────────────────────────────────────────────────────
const blankPos = () => ({ asset: "", buyDate: todayStr(), maturityDate: "", amount: "", yieldRate: "", note: "" });
const blankCT = () => ({ asset: "", buyDate: todayStr(), maturityDate: "", amount: "", borrowRate: "", lendRate: "", note: "" });

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function PendleDashboard() {
  const [positions, setPositions] = useState([]);
  const [carries, setCarries] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [tab, setTab] = useState("dashboard");

  const [showPosForm, setShowPosForm] = useState(false);
  const [showCTForm, setShowCTForm] = useState(false);
  const [editPosId, setEditPosId] = useState(null);
  const [editCTId, setEditCTId] = useState(null);
  const [posForm, setPosForm] = useState(blankPos());
  const [ctForm, setCtForm] = useState(blankCT());

  // calculator state
  const [calcState, setCalcState] = useState({ invested: "", profit: "", startDate: todayStr(), endDate: "", result: null });
  const [ctCalc, setCtCalc] = useState({ amount: "", borrowRate: "", lendRate: "", startDate: todayStr(), endDate: "", result: null });

  // ── Load
  useEffect(() => {
    (async () => {
      const pos = await loadData(KEYS.positions);
      const cts = await loadData(KEYS.carries);
      const snaps = await loadData(KEYS.snapshots);
      if (pos) setPositions(pos);
      if (cts) setCarries(cts);
      if (snaps) setSnapshots(snaps);
      setLoaded(true);
    })();
  }, []);
  useEffect(() => { if (loaded) saveData(KEYS.positions, positions); }, [positions, loaded]);
  useEffect(() => { if (loaded) saveData(KEYS.carries, carries); }, [carries, loaded]);

  // ── Daily snapshot (regular positions only)
  useEffect(() => {
    if (!loaded || !positions.length) return;
    const ts = todayStr();
    if (snapshots.some((s) => s.date === ts)) return;
    const { totalInvested, totalEarned, portfolioPct } = calcPortfolio(positions);
    const ns = [...snapshots, { date: ts, totalInvested, totalEarned, portfolioPct, count: positions.length }].slice(-90);
    setSnapshots(ns);
    saveData(KEYS.snapshots, ns);
  }, [loaded, positions]);

  const portfolio = calcPortfolio(positions);

  const compare = (daysAgo) => {
    if (!snapshots.length) return null;
    const d = new Date(); d.setDate(d.getDate() - daysAgo);
    const snap = [...snapshots].sort((a, b) => Math.abs(new Date(a.date) - d) - Math.abs(new Date(b.date) - d))[0];
    if (!snap) return null;
    return { investedDiff: portfolio.totalInvested - snap.totalInvested, earnedDiff: portfolio.totalEarned - snap.totalEarned, pctDiff: portfolio.portfolioPct - snap.portfolioPct, snap };
  };
  const comp1d = compare(1), comp1w = compare(7), comp1m = compare(30);

  // ── Position CRUD
  const submitPos = () => {
    if (!posForm.asset || !posForm.buyDate || !posForm.maturityDate || !posForm.amount || !posForm.yieldRate) return;
    const p = { ...posForm, id: editPosId || String(Date.now()), amount: +posForm.amount, yieldRate: +posForm.yieldRate };
    setPositions((prev) => editPosId ? prev.map((x) => x.id === editPosId ? p : x) : [...prev, p]);
    setEditPosId(null); setPosForm(blankPos()); setShowPosForm(false);
  };
  const editPos = (p) => { setPosForm({ ...p, amount: String(p.amount), yieldRate: String(p.yieldRate) }); setEditPosId(p.id); setShowPosForm(true); };
  const deletePos = (id) => setPositions((prev) => prev.filter((p) => p.id !== id));

  // ── Carry CRUD
  const submitCT = () => {
    if (!ctForm.asset || !ctForm.buyDate || !ctForm.maturityDate || !ctForm.amount || !ctForm.borrowRate || !ctForm.lendRate) return;
    const ct = { ...ctForm, id: editCTId || String(Date.now()), amount: +ctForm.amount, borrowRate: +ctForm.borrowRate, lendRate: +ctForm.lendRate };
    setCarries((prev) => editCTId ? prev.map((x) => x.id === editCTId ? ct : x) : [...prev, ct]);
    setEditCTId(null); setCtForm(blankCT()); setShowCTForm(false);
  };
  const editCT = (ct) => { setCtForm({ ...ct, amount: String(ct.amount), borrowRate: String(ct.borrowRate), lendRate: String(ct.lendRate) }); setEditCTId(ct.id); setShowCTForm(true); };
  const deleteCT = (id) => setCarries((prev) => prev.filter((c) => c.id !== id));

  // ── APR / ROE Calculator
  const runCalc = () => {
    const inv = +calcState.invested, profit = +calcState.profit;
    const days = daysBetween(calcState.startDate, calcState.endDate);
    if (!inv || !profit || !days) return;
    setCalcState((c) => ({ ...c, result: { roe: (profit / inv) * 100, apr: calcAPR(profit, inv, days), days, daily: profit / days } }));
  };

  // ── Carry Calculator
  const runCtCalc = () => {
    const amt = +ctCalc.amount, br = +ctCalc.borrowRate, lr = +ctCalc.lendRate;
    const days = daysBetween(ctCalc.startDate, ctCalc.endDate);
    if (!amt || !br || !lr || !days) return;
    const spread = lr - br;
    const lendIncome = amt * (lr / 100) * (days / 365);
    const borrowCost = amt * (br / 100) * (days / 365);
    const netProfit = lendIncome - borrowCost;
    setCtCalc((c) => ({ ...c, result: { spread, lendIncome, borrowCost, netProfit, netRoe: (netProfit / amt) * 100, apr: calcAPR(netProfit, amt, days), days } }));
  };

  // Chart data
  const chartData = snapshots.slice(-30).map((s) => ({ date: s.date.slice(5), earned: +s.totalEarned.toFixed(2) }));
  const pieAll = [
    ...positions.map((p) => ({ name: p.asset, value: p.amount, kind: "regular" })),
    ...carries.map((c) => ({ name: `[CT] ${c.asset}`, value: c.amount, kind: "carry" })),
  ];
  const pieRegular = positions.map((p) => ({ name: p.asset, value: p.amount }));

  const maturingSoon = [
    ...positions.map((p) => ({ ...p, _kind: "regular" })),
    ...carries.map((c) => ({ ...c, _kind: "carry" })),
  ].filter((p) => { const d = daysBetween(todayStr(), p.maturityDate); return d >= 0 && d <= 14; })
   .sort((a, b) => new Date(a.maturityDate) - new Date(b.maturityDate));

  // ────────────────────────────────────────────────────────────────
  return (
    <div style={S.root}>
      <div style={S.gridBg} />

      {/* HEADER */}
      <header style={S.header}>
        <div style={S.logoWrap}>
          <span style={S.logoIcon}>◈</span>
          <div>
            <div style={S.logoTitle}>PENDLE VAULT</div>
            <div style={S.logoSub}>Fixed Yield · Carry Trade · Portfolio Manager</div>
          </div>
        </div>
        <div style={S.headerRight}>
          <span style={S.liveTag}>● LIVE</span>
          <span style={S.dateTag}>{new Date().toLocaleDateString("vi-VN", { weekday: "short", year: "numeric", month: "short", day: "numeric" })}</span>
        </div>
      </header>

      {/* NAV */}
      <nav style={S.nav}>
        {[["dashboard","⬡ Dashboard"],["positions","⊞ Positions"],["carry","⇄ Carry Trade"],["analytics","◈ Analytics"],["calculator","⌗ Calculator"]].map(([t, lbl]) => (
          <button key={t} onClick={() => setTab(t)} style={{ ...S.navBtn, ...(tab === t ? S.navBtnActive : {}) }}>{lbl}</button>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button onClick={() => { setShowPosForm(true); setEditPosId(null); setPosForm(blankPos()); }} style={S.addBtn}>+ Kèo Gốc</button>
          <button onClick={() => { setShowCTForm(true); setEditCTId(null); setCtForm(blankCT()); }} style={{ ...S.addBtn, background: "#ff6b9d", boxShadow: "0 0 18px #ff6b9d35" }}>⇄ Carry Trade</button>
        </div>
      </nav>

      {/* ═══════════════ DASHBOARD ═══════════════ */}
      {tab === "dashboard" && (
        <div style={S.content}>
          <div style={S.sectionLabel}>⬡ Portfolio — Kèo Gốc (Carry Trade không tính vào đây)</div>
          <div style={S.kpiGrid}>
            <KPICard label="Total Invested" value={fmtUSD(portfolio.totalInvested)} sub={`${portfolio.activeCount} active positions`} accent="#00ffc8" icon="◈" />
            <KPICard label="ROE Accrued" value={fmtUSD(portfolio.totalEarned)} sub={fmtPct(portfolio.portfolioPct) + " of portfolio"} accent="#00b8ff" icon="↗" />
            <KPICard label="Avg APY" value={positions.length ? fmtPct(positions.reduce((s,p)=>s+p.yieldRate,0)/positions.length) : "—"} sub="avg annualised yield" accent="#a78bfa" icon="%" />
            <KPICard label="Portfolio Value" value={fmtUSD(portfolio.totalInvested + portfolio.totalEarned)} sub="principal + yield" accent="#ffaa00" icon="$" />
          </div>

          {carries.length > 0 && (() => {
            const totalCT = carries.reduce((s,c)=>s+c.amount,0);
            const totalCTEarned = carries.reduce((s,c)=>s+calcCarry(c).netEarned,0);
            const avgSpread = carries.reduce((s,c)=>s+(c.lendRate-c.borrowRate),0)/carries.length;
            return (
              <div style={S.ctSummaryBox}>
                <div style={S.ctSummaryTitle}>⇄ Carry Trade — Informational Only <span style={{ opacity: .4, fontWeight: 400, fontSize: 10 }}>(không tính vào portfolio trên)</span></div>
                <div style={S.ctSummaryGrid}>
                  <div><div style={S.ctStat}>Borrowed/Lent</div><div style={{ ...S.ctStatVal, color: "#ffb3d0" }}>{fmtUSD(totalCT)}</div></div>
                  <div><div style={S.ctStat}>Net Accrued</div><div style={{ ...S.ctStatVal, color: "#00ffc8" }}>+{fmtUSD(totalCTEarned)}</div></div>
                  <div><div style={S.ctStat}>Avg Spread</div><div style={{ ...S.ctStatVal, color: "#ffaa00" }}>{fmt(avgSpread)}% APY</div></div>
                  <div><div style={S.ctStat}>Active</div><div style={S.ctStatVal}>{carries.filter(c=>new Date(c.maturityDate)>new Date()).length} trades</div></div>
                </div>
              </div>
            );
          })()}

          <div style={S.sectionLabel}>◈ Performance vs. History</div>
          <div style={S.compGrid}>
            {[["vs Yesterday", comp1d],["vs 1 Week", comp1w],["vs 1 Month", comp1m]].map(([lbl,data]) => (
              <CompCard key={lbl} label={lbl} data={data} />
            ))}
          </div>

          {chartData.length > 1 && (
            <div style={S.chartBox}>
              <div style={S.chartTitle}>ROE Growth — Last 30 Days</div>
              <ResponsiveContainer width="100%" height={185}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="eg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00ffc8" stopOpacity={0.22}/>
                      <stop offset="95%" stopColor="#00ffc8" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#0f2040"/>
                  <XAxis dataKey="date" tick={{ fill:"#3a6a8a", fontSize:10 }}/>
                  <YAxis tick={{ fill:"#3a6a8a", fontSize:10 }} tickFormatter={v=>`$${v}`}/>
                  <Tooltip contentStyle={S.tooltip} formatter={v=>[`$${fmt(v)}`,"ROE"]}/>
                  <Area type="monotone" dataKey="earned" stroke="#00ffc8" strokeWidth={2} fill="url(#eg)"/>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {maturingSoon.length > 0 && (
            <>
              <div style={S.sectionLabel}>⚠ Maturing ≤ 14 Days</div>
              <div style={S.alertBox}>
                {maturingSoon.map((p) => {
                  const d = Math.ceil(daysBetween(todayStr(), p.maturityDate));
                  const isCarry = p._kind === "carry";
                  const earned = isCarry ? calcCarry(p).netEarned : calcPositionROE(p).earned;
                  return (
                    <div key={p.id} style={S.alertRow}>
                      <span style={{ fontSize:9, border:"1px solid", padding:"1px 5px", borderRadius:3, color: isCarry?"#ff6b9d":"#00ffc8", borderColor: isCarry?"#ff6b9d":"#00ffc8" }}>{isCarry?"CARRY":"GỐCⓂ"}</span>
                      <span style={{ color: d<=3?"#ff4444":"#ffaa00", fontFamily:"monospace", fontSize:12 }}>{d<=0?"MATURED":`${d}d`}</span>
                      <span style={{ color:"#cce", flex:1 }}>{p.asset}</span>
                      <span style={{ color:"#7a9ab8", fontFamily:"monospace" }}>{fmtUSD(p.amount)}</span>
                      <span style={{ color:"#00ffc8", fontFamily:"monospace" }}>+{fmtUSD(earned)}</span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* ═══════════════ POSITIONS ═══════════════ */}
      {tab === "positions" && (
        <div style={S.content}>
          <div style={S.sectionLabel}>⬡ Kèo Gốc — Regular Positions</div>
          {positions.length === 0
            ? <div style={S.empty}>Chưa có kèo nào. Nhấn <b style={{color:"#00ffc8"}}>+ Kèo Gốc</b> để thêm.</div>
            : <div style={S.tableWrap}>
                <table style={S.table}>
                  <thead><tr>{["Asset","Buy","Maturity","Days Left","Amount","APY","ROE $","ROE %","APR","Progress","Status",""].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
                  <tbody>
                    {positions.map(p => {
                      const r = calcPositionROE(p);
                      const st = positionStatus(p.maturityDate);
                      const col = STATUS_COLOR[st];
                      return (
                        <tr key={p.id} style={S.tr}>
                          <td style={{...S.td, color:"#e0f0ff", fontWeight:600}}>{p.asset}</td>
                          <td style={S.tdM}>{p.buyDate}</td>
                          <td style={S.tdM}>{p.maturityDate}</td>
                          <td style={{...S.tdM, color:col}}>{r.daysLeft<=0?"Matured":`${Math.ceil(r.daysLeft)}d`}</td>
                          <td style={{...S.tdM, color:"#fff"}}>{fmtUSD(p.amount)}</td>
                          <td style={{...S.tdM, color:"#a78bfa"}}>{fmtPct(p.yieldRate)}</td>
                          <td style={{...S.tdM, color:"#00ffc8"}}>+{fmtUSD(r.earned)}</td>
                          <td style={{...S.tdM, color:"#00ffc8"}}>{fmtPct(r.earnedPct)}</td>
                          <td style={{...S.tdM, color:"#00b8ff", fontWeight:700}}>{fmtPct(r.apr)}</td>
                          <td style={{...S.td, minWidth:90}}>
                            <div style={S.progBar}><div style={{...S.progFill, width:`${r.progress}%`, background:col}}/></div>
                            <div style={{fontSize:9, color:"#3a6a8a", marginTop:2}}>{fmt(r.progress,1)}%</div>
                          </td>
                          <td style={S.td}><span style={{...S.badge, borderColor:col, color:col}}>{st.toUpperCase()}</span></td>
                          <td style={S.td}>
                            <button onClick={()=>editPos(p)} style={S.iconBtn}>✎</button>
                            <button onClick={()=>deletePos(p.id)} style={{...S.iconBtn, color:"#ff4444"}}>✕</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>}

          <div style={{...S.sectionLabel, marginTop:32, color:"#ff6b9d"}}>⇄ Carry Trade Positions</div>
          {carries.length === 0
            ? <div style={S.empty}>Chưa có carry trade.</div>
            : <div style={S.tableWrap}>
                <table style={S.table}>
                  <thead><tr>{["Asset","Buy","Maturity","Days Left","Amount","Borrow","Lend","Spread","Net $","Net %","APR","Progress","Status",""].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
                  <tbody>
                    {carries.map(ct => {
                      const c = calcCarry(ct);
                      const st = positionStatus(ct.maturityDate);
                      const col = st==="active"?"#ff6b9d":st==="warning"?"#ffaa00":"#444";
                      return (
                        <tr key={ct.id} style={{...S.tr, background:"#120610"}}>
                          <td style={{...S.td, color:"#ffb3d0", fontWeight:600}}>
                            <span style={{fontSize:8, border:"1px solid #ff6b9d50", color:"#ff6b9d", padding:"1px 4px", borderRadius:2, marginRight:6}}>CT</span>
                            {ct.asset}
                          </td>
                          <td style={S.tdM}>{ct.buyDate}</td>
                          <td style={S.tdM}>{ct.maturityDate}</td>
                          <td style={{...S.tdM, color:col}}>{c.daysLeft<=0?"Matured":`${Math.ceil(c.daysLeft)}d`}</td>
                          <td style={{...S.tdM, color:"#fff"}}>{fmtUSD(ct.amount)}</td>
                          <td style={{...S.tdM, color:"#ff6b9d"}}>-{fmt(ct.borrowRate)}%</td>
                          <td style={{...S.tdM, color:"#00ffc8"}}>+{fmt(ct.lendRate)}%</td>
                          <td style={{...S.tdM, color:c.spread>0?"#00ffc8":"#ff4444", fontWeight:700}}>{c.spread>0?"+":""}{fmt(c.spread)}%</td>
                          <td style={{...S.tdM, color:"#00ffc8"}}>+{fmtUSD(c.netEarned)}</td>
                          <td style={{...S.tdM, color:"#00ffc8"}}>{fmtPct(c.netEarnedPct)}</td>
                          <td style={{...S.tdM, color:"#00b8ff", fontWeight:700}}>{fmtPct(c.apr)}</td>
                          <td style={{...S.td, minWidth:90}}>
                            <div style={S.progBar}><div style={{...S.progFill, width:`${c.progress}%`, background:col}}/></div>
                            <div style={{fontSize:9, color:"#3a6a8a", marginTop:2}}>{fmt(c.progress,1)}%</div>
                          </td>
                          <td style={S.td}><span style={{...S.badge, borderColor:col, color:col}}>{st.toUpperCase()}</span></td>
                          <td style={S.td}>
                            <button onClick={()=>editCT(ct)} style={S.iconBtn}>✎</button>
                            <button onClick={()=>deleteCT(ct.id)} style={{...S.iconBtn, color:"#ff4444"}}>✕</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>}
        </div>
      )}

      {/* ═══════════════ CARRY TRADE TAB ═══════════════ */}
      {tab === "carry" && (
        <div style={S.content}>
          <div style={S.ctInfoBox}>
            <div style={{color:"#ff6b9d", fontWeight:700, fontSize:15, marginBottom:10}}>⇄ Chiến lược Carry Trade trên Pendle</div>
            <div style={{color:"#9a7a8a", fontSize:13, lineHeight:1.9}}>
              Bạn <span style={{color:"#ff6b9d", fontWeight:600}}>vay ($) với lãi suất thấp</span> (Borrow Rate) và <span style={{color:"#00ffc8", fontWeight:600}}>deposit/lend với lãi suất cao hơn</span> (Lend Rate).<br/>
              <b style={{color:"#e0d0f0"}}>Net Spread = Lend Rate − Borrow Rate</b> → lợi nhuận ròng mỗi năm.<br/>
              Khoản này <b style={{color:"#ffaa00"}}>không được tính vào tổng portfolio</b> vì đây là tiền vay, nhưng vẫn hiển thị ở Positions và Analytics.
            </div>
            <div style={{background:"#0a0512", border:"1px solid #ff6b9d15", borderRadius:6, padding:"10px 14px", marginTop:12, fontFamily:"monospace", fontSize:11, color:"#ff6b9d80", lineHeight:2.2}}>
              Net ROE = Amount × (Lend% − Borrow%) × (Days / 365)<br/>
              APR = (Net Profit / Amount) / Days × 365
            </div>
          </div>

          {carries.length === 0
            ? <div style={{...S.empty, marginTop:20}}>Chưa có carry trade. Nhấn <b style={{color:"#ff6b9d"}}>⇄ Carry Trade</b> ở trên.</div>
            : carries.map(ct => {
                const c = calcCarry(ct);
                return (
                  <div key={ct.id} style={S.ctDetailCard}>
                    <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16}}>
                      <div>
                        <span style={S.ctTag}>⇄ CARRY TRADE</span>
                        <span style={{color:"#ffb3d0", fontWeight:700, fontSize:16, marginLeft:10}}>{ct.asset}</span>
                        {ct.note && <span style={{color:"#5a4a6a", fontSize:12, marginLeft:8}}>{ct.note}</span>}
                      </div>
                      <div>
                        <button onClick={()=>editCT(ct)} style={{...S.iconBtn, fontSize:12}}>✎ Edit</button>
                        <button onClick={()=>deleteCT(ct.id)} style={{...S.iconBtn, color:"#ff4444", fontSize:12}}>✕ Del</button>
                      </div>
                    </div>
                    <div style={{display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(170px,1fr))", gap:12}}>
                      {[
                        ["Amount", fmtUSD(ct.amount), "#fff"],
                        ["Borrow Rate", `-${fmt(ct.borrowRate)}% APY`, "#ff6b9d"],
                        ["Lend Rate", `+${fmt(ct.lendRate)}% APY`, "#00ffc8"],
                        ["Net Spread", `${c.spread>=0?"+":""}${fmt(c.spread)}% APY`, c.spread>=0?"#00ffc8":"#ff4444"],
                        ["Lend Income (total)", `+${fmtUSD(c.lendIncome)}`, "#00ffc870"],
                        ["Borrow Cost (total)", `-${fmtUSD(c.borrowCost)}`, "#ff6b9d70"],
                        ["Net Profit at Maturity", `+${fmtUSD(c.totalNetEarned)}`, "#a78bfa"],
                        ["Net Accrued (now)", `+${fmtUSD(c.netEarned)}`, "#00ffc8"],
                        ["APR (net)", fmtPct(c.apr), "#00b8ff"],
                        ["Duration", `${ct.buyDate} → ${ct.maturityDate}`, "#5a7a9a"],
                      ].map(([lbl,val,col]) => (
                        <div key={lbl} style={{background:"#0e051a", borderRadius:8, padding:"12px 14px"}}>
                          <div style={{fontSize:9, color:"#3a6a8a", letterSpacing:1.5, textTransform:"uppercase", marginBottom:6}}>{lbl}</div>
                          <div style={{fontSize:16, fontWeight:700, fontFamily:"monospace", color:col||"#e0d0f0"}}>{val}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{marginTop:14}}>
                      <div style={{fontSize:10, color:"#3a6a8a", marginBottom:4}}>Progress: {fmt(c.progress,1)}% — {Math.ceil(c.daysLeft)}d remaining</div>
                      <div style={{...S.progBar, height:6}}><div style={{...S.progFill, width:`${c.progress}%`, background:"linear-gradient(90deg,#ff6b9d,#a78bfa)"}}/></div>
                    </div>
                  </div>
                );
              })}
        </div>
      )}

      {/* ═══════════════ ANALYTICS ═══════════════ */}
      {tab === "analytics" && (
        <div style={S.content}>
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16}}>
            {/* All allocation pie */}
            <div style={S.aCard}>
              <div style={S.aTitle}>Portfolio Allocation — Tất cả</div>
              <div style={{fontSize:10, color:"#3a6a8a", marginBottom:8}}>
                <span style={{color:"#00ffc8"}}>■</span> Kèo Gốc &nbsp;<span style={{color:"#ff6b9d"}}>■</span> Carry Trade
              </div>
              {pieAll.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={pieAll} cx="50%" cy="50%" innerRadius={58} outerRadius={90} paddingAngle={2} dataKey="value"
                      label={({name, percent})=>`${name.replace("[CT] ","")} ${(percent*100).toFixed(0)}%`}
                      labelLine={{stroke:"#1a2a3a"}}>
                      {pieAll.map((e,i)=>(
                        <Cell key={i} fill={e.kind==="carry" ? CT_PIE_COLORS[i % CT_PIE_COLORS.length] : PIE_COLORS[i % PIE_COLORS.length]}/>
                      ))}
                    </Pie>
                    <Tooltip contentStyle={S.tooltip} formatter={(v,n)=>[fmtUSD(v),n]}/>
                  </PieChart>
                </ResponsiveContainer>
              ) : <div style={S.empty}>No data</div>}
            </div>

            {/* Kèo Gốc only pie */}
            <div style={S.aCard}>
              <div style={S.aTitle}>Kèo Gốc — Phân bổ</div>
              {pieRegular.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={pieRegular} cx="50%" cy="50%" innerRadius={58} outerRadius={90} paddingAngle={2} dataKey="value"
                      label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}
                      labelLine={{stroke:"#1a2a3a"}}>
                      {pieRegular.map((_,i)=><Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                    </Pie>
                    <Tooltip contentStyle={S.tooltip} formatter={v=>fmtUSD(v)}/>
                  </PieChart>
                </ResponsiveContainer>
              ) : <div style={S.empty}>No data</div>}
            </div>
          </div>

          {positions.length > 0 && (
            <div style={S.aCard}>
              <div style={S.aTitle}>Kèo Gốc — APY vs ROE Earned vs APR</div>
              <ResponsiveContainer width="100%" height={195}>
                <BarChart data={positions.map(p=>{ const r=calcPositionROE(p); return {name:p.asset, "APY%":p.yieldRate, "ROE $":+r.earned.toFixed(2), "APR%":+r.apr.toFixed(2)}; })}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#0f2040"/>
                  <XAxis dataKey="name" tick={{fill:"#3a6a8a",fontSize:10}}/>
                  <YAxis tick={{fill:"#3a6a8a",fontSize:10}}/>
                  <Tooltip contentStyle={S.tooltip}/>
                  <Bar dataKey="APY%" fill="#a78bfa" radius={[3,3,0,0]}/>
                  <Bar dataKey="ROE $" fill="#00ffc8" radius={[3,3,0,0]}/>
                  <Bar dataKey="APR%" fill="#00b8ff" radius={[3,3,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {carries.length > 0 && (
            <div style={S.aCard}>
              <div style={S.aTitle}>Carry Trade — Spread Analysis</div>
              <ResponsiveContainer width="100%" height={195}>
                <BarChart data={carries.map(ct=>{ const c=calcCarry(ct); return {name:ct.asset, "Borrow%":ct.borrowRate, "Lend%":ct.lendRate, "Spread%":+c.spread.toFixed(2), "Net $":+c.netEarned.toFixed(2)}; })}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#0f2040"/>
                  <XAxis dataKey="name" tick={{fill:"#3a6a8a",fontSize:10}}/>
                  <YAxis tick={{fill:"#3a6a8a",fontSize:10}}/>
                  <Tooltip contentStyle={S.tooltip}/>
                  <Bar dataKey="Borrow%" fill="#ff6b9d" radius={[3,3,0,0]}/>
                  <Bar dataKey="Lend%" fill="#00ffc8" radius={[3,3,0,0]}/>
                  <Bar dataKey="Spread%" fill="#ffaa00" radius={[3,3,0,0]}/>
                  <Bar dataKey="Net $" fill="#a78bfa" radius={[3,3,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {positions.length > 0 && (
            <div style={S.aCard}>
              <div style={S.aTitle}>Expected vs Accrued — Kèo Gốc</div>
              <div style={S.tableWrap}>
                <table style={{...S.table, marginTop:12}}>
                  <thead><tr>{["Asset","Days","Elapsed","Expected ROE $","Expected ROE %","APR","Accrued $","Remaining $","Done%"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
                  <tbody>
                    {positions.map(p=>{ const r=calcPositionROE(p); return (
                      <tr key={p.id} style={S.tr}>
                        <td style={{...S.td, color:"#e0f0ff", fontWeight:600}}>{p.asset}</td>
                        <td style={S.tdM}>{Math.round(r.totalDays)}d</td>
                        <td style={S.tdM}>{Math.round(r.elapsed)}d</td>
                        <td style={{...S.tdM, color:"#a78bfa"}}>{fmtUSD(r.totalExpectedEarned)}</td>
                        <td style={{...S.tdM, color:"#a78bfa"}}>{fmtPct(r.totalExpectedPct)}</td>
                        <td style={{...S.tdM, color:"#00b8ff", fontWeight:700}}>{fmtPct(r.apr)}</td>
                        <td style={{...S.tdM, color:"#00ffc8"}}>{fmtUSD(r.earned)}</td>
                        <td style={{...S.tdM, color:"#ffaa00"}}>{fmtUSD(r.totalExpectedEarned-r.earned)}</td>
                        <td style={S.tdM}>{fmt(r.progress,1)}%</td>
                      </tr>
                    );})}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ CALCULATOR ═══════════════ */}
      {tab === "calculator" && (
        <div style={S.content}>
          <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:20}}>

            {/* APR / ROE Calculator */}
            <div style={S.calcCard}>
              <div style={{color:"#00ffc8", fontSize:16, fontWeight:700, marginBottom:4}}>⌗ APR & ROE Calculator</div>
              <div style={{color:"#3a6a8a", fontSize:12, marginBottom:10}}>Tính APR và ROE cho bất kỳ kèo nào</div>
              <div style={{background:"#050d1a", border:"1px solid #00ffc815", borderRadius:6, padding:"10px 14px", marginBottom:16, fontFamily:"monospace", fontSize:11, color:"#00ffc870", lineHeight:2.2}}>
                APR = (Lãi / Vốn) ÷ Số Ngày × 365<br/>
                ROE % = (Lãi / Vốn) × 100
              </div>
              <div style={{display:"flex", flexDirection:"column", gap:12}}>
                <FormField label="Số tiền đầu tư ($)" value={calcState.invested} onChange={v=>setCalcState(c=>({...c,invested:v}))} type="number" placeholder="e.g. 10000"/>
                <FormField label="Số tiền lãi nhận ($)" value={calcState.profit} onChange={v=>setCalcState(c=>({...c,profit:v}))} type="number" placeholder="e.g. 300"/>
                <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
                  <FormField label="Ngày bắt đầu" value={calcState.startDate} onChange={v=>setCalcState(c=>({...c,startDate:v}))} type="date"/>
                  <FormField label="Ngày đáo hạn" value={calcState.endDate} onChange={v=>setCalcState(c=>({...c,endDate:v}))} type="date"/>
                </div>
                <button onClick={runCalc} style={S.submitBtn}>Tính APR & ROE</button>
              </div>
              {calcState.result && (
                <div style={{background:"#050d1a", border:"1px solid #00ffc818", borderRadius:8, padding:"14px 16px", marginTop:14}}>
                  {[
                    ["Số ngày", `${calcState.result.days} ngày`, "#e0f0ff"],
                    ["ROE %", fmtPct(calcState.result.roe), "#00ffc8"],
                    ["APR (annualised)", fmtPct(calcState.result.apr), "#00b8ff"],
                    ["Lợi nhuận/ngày", `+$${fmt(calcState.result.daily)}/day`, "#a78bfa"],
                  ].map(([lbl,val,col])=>(
                    <div key={lbl} style={{display:"flex", justifyContent:"space-between", padding:"7px 0", borderBottom:"1px solid #0a1a2e", fontSize:13}}>
                      <span style={{color:"#3a6a8a"}}>{lbl}</span>
                      <span style={{color:col, fontFamily:"monospace", fontWeight:700, fontSize:18}}>{val}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Carry Trade Calculator */}
            <div style={{...S.calcCard, borderColor:"#ff6b9d25"}}>
              <div style={{color:"#ff6b9d", fontSize:16, fontWeight:700, marginBottom:4}}>⇄ Carry Trade Calculator</div>
              <div style={{color:"#3a6a8a", fontSize:12, marginBottom:10}}>Ước tính lợi nhuận carry trade</div>
              <div style={{background:"#0a0512", border:"1px solid #ff6b9d15", borderRadius:6, padding:"10px 14px", marginBottom:16, fontFamily:"monospace", fontSize:11, color:"#ff6b9d80", lineHeight:2.2}}>
                Net Spread = Lend Rate − Borrow Rate<br/>
                Net ROE = Amount × Spread × (Days / 365)
              </div>
              <div style={{display:"flex", flexDirection:"column", gap:12}}>
                <FormField label="Amount ($)" value={ctCalc.amount} onChange={v=>setCtCalc(c=>({...c,amount:v}))} type="number" placeholder="e.g. 10000"/>
                <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:12}}>
                  <FormField label="🔴 Borrow Rate %" value={ctCalc.borrowRate} onChange={v=>setCtCalc(c=>({...c,borrowRate:v}))} type="number" placeholder="e.g. 3"/>
                  <FormField label="🟢 Lend Rate %" value={ctCalc.lendRate} onChange={v=>setCtCalc(c=>({...c,lendRate:v}))} type="number" placeholder="e.g. 10"/>
                  <FormField label="Start Date" value={ctCalc.startDate} onChange={v=>setCtCalc(c=>({...c,startDate:v}))} type="date"/>
                  <FormField label="End Date" value={ctCalc.endDate} onChange={v=>setCtCalc(c=>({...c,endDate:v}))} type="date"/>
                </div>
                <button onClick={runCtCalc} style={{...S.submitBtn, background:"#ff6b9d"}}>Tính Carry Trade</button>
              </div>
              {ctCalc.result && (
                <div style={{background:"#0a0512", border:"1px solid #ff6b9d18", borderRadius:8, padding:"14px 16px", marginTop:14}}>
                  {[
                    ["Số ngày", `${ctCalc.result.days} ngày`, "#e0f0ff"],
                    ["Net Spread", `${ctCalc.result.spread>=0?"+":""}${fmt(ctCalc.result.spread)}% APY`, ctCalc.result.spread>=0?"#00ffc8":"#ff4444"],
                    ["Lend Income", `+${fmtUSD(ctCalc.result.lendIncome)}`, "#00ffc8"],
                    ["Borrow Cost", `-${fmtUSD(ctCalc.result.borrowCost)}`, "#ff6b9d"],
                    ["Net Profit", `+${fmtUSD(ctCalc.result.netProfit)}`, "#00ffc8"],
                    ["Net ROE %", fmtPct(ctCalc.result.netRoe), "#a78bfa"],
                    ["APR (net)", fmtPct(ctCalc.result.apr), "#00b8ff"],
                  ].map(([lbl,val,col])=>(
                    <div key={lbl} style={{display:"flex", justifyContent:"space-between", padding:"7px 0", borderBottom:"1px solid #0f0518", fontSize:13}}>
                      <span style={{color:"#3a6a8a"}}>{lbl}</span>
                      <span style={{color:col, fontFamily:"monospace", fontWeight:700, fontSize:16}}>{val}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* APR summary table */}
          {positions.length > 0 && (
            <div style={S.aCard}>
              <div style={S.aTitle}>APR Summary — Tất cả Kèo Gốc</div>
              <div style={S.tableWrap}>
                <table style={{...S.table, marginTop:12}}>
                  <thead><tr>{["Asset","Amount","APY (input)","Duration","Expected Profit","ROE %","APR %","$/day"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
                  <tbody>
                    {positions.map(p=>{ const r=calcPositionROE(p); const daily=p.amount*(p.yieldRate/100)/365; return (
                      <tr key={p.id} style={S.tr}>
                        <td style={{...S.td, color:"#e0f0ff", fontWeight:600}}>{p.asset}</td>
                        <td style={S.tdM}>{fmtUSD(p.amount)}</td>
                        <td style={{...S.tdM, color:"#a78bfa"}}>{fmtPct(p.yieldRate)}</td>
                        <td style={S.tdM}>{Math.round(r.totalDays)}d</td>
                        <td style={{...S.tdM, color:"#00ffc8"}}>+{fmtUSD(r.totalExpectedEarned)}</td>
                        <td style={{...S.tdM, color:"#00ffc8"}}>{fmtPct(r.totalExpectedPct)}</td>
                        <td style={{...S.tdM, color:"#00b8ff", fontWeight:700}}>{fmtPct(r.apr)}</td>
                        <td style={{...S.tdM, color:"#ffaa00"}}>+${fmt(daily)}</td>
                      </tr>
                    );})}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ MODAL: KÈO GỐC ═══════════════ */}
      {showPosForm && (
        <div style={S.overlay} onClick={()=>setShowPosForm(false)}>
          <div style={S.modal} onClick={e=>e.stopPropagation()}>
            <div style={S.mHeader}>
              <span style={{color:"#00ffc8", fontSize:17, fontWeight:700}}>{editPosId?"✎ Edit Kèo Gốc":"+ New Kèo Gốc"}</span>
              <button onClick={()=>setShowPosForm(false)} style={{...S.iconBtn, color:"#ff4444", fontSize:18}}>✕</button>
            </div>
            <div style={S.formGrid}>
              <FormField label="Asset / Pool" value={posForm.asset} onChange={v=>setPosForm(f=>({...f,asset:v}))} placeholder="e.g. weETH-26DEC2025"/>
              <FormField label="Note" value={posForm.note} onChange={v=>setPosForm(f=>({...f,note:v}))} placeholder="optional"/>
              <FormField label="Buy Date" value={posForm.buyDate} onChange={v=>setPosForm(f=>({...f,buyDate:v}))} type="date"/>
              <FormField label="Maturity Date" value={posForm.maturityDate} onChange={v=>setPosForm(f=>({...f,maturityDate:v}))} type="date"/>
              <FormField label="Amount (USD)" value={posForm.amount} onChange={v=>setPosForm(f=>({...f,amount:v}))} type="number" placeholder="e.g. 5000"/>
              <FormField label="Fixed Yield APY %" value={posForm.yieldRate} onChange={v=>setPosForm(f=>({...f,yieldRate:v}))} type="number" placeholder="e.g. 12.5"/>
            </div>
            {posForm.amount && posForm.yieldRate && posForm.buyDate && posForm.maturityDate && (()=>{
              const pr=calcPositionROE({...posForm, amount:+posForm.amount, yieldRate:+posForm.yieldRate});
              return (
                <div style={S.preview}>
                  <div style={{fontSize:9, color:"#3a6a8a", letterSpacing:2, textTransform:"uppercase", marginBottom:10}}>Preview</div>
                  {[["Duration",`${Math.round(pr.totalDays)} days`,"#e0f0ff"],["Expected ROE",`+${fmtUSD(pr.totalExpectedEarned)} (${fmtPct(pr.totalExpectedPct)})`,"#00ffc8"],["APR",fmtPct(pr.apr),"#00b8ff"],["Daily",`+$${fmt((+posForm.amount*(+posForm.yieldRate)/100)/365)}/day`,"#a78bfa"]].map(([l,v,c])=>(
                    <div key={l} style={{display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:"1px solid #0a1a2e", fontSize:12, color:"#5a7a9a"}}>
                      <span>{l}</span><span style={{color:c, fontFamily:"monospace"}}>{v}</span>
                    </div>
                  ))}
                </div>
              );
            })()}
            <button onClick={submitPos} style={S.submitBtn}>{editPosId?"Save":"Add Kèo Gốc"}</button>
          </div>
        </div>
      )}

      {/* ═══════════════ MODAL: CARRY TRADE ═══════════════ */}
      {showCTForm && (
        <div style={S.overlay} onClick={()=>setShowCTForm(false)}>
          <div style={{...S.modal, borderColor:"#ff6b9d30"}} onClick={e=>e.stopPropagation()}>
            <div style={S.mHeader}>
              <span style={{color:"#ff6b9d", fontSize:17, fontWeight:700}}>{editCTId?"✎ Edit Carry Trade":"⇄ New Carry Trade"}</span>
              <button onClick={()=>setShowCTForm(false)} style={{...S.iconBtn, color:"#ff4444", fontSize:18}}>✕</button>
            </div>
            <div style={S.formGrid}>
              <FormField label="Asset / Pool" value={ctForm.asset} onChange={v=>setCtForm(f=>({...f,asset:v}))} placeholder="e.g. USDC Carry"/>
              <FormField label="Note" value={ctForm.note} onChange={v=>setCtForm(f=>({...f,note:v}))} placeholder="optional"/>
              <FormField label="Buy Date" value={ctForm.buyDate} onChange={v=>setCtForm(f=>({...f,buyDate:v}))} type="date"/>
              <FormField label="Maturity Date" value={ctForm.maturityDate} onChange={v=>setCtForm(f=>({...f,maturityDate:v}))} type="date"/>
              <FormField label="Amount (USD)" value={ctForm.amount} onChange={v=>setCtForm(f=>({...f,amount:v}))} type="number" placeholder="e.g. 10000"/>
              <div/>
              <FormField label="🔴 Borrow Rate APY %" value={ctForm.borrowRate} onChange={v=>setCtForm(f=>({...f,borrowRate:v}))} type="number" placeholder="e.g. 3"/>
              <FormField label="🟢 Lend Rate APY %" value={ctForm.lendRate} onChange={v=>setCtForm(f=>({...f,lendRate:v}))} type="number" placeholder="e.g. 10"/>
            </div>
            {ctForm.amount && ctForm.borrowRate && ctForm.lendRate && ctForm.buyDate && ctForm.maturityDate && (()=>{
              const pr=calcCarry({...ctForm, amount:+ctForm.amount, borrowRate:+ctForm.borrowRate, lendRate:+ctForm.lendRate});
              return (
                <div style={{...S.preview, borderColor:"#ff6b9d18"}}>
                  <div style={{fontSize:9, color:"#3a6a8a", letterSpacing:2, textTransform:"uppercase", marginBottom:10}}>Preview</div>
                  {[["Duration",`${Math.round(pr.totalDays)} days`,"#e0f0ff"],["Net Spread",`${pr.spread>=0?"+":""}${fmt(pr.spread)}% APY`, pr.spread>=0?"#00ffc8":"#ff4444"],["Lend Income",`+${fmtUSD(pr.lendIncome)}`,"#00ffc8"],["Borrow Cost",`-${fmtUSD(pr.borrowCost)}`,"#ff6b9d"],["Net Profit at Maturity",`+${fmtUSD(pr.totalNetEarned)}`,"#00ffc8"],["APR (net)",fmtPct(pr.apr),"#00b8ff"]].map(([l,v,c])=>(
                    <div key={l} style={{display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:"1px solid #0f0518", fontSize:12, color:"#5a7a9a"}}>
                      <span>{l}</span><span style={{color:c, fontFamily:"monospace", fontWeight:600}}>{v}</span>
                    </div>
                  ))}
                </div>
              );
            })()}
            <button onClick={submitCT} style={{...S.submitBtn, background:"#ff6b9d"}}>{editCTId?"Save":"Add Carry Trade"}</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────
function KPICard({ label, value, sub, accent, icon }) {
  return (
    <div style={{ background:"#071422", border:`1px solid ${accent}25`, borderRadius:10, padding:"18px 20px" }}>
      <div style={{ fontSize:20, color:accent, marginBottom:8 }}>{icon}</div>
      <div style={{ fontSize:10, color:"#3a6a8a", letterSpacing:1.5, textTransform:"uppercase", marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:26, fontWeight:800, fontFamily:"monospace", lineHeight:1, color:accent }}>{value}</div>
      <div style={{ fontSize:10, color:"#3a6a8a", marginTop:6 }}>{sub}</div>
    </div>
  );
}
function CompCard({ label, data }) {
  if (!data) return <div style={S.compCard}><div style={S.compLabel}>{label}</div><div style={{color:"#3a6a8a",fontSize:12,marginTop:8}}>No snapshot yet</div></div>;
  const pos = data.earnedDiff >= 0;
  return (
    <div style={S.compCard}>
      <div style={S.compLabel}>{label}</div>
      <div style={{color:pos?"#00ffc8":"#ff4444", fontSize:22, fontWeight:700, marginTop:8, fontFamily:"monospace"}}>{pos?"+":""}{fmtUSD(data.earnedDiff)}</div>
      <div style={{color:pos?"#00ffc8":"#ff4444", fontSize:11, marginTop:3}}>{pos?"▲":"▼"} {fmtPct(data.pctDiff)} portfolio ROE</div>
      <div style={{color:"#3a6a8a", fontSize:11, marginTop:5}}>Capital Δ: {data.investedDiff>=0?"+":""}{fmtUSD(data.investedDiff)}</div>
    </div>
  );
}
function FormField({ label, value, onChange, type="text", placeholder }) {
  return (
    <div style={S.formField}>
      <label style={S.formLabel}>{label}</label>
      <input type={type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} style={S.input}/>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────────────────────────────────────
const S = {
  root: { background:"#050d1a", minHeight:"100vh", color:"#c8d8e8", fontFamily:"'DM Sans','Segoe UI',sans-serif", position:"relative", overflowX:"hidden" },
  gridBg: { position:"fixed", top:0, left:0, right:0, bottom:0, backgroundImage:`linear-gradient(#0a1a2e 1px,transparent 1px),linear-gradient(90deg,#0a1a2e 1px,transparent 1px)`, backgroundSize:"40px 40px", opacity:.4, pointerEvents:"none", zIndex:0 },
  header: { position:"relative", zIndex:1, display:"flex", alignItems:"center", justifyContent:"space-between", padding:"18px 28px", borderBottom:"1px solid #0f2040", background:"linear-gradient(180deg,#050f1e 0%,transparent 100%)" },
  logoWrap: { display:"flex", alignItems:"center", gap:14 },
  logoIcon: { fontSize:30, color:"#00ffc8", filter:"drop-shadow(0 0 12px #00ffc870)" },
  logoTitle: { fontSize:18, fontWeight:800, letterSpacing:4, color:"#e0f8ff", fontFamily:"monospace" },
  logoSub: { fontSize:10, color:"#3a6a8a", letterSpacing:2, marginTop:2 },
  headerRight: { display:"flex", alignItems:"center", gap:14 },
  liveTag: { background:"#001a10", border:"1px solid #00ffc840", color:"#00ffc8", fontSize:10, padding:"4px 10px", borderRadius:4, letterSpacing:1, fontFamily:"monospace" },
  dateTag: { color:"#3a6a8a", fontSize:11, fontFamily:"monospace" },
  nav: { position:"relative", zIndex:1, display:"flex", alignItems:"center", gap:4, padding:"10px 28px", borderBottom:"1px solid #0f2040", flexWrap:"wrap" },
  navBtn: { background:"transparent", border:"1px solid transparent", color:"#4a6a8a", padding:"8px 14px", borderRadius:6, cursor:"pointer", fontSize:12, transition:"all .2s" },
  navBtnActive: { background:"#0a1e33", border:"1px solid #00ffc830", color:"#00ffc8" },
  addBtn: { background:"#00ffc8", color:"#050d1a", border:"none", padding:"9px 16px", borderRadius:6, cursor:"pointer", fontWeight:700, fontSize:12, boxShadow:"0 0 18px #00ffc835" },
  content: { position:"relative", zIndex:1, padding:"22px 28px", maxWidth:1400 },
  sectionLabel: { fontSize:10, color:"#3a6a8a", letterSpacing:2, textTransform:"uppercase", marginBottom:12, marginTop:4 },
  kpiGrid: { display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(200px,1fr))", gap:14, marginBottom:20 },
  ctSummaryBox: { background:"#120810", border:"1px solid #ff6b9d20", borderRadius:10, padding:"16px 20px", marginBottom:20 },
  ctSummaryTitle: { fontSize:10, color:"#ff6b9d", letterSpacing:2, textTransform:"uppercase", marginBottom:12 },
  ctSummaryGrid: { display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 },
  ctStat: { fontSize:9, color:"#3a6a8a", letterSpacing:1.5, textTransform:"uppercase", marginBottom:4 },
  ctStatVal: { fontSize:18, fontWeight:700, fontFamily:"monospace" },
  compGrid: { display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:20 },
  compCard: { background:"#071422", border:"1px solid #0f2040", borderRadius:10, padding:"16px 18px" },
  compLabel: { fontSize:10, color:"#3a6a8a", letterSpacing:1.5, textTransform:"uppercase" },
  chartBox: { background:"#071422", border:"1px solid #0f2040", borderRadius:10, padding:"16px", marginBottom:20 },
  chartTitle: { fontSize:10, color:"#3a6a8a", letterSpacing:2, textTransform:"uppercase", marginBottom:12 },
  tooltip: { background:"#071422", border:"1px solid #0f2040", borderRadius:6, color:"#c8d8e8", fontSize:11 },
  alertBox: { background:"#071422", border:"1px solid #ffaa0025", borderRadius:10, overflow:"hidden", marginBottom:20 },
  alertRow: { display:"grid", gridTemplateColumns:"60px 70px 1fr 110px 110px", padding:"11px 18px", gap:8, borderBottom:"1px solid #0f2040", fontSize:12, alignItems:"center" },
  tableWrap: { overflowX:"auto" },
  table: { width:"100%", borderCollapse:"collapse", fontSize:12 },
  th: { padding:"9px 12px", textAlign:"left", fontSize:9, color:"#3a6a8a", letterSpacing:1.5, textTransform:"uppercase", borderBottom:"1px solid #0f2040", whiteSpace:"nowrap" },
  tr: { borderBottom:"1px solid #0a1a2e" },
  td: { padding:"11px 12px", color:"#7a9ab8" },
  tdM: { padding:"11px 12px", color:"#7a9ab8", fontFamily:"monospace", fontSize:11, whiteSpace:"nowrap" },
  progBar: { height:4, background:"#0a1a2e", borderRadius:2, overflow:"hidden" },
  progFill: { height:"100%", borderRadius:2 },
  badge: { border:"1px solid", borderRadius:3, padding:"2px 6px", fontSize:9, letterSpacing:1, fontFamily:"monospace" },
  iconBtn: { background:"transparent", border:"none", cursor:"pointer", color:"#4a6a8a", fontSize:13, padding:"2px 5px" },
  empty: { color:"#3a6a8a", padding:"36px", textAlign:"center", fontSize:13 },
  ctInfoBox: { background:"#140818", border:"1px solid #ff6b9d20", borderRadius:10, padding:"18px 22px", marginBottom:22 },
  ctTag: { fontSize:9, border:"1px solid #ff6b9d50", color:"#ff6b9d", padding:"2px 6px", borderRadius:3, letterSpacing:1 },
  ctDetailCard: { background:"#0e0516", border:"1px solid #ff6b9d22", borderRadius:12, padding:"20px", marginBottom:16 },
  aCard: { background:"#071422", border:"1px solid #0f2040", borderRadius:10, padding:"18px", marginBottom:14, overflowX:"auto" },
  aTitle: { fontSize:10, color:"#3a6a8a", letterSpacing:2, textTransform:"uppercase", marginBottom:4 },
  calcCard: { background:"#071422", border:"1px solid #00ffc820", borderRadius:12, padding:"22px" },
  overlay: { position:"fixed", inset:0, background:"#000c", backdropFilter:"blur(5px)", zIndex:100, display:"flex", alignItems:"center", justifyContent:"center" },
  modal: { background:"#071422", border:"1px solid #00ffc830", borderRadius:14, padding:"26px", width:"min(560px,95vw)", maxHeight:"90vh", overflowY:"auto" },
  mHeader: { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 },
  formGrid: { display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 },
  formField: { display:"flex", flexDirection:"column", gap:6 },
  formLabel: { fontSize:10, color:"#3a6a8a", letterSpacing:1.2, textTransform:"uppercase" },
  input: { background:"#050d1a", border:"1px solid #0f2040", borderRadius:6, padding:"10px 12px", color:"#e0f0ff", fontSize:13, outline:"none", fontFamily:"monospace" },
  preview: { background:"#050d1a", border:"1px solid #00ffc818", borderRadius:8, padding:"14px", margin:"14px 0" },
  submitBtn: { width:"100%", background:"#00ffc8", color:"#050d1a", border:"none", borderRadius:8, padding:"12px", fontWeight:800, fontSize:13, cursor:"pointer", letterSpacing:1, marginTop:4 },
};
