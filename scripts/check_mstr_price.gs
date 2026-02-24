/**
 * 多股票价格与 170 周均线监控脚本
 * 监控股票列表中的价格与 170 周均线的关系，将结果发送到指定邮箱
 */

// ============ 配置区 ============
const TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "MSTR", "UBER", "AMD", "TSM", "MCD", "KO"]; // 美股7姐妹 + MSTR + 优步/AMD/台积电/麦当劳/可口可乐
const MARKET_INDICES = [
  { ticker: "IVV", name: "IVV (标普ETF)" },
  { ticker: "QQQ", name: "QQQ (纳指ETF)" }
];
const HONG_KONG_STOCKS = [
  { ticker: "1810.HK", name: "小米" },
  { ticker: "0700.HK", name: "腾讯" },
  { ticker: "9988.HK", name: "阿里巴巴" },
  { ticker: "3690.HK", name: "美团" }
];
const EMAIL = "zuo_hang97@163.com";
const MA_WEEKS = 170;

function checkStockPrices() {
  const results = [];
  for (const ticker of TICKERS) {
    try {
      results.push(getPriceAndMA170(ticker));
    } catch (e) {
      results.push({ ticker: ticker, error: e.toString() });
    }
  }

  const marketResults = [];
  for (let i = 0; i < MARKET_INDICES.length; i++) {
    const item = MARKET_INDICES[i];
    try {
      const info = getPriceAndMA170(item.ticker);
      info.name = item.name;
      marketResults.push(info);
    } catch (e) {
      marketResults.push({ ticker: item.ticker, name: item.name, error: e.toString() });
    }
  }

  const hkResults = [];
  for (let i = 0; i < HONG_KONG_STOCKS.length; i++) {
    const item = HONG_KONG_STOCKS[i];
    try {
      const info = getPriceAndMA170(item.ticker);
      info.name = item.name;
      hkResults.push(info);
    } catch (e) {
      hkResults.push({ ticker: item.ticker, name: item.name, error: e.toString() });
    }
  }

  const subject = `股价VS170周均线 ${formatDate(new Date())}`;
  const htmlBody = buildEmailHtmlBody(results, marketResults, hkResults);
  MailApp.sendEmail(EMAIL, subject, "", { htmlBody: htmlBody });
}

/**
 * 获取指定股票的当前价格和 170 周均线
 */
function getPriceAndMA170(ticker) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?range=10y&interval=1wk`;
  const response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  const data = JSON.parse(response.getContentText());

  if (!data.chart || !data.chart.result || data.chart.result.length === 0) {
    throw new Error("无法获取行情数据");
  }

  const result = data.chart.result[0];
  const currentPrice = result.meta.regularMarketPrice;

  // 获取周线收盘价：优先 adjclose（复权），否则用 quote.close
  let closes = [];
  if (result.indicators.adjclose && result.indicators.adjclose[0]) {
    closes = result.indicators.adjclose[0].adjclose || [];
  }
  if (closes.length === 0 && result.indicators.quote && result.indicators.quote[0]) {
    closes = result.indicators.quote[0].close || [];
  }

  // 过滤掉 null
  closes = closes.filter(function(c) { return c != null; });

  if (closes.length < MA_WEEKS) {
    throw new Error("历史数据不足 " + MA_WEEKS + " 周，当前仅 " + closes.length + " 周");
  }

  const last170 = closes.slice(-MA_WEEKS);
  const ma170 = last170.reduce(function(a, b) { return a + b; }, 0) / MA_WEEKS;

  const diffPercent = ((currentPrice - ma170) / ma170) * 100;
  const relation = currentPrice >= ma170 ? "≥" : "<";

  return {
    ticker: ticker,
    price: currentPrice,
    ma170: ma170,
    diffPercent: diffPercent,
    relation: relation
  };
}

/**
 * 根据偏离均线幅度给出操作建议
 * 梯度：≤0 考虑买入；0~15% 持有；15~30% 卖1/3；30~50% 再卖1/3；>50% 可卖剩余
 */
function getSuggestion(diffPercent) {
  if (diffPercent <= 0) return { text: "考虑买入", color: "#0a0" };
  if (diffPercent <= 15) return { text: "持有观望", color: "#666" };
  if (diffPercent <= 30) return { text: "分批卖 1/3", color: "#c60" };
  if (diffPercent <= 50) return { text: "分批再卖 1/3", color: "#c00" };
  return { text: "分批卖剩余", color: "#800" };
}

/**
 * 构建单行表格 HTML
 */
function buildTableRows(results, showName) {
  let rows = "";
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const label = (showName && r.name) ? r.name : r.ticker;
    if (r.error) {
      rows += "<tr><td>" + label + "</td><td colspan='5' style='color:#c00'>获取失败: " + r.error + "</td></tr>";
    } else {
      const diffStr = (r.diffPercent >= 0 ? "+" : "") + r.diffPercent.toFixed(2) + "%";
      const diffColor = r.diffPercent >= 0 ? "#0a0" : "#c00";
      const status = r.price >= r.ma170 ? "✅ 均线上方" : "⚠️ 均线下方";
      const sug = getSuggestion(r.diffPercent);
      rows += "<tr><td><b>" + label + "</b></td><td>" + r.price.toFixed(2) + "</td><td>" +
        r.ma170.toFixed(2) + "</td><td style='color:" + diffColor + "'><b>" + diffStr + "</b></td><td>" + status +
        "</td><td style='color:" + sug.color + "; font-weight:bold'>" + sug.text + "</td></tr>";
    }
  }
  return rows;
}

/**
 * 构建邮件正文（HTML 表格格式）
 */
function buildEmailHtmlBody(results, marketResults, hkResults) {
  const stockTable = "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%'>" +
    "<thead><tr style='background:#f0f0f0'><th>代码</th><th>当前价</th><th>170周MA</th><th>偏离</th><th>状态</th><th>建议</th></tr></thead>" +
    "<tbody>" + buildTableRows(results, false) + "</tbody></table>";

  const marketTable = "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%'>" +
    "<thead><tr style='background:#e8f4f8'><th>大盘/ETF</th><th>当前价</th><th>170周MA</th><th>偏离</th><th>状态</th><th>建议</th></tr></thead>" +
    "<tbody>" + buildTableRows(marketResults, true) + "</tbody></table>";

  const hkTable = "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%'>" +
    "<thead><tr style='background:#f5f0e8'><th>港股</th><th>当前价</th><th>170周MA</th><th>偏离</th><th>状态</th><th>建议</th></tr></thead>" +
    "<tbody>" + buildTableRows(hkResults, true) + "</tbody></table>";

  const html = "<div style='font-family: Arial, sans-serif; max-width: 520px'>" +
    "<h3>股票价格观察</h3>" + stockTable +
    "<h3 style='margin-top:20px'>大盘价格观察</h3>" + marketTable +
    "<h3 style='margin-top:20px'>港股价格观察</h3>" + hkTable +
    "<p style='color:#888; font-size:12px; margin-top:12px'>生成时间: " + formatDate(new Date()) + "</p></div>";
  return html;
}

function formatDate(d) {
  return Utilities.formatDate(d, "Asia/Shanghai", "yyyy-MM-dd HH:mm");
}
