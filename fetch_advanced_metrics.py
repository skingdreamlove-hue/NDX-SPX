import os
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import tempfile
import time

# Disable yfinance SQLite cache to avoid "unable to open database file" errors
yf.set_tz_cache_location(tempfile.gettempdir())

class AdvancedMetricsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        self.timeout = 30

        self.BARCHART_SPY_URL = "https://www.barchart.com/etfs-funds/quotes/SPY/technical-analysis"
        self.BARCHART_NDX_URL = "https://www.barchart.com/etfs-funds/quotes/NDX/technical-analysis"
        
        self.FRED_CREDIT_SPREAD_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2"

        self.YAHOO_VIX3M_SYMBOL = "^VIX3M"
        self.YAHOO_TNX_SYMBOL = "^TNX"

        self.STOCKCHARTS_SPXA200R_URL = "https://stockcharts.com/sc3/ui/?s=%24SPXA200R"
        self.STOCKCHARTS_NDXA200R_URL = "https://stockcharts.com/sc3/ui/?s=%24NDXA200R"
        
        # MacroMicro 纳斯达克100 200日线比例
        self.MACROMICRO_NDX_MA200_URL = "https://www.macromicro.me/series/25229/nasdaq100-ma200-breadth"

    def _get_yahoo_symbol_data(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            if hist.empty:
                print(f"    {symbol}: 无数据")
                return None
            current_price = float(hist['Close'].iloc[-1])
            return {
                'current_price': current_price,
                'close_prices': hist['Close'].tolist()
            }
        except Exception as e:
            print(f"    {symbol} 获取失败: {str(e)}")
            return None

    def get_sp500_breadth_real(self):
        """Calculate real S&P 500 breadth using component stocks"""
        sp500_components = [
            'MMM', 'AOS', 'ABT', 'ABBV', 'ACN', 'ADBE', 'AMD', 'AAP', 'AES', 'AFL',
            'A', 'APD', 'ABNB', 'AKAM', 'ALB', 'ARE', 'ALGN', 'ALLE', 'LNT', 'ALL',
            'GOOGL', 'GOOG', 'MO', 'AMZN', 'AMCR', 'AEE', 'AAL', 'AEP', 'AXP', 'AIG',
            'AMT', 'AWK', 'AMP', 'AME', 'AMGN', 'APH', 'ADI', 'ANSS', 'AON', 'APA',
            'AAPL', 'AMAT', 'APTV', 'ACGL', 'ADM', 'ANET', 'AJG', 'AIZ', 'T', 'ATO',
            'ADSK', 'ADP', 'AZO', 'AVB', 'AVY', 'AXON', 'BKR', 'BALL', 'BAC', 'BK',
            'BBWI', 'BAX', 'BDX', 'BBY', 'TECH', 'BIIB', 'BLK', 'BX', 'BA',
            'BKNG', 'BWA', 'BSX', 'BMY', 'AVGO', 'BR', 'BRO', 'BLDR', 'BG',
            'CDNS', 'CZR', 'CPT', 'CPB', 'COF', 'CAH', 'KMX', 'CCL', 'CARR', 'CTLT',
            'CAT', 'CBOE', 'CBRE', 'CDW', 'CE', 'COR', 'CNC', 'CNP', 'CF', 'CHRW',
            'CRL', 'SCHW', 'CHTR', 'CVX', 'CMG', 'CB', 'CHD', 'CI', 'CINF', 'CTAS',
            'CSCO', 'C', 'CFG', 'CLX', 'CME', 'CMS', 'KO', 'CTSH', 'CL', 'CMCSA',
            'CMA', 'CAG', 'COP', 'ED', 'STZ', 'CEG', 'COO', 'CPRT', 'GLW', 'CPAY',
            'CTVA', 'CSGP', 'COST', 'CTRA', 'CCI', 'CSX', 'CMI', 'CVS', 'DHI', 'DHR',
            'DRI', 'DVA', 'DAY', 'DECK', 'DE', 'DAL', 'DVN', 'DXCM', 'FANG', 'DLR',
            'DFS', 'DG', 'DLTR', 'D', 'DPZ', 'DOV', 'DOW', 'DTE', 'DUK', 'DD',
            'EMN', 'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'ELV', 'LLY', 'EMR',
            'ENPH', 'ETR', 'EOG', 'EPAM', 'EQT', 'EFX', 'EQIX', 'EQR', 'ESS', 'EL',
            'EG', 'EVRG', 'ES', 'EXC', 'EXPE', 'EXPD', 'EXR', 'XOM', 'FFIV', 'FDS',
            'FICO', 'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FSLR', 'FE', 'FI', 'FMC',
            'F', 'FTNT', 'FTV', 'FOXA', 'FOX', 'BEN', 'FCX', 'GRMN', 'IT', 'GE',
            'GEHC', 'GEV', 'GEN', 'GNRC', 'GD', 'GIS', 'GM', 'GPC', 'GILD', 'GPN',
            'GL', 'GDDY', 'GS', 'HAL', 'HIG', 'HAS', 'HCA', 'DOC', 'HSIC', 'HSY',
            'HES', 'HPE', 'HLT', 'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HWM', 'HPQ',
            'HUBB', 'HUM', 'HBAN', 'HII', 'IBM', 'IEX', 'IDXX', 'ITW', 'INCY', 'IR',
            'PODD', 'INTC', 'ICE', 'IFF', 'IP', 'IPG', 'INTU', 'ISRG', 'IVZ', 'INVH',
            'IQV', 'IRM', 'JBHT', 'JBL', 'JKHY', 'J', 'JNJ', 'JCI', 'JPM', 'JNPR',
            'K', 'KVUE', 'KDP', 'KEY', 'KEYS', 'KMB', 'KIM', 'KMI', 'KHC', 'KR',
            'LHX', 'LH', 'LRCX', 'LW', 'LVS', 'LDOS', 'LEN', 'LIN', 'LYV', 'LKQ',
            'LMT', 'L', 'LOW', 'LULU', 'LYB', 'MTB', 'MRO', 'MPC', 'MKTX', 'MAR',
            'MMC', 'MLM', 'MAS', 'MA', 'MTCH', 'MKC', 'MCD', 'MCK', 'MDT', 'MRK',
            'META', 'MET', 'MTD', 'MGM', 'MCHP', 'MU', 'MSFT', 'MAA', 'MRNA', 'MHK',
            'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MSCI',
            'NDAQ', 'NTAP', 'NFLX', 'NEM', 'NWSA', 'NWS', 'NEE', 'NKE', 'NI', 'NDSN',
            'NSC', 'NTRS', 'NOC', 'NCLH', 'NRG', 'NUE', 'NVDA', 'NVR', 'NXPI', 'ORLY',
            'OXY', 'ODFL', 'OMC', 'ON', 'OKE', 'ORCL', 'OTIS', 'PCAR', 'PKG', 'PANW',
            'PARA', 'PH', 'PAYX', 'PAYC', 'PYPL', 'PNR', 'PEP', 'PFE', 'PCG', 'PM',
            'PSX', 'PNW', 'PNC', 'POOL', 'PPG', 'PPL', 'PFG', 'PG', 'PGR', 'PLD',
            'PRU', 'PEG', 'PTC', 'PSA', 'PHM', 'QRVO', 'PWR', 'QCOM', 'DGX', 'RL',
            'RJF', 'RTX', 'O', 'REG', 'REGN', 'RF', 'RSG', 'RMD', 'RVTY', 'ROK',
            'ROL', 'ROP', 'ROST', 'RCL', 'SPGI', 'CRM', 'SBAC', 'SLB', 'STX', 'SRE',
            'NOW', 'SHW', 'SPG', 'SWKS', 'SJM', 'SNA', 'SOLV', 'SO', 'LUV', 'SWK',
            'SBUX', 'STT', 'STLD', 'STE', 'SYK', 'SMCI', 'SYF', 'SNPS', 'SYY', 'TMUS',
            'TROW', 'TTWO', 'TPR', 'TRGP', 'TGT', 'TEL', 'TDY', 'TFX', 'TER', 'TSLA',
            'TXN', 'TXT', 'TMO', 'TJX', 'TSCO', 'TT', 'TDG', 'TRV', 'TRMB', 'TFC',
            'TYL', 'TSN', 'USB', 'UBER', 'UDR', 'ULTA', 'UNP', 'UAL', 'UPS', 'URI',
            'UNH', 'UHS', 'VLO', 'VTR', 'VLTO', 'VRSN', 'VRSK', 'VZ', 'VRTX', 'VFC',
            'VTRS', 'VICI', 'V', 'VMC', 'WRB', 'GWW', 'WAB', 'WBA', 'WMT', 'DIS',
            'WBD', 'WM', 'WAT', 'WEC', 'WFC', 'WELL', 'WST', 'WDC', 'WRK', 'WY',
            'WHR', 'WMB', 'WTW', 'WYNN', 'XEL', 'XYL', 'YUM', 'ZBRA', 'ZBH', 'ZTS'
        ]
        
        print(f"  正在计算标普500真实广度 ({len(sp500_components)} 只成分股)...")
        above_200 = 0
        total = 0
        
        for i, sym in enumerate(sp500_components):
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="1y", interval="1d")
                if len(hist) >= 200:
                    ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
                    current = hist['Close'].iloc[-1]
                    if current > ma200:
                        above_200 += 1
                    total += 1
                time.sleep(0.03)
            except:
                pass
        
        if total > 0:
            breadth = (above_200 / total) * 100
            return round(breadth, 2)
        return None

    def get_ndx_breadth_real(self):
        """Calculate real Nasdaq 100 breadth using component stocks"""
        ndx_components = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'COST',
            'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'CMCSA', 'TMUS', 'INTC', 'INTU', 'AMGN',
            'QCOM', 'TXN', 'HON', 'AMAT', 'SBUX', 'ISRG', 'BKNG', 'GILD', 'ADI', 'MDLZ',
            'ADP', 'VRTX', 'REGN', 'LRCX', 'PANW', 'MU', 'PYPL', 'KLAC', 'SNPS', 'CDNS',
            'ABNB', 'MELI', 'CRWD', 'MAR', 'MRVL', 'ORLY', 'CSX', 'FTNT', 'ADSK', 'DASH',
            'WDAY', 'NXPI', 'ROP', 'PCAR', 'CPRT', 'AEP', 'PAYX', 'MNST', 'ODFL', 'ROST',
            'FAST', 'KDP', 'EA', 'VRSK', 'CTSH', 'BKR', 'GEHC', 'EXC', 'KHC', 'TEAM',
            'DXCM', 'CTAS', 'IDXX', 'LULU', 'CSGP', 'ON', 'TTWO', 'FANG', 'CDW', 'BIIB',
            'ANSS', 'GFS', 'DDOG', 'ZS', 'ILMN', 'MRNA', 'ARM', 'SMCI', 'TTD', 'WBD',
            'DLTR', 'MDB', 'CEG', 'CCEP', 'XEL', 'APP', 'TTD', 'TTD', 'TTD', 'TTD'
        ]
        ndx_components = list(dict.fromkeys(ndx_components))
        
        print(f"  正在计算纳斯达克100真实广度 ({len(ndx_components)} 只成分股)...")
        above_200 = 0
        total = 0
        
        for i, sym in enumerate(ndx_components):
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="1y", interval="1d")
                if len(hist) >= 200:
                    ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
                    current = hist['Close'].iloc[-1]
                    if current > ma200:
                        above_200 += 1
                    total += 1
                time.sleep(0.03)
            except:
                pass
        
        if total > 0:
            breadth = (above_200 / total) * 100
            return round(breadth, 2)
        return None

    def get_breadth_from_history(self, symbol):
        """
        Estimate breadth (% of stocks above MA200) using index position relative to MA200.
        Used as fallback when StockCharts scraping fails.
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5y", interval="1d")
            if hist.empty or len(hist) < 200:
                return None
            
            ma200 = hist['Close'].rolling(window=200).mean()
            current = float(hist['Close'].iloc[-1])
            current_ma = float(ma200.iloc[-1])
            
            if current_ma == 0 or pd.isna(current_ma):
                return None
            
            deviation_pct = ((current - current_ma) / current_ma) * 100
            
            # 使用更合理的估算公式，基于历史经验
            if deviation_pct > 0:
                # 当指数高于MA200时，广度增长较慢
                breadth = 50.0 + min(45.0, deviation_pct * 2.5)
            else:
                # 当指数低于MA200时，广度下降也较慢
                breadth = 50.0 - min(45.0, -deviation_pct * 2.5)
            
            # 确保在合理范围内
            breadth = max(5.0, min(95.0, breadth))
            return round(breadth, 2)
        except Exception as e:
            print(f"    {symbol} 广度估算失败: {str(e)}")
            return None

    def get_sp500_breadth_from_eoddata(self):
        try:
            response = self.session.get(self.BARCHART_SPY_URL, timeout=self.timeout)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            cells = soup.find_all('td')
            for cell in cells:
                if 'aboveMA200' in str(cell) or '> MA(200)' in str(cell):
                    text = cell.get_text().strip()
                    import re
                    match = re.search(r'(\d+\.?\d*)%', text)
                    if match:
                        return float(match.group(1))
            return None
        except Exception as e:
            return None

    def get_ndx_breadth_from_eoddata(self):
        try:
            response = self.session.get(self.BARCHART_NDX_URL, timeout=self.timeout)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            cells = soup.find_all('td')
            for cell in cells:
                if 'aboveMA200' in str(cell) or '> MA(200)' in str(cell):
                    text = cell.get_text().strip()
                    import re
                    match = re.search(r'(\d+\.?\d*)%', text)
                    if match:
                        return float(match.group(1))
            return None
        except Exception as e:
            return None

    def get_stockcharts_sp500_breadth(self):
        """从StockCharts获取标普500高于MA200比例"""
        try:
            print("  正在从 StockCharts 获取标普500 200日线比例...")
            response = self.session.get(self.STOCKCHARTS_SPXA200R_URL, timeout=self.timeout)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            import re
            text = soup.get_text()
            match = re.search(r'(\d+\.?\d*)%', text)
            if match:
                return float(match.group(1))
            return None
        except Exception as e:
            print(f"  StockCharts SPXA200R 获取失败: {str(e)}")
            return None

    def get_stockcharts_ndx_breadth(self):
        """从StockCharts获取纳斯达克100高于MA200比例"""
        try:
            print("  正在从 StockCharts 获取纳斯达克100 200日线比例...")
            response = self.session.get(self.STOCKCHARTS_NDXA200R_URL, timeout=self.timeout)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            import re
            text = soup.get_text()
            match = re.search(r'(\d+\.?\d*)%', text)
            if match:
                return float(match.group(1))
            return None
        except Exception as e:
            print(f"  StockCharts NDXA200R 获取失败: {str(e)}")
            return None

    def get_macromicro_ndx_ma200_breadth(self):
        """从MacroMicro获取纳斯达克100高于MA200比例
        
        由于MacroMicro有安全验证，这里提供两种方案：
        1. 尝试直接抓取（可能被拦截）
        2. 使用备用数据源（StockCharts）
        """
        try:
            print("  正在尝试从 MacroMicro 获取纳斯达克100 200日线比例...")
            
            # 方案1: 尝试直接抓取MacroMicro
            response = self.session.get(self.MACROMICRO_NDX_MA200_URL, timeout=self.timeout)
            
            if response.status_code != 200:
                print(f"  MacroMicro 请求失败: {response.status_code}")
                # 方案2: 使用备用数据源
                return self.get_stockcharts_ndx_breadth()
            
            # 检查是否被安全验证拦截
            if "安全验证" in response.text or "Cloudflare" in response.text:
                print("  MacroMicro 被安全验证拦截，使用备用数据源")
                return self.get_stockcharts_ndx_breadth()
            
            # 解析页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种解析方式
            # 方式1: 查找包含百分比的文本
            import re
            text = soup.get_text()
            
            # 查找类似 "65.2%" 这样的百分比数值
            matches = re.findall(r'(\d+\.?\d*)%', text)
            if matches:
                # 取最后一个匹配项（通常是当前值）
                for match in reversed(matches):
                    value = float(match)
                    if 0 <= value <= 100:  # 验证是合理的百分比
                        print(f"  从MacroMicro获取到纳斯达克100 200日线比例: {value}%")
                        return value
            
            # 方式2: 查找图表数据或API接口
            # MacroMicro通常使用图表显示数据，可能需要解析JavaScript或API调用
            
            print("  无法从MacroMicro页面解析数据，使用备用数据源")
            return self.get_stockcharts_ndx_breadth()
            
        except Exception as e:
            print(f"  MacroMicro 获取失败: {str(e)}")
            # 使用备用数据源
            return self.get_stockcharts_ndx_breadth()

    def get_credit_spread(self):
        try:
            response = requests.get(self.FRED_CREDIT_SPREAD_URL, timeout=self.timeout)
            if response.status_code != 200:
                return None
        except requests.exceptions.RequestException as e:
            return None

        try:
            text = response.text.strip()
            lines = [line for line in text.split('\n') if line.strip() and ',' in line]
            if not lines:
                return None
            last_line = lines[-1].strip()
            parts = last_line.split(',')
            if len(parts) >= 2:
                spread = float(parts[1].strip())
                return round(spread, 2)
        except Exception as e:
            pass

        return None

    def get_vix_term_ratio(self):
        print("  正在获取 VIX 和 VIX3M 数据...")
        vix_data = self._get_yahoo_symbol_data('^VIX')
        vix3m_data = self._get_yahoo_symbol_data('^VIX3M')
        if vix_data is None or vix3m_data is None:
            return None
        vix_price = vix_data['current_price']
        vix3m_price = vix3m_data['current_price']
        if vix3m_price == 0:
            return None
        ratio = vix_price / vix3m_price
        return round(ratio, 2)

    def get_tnx_ma50_diff(self):
        print("  正在获取 10年期美债收益率 (^TNX) 数据...")
        data = self._get_yahoo_symbol_data('^TNX')
        if data is None:
            return None
        close_prices = data['close_prices']
        current_price = data['current_price']
        if len(close_prices) < 50:
            return None
        ma50 = sum(close_prices[-50:]) / 50
        if ma50 == 0:
            return None
        diff_pct = ((current_price - ma50) / ma50) * 100
        return round(diff_pct, 2)

    def fetch_daily_pcr(self, ticker_symbol):
        """获取指定标的的Put/Call比率
        - 使用 Barchart 页面底部汇总数据
        - 返回 (volume_ratio, oi_ratio) 或 (None, None)
        
        :param ticker_symbol: 'SPY' 或 'QQQ'
        """
        print(f"  正在获取 {ticker_symbol} Put/Call 比率...")
        try:
            import re
            from bs4 import BeautifulSoup
            
            # 构建Barchart URL
            url = f"https://www.barchart.com/etfs-funds/quotes/{ticker_symbol}/put-call-ratios"
            
            # 获取页面
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                print(f"  {ticker_symbol} 页面请求失败: {response.status_code}")
                return None, None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            
            # 方法一：用正则直接匹配 Put/Call Open Interest Ratio
            oi_ratio_pattern = r'Put/Call Open Interest Ratio\s*([\d.]+)'
            oi_ratio_match = re.search(oi_ratio_pattern, page_text)
            
            if not oi_ratio_match:
                print(f"  {ticker_symbol} 未找到 Put/Call Open Interest Ratio")
                return None, None
            
            oi_ratio_from_page = float(oi_ratio_match.group(1))
            
            # 方法二：抓取 Put Open Interest Total 和 Call Open Interest Total
            # 匹配格式：Put Open Interest Total    11,570,726
            put_oi_pattern = r'Put Open Interest Total\s*([\d,]+)'
            call_oi_pattern = r'Call Open Interest Total\s*([\d,]+)'
            
            put_oi_match = re.search(put_oi_pattern, page_text)
            call_oi_match = re.search(call_oi_pattern, page_text)
            
            put_oi_total = None
            call_oi_total = None
            
            if put_oi_match and call_oi_match:
                put_oi_total = int(put_oi_match.group(1).replace(',', ''))
                call_oi_total = int(call_oi_match.group(1).replace(',', ''))
                oi_ratio_calculated = round(put_oi_total / call_oi_total, 2)
                
                # 校验计算值与页面显示值的误差
                if abs(oi_ratio_calculated - oi_ratio_from_page) > 0.01:
                    print(f"  [警告] {ticker_symbol} OI Ratio 校验失败：页面显示 {oi_ratio_from_page}，计算值 {oi_ratio_calculated}")
                else:
                    print(f"  {ticker_symbol} OI Ratio 抓取成功：{oi_ratio_calculated} (Put OI: {put_oi_total}, Call OI: {call_oi_total})")
            else:
                oi_ratio_calculated = oi_ratio_from_page
                print(f"  {ticker_symbol} OI Ratio 直接使用页面值：{oi_ratio_from_page}")
            
            # 抓取 Volume Ratio 作为返回值（虽然主逻辑用OI Ratio）
            volume_ratio = None
            volume_ratio_pattern = r'Put/Call Volume Ratio\s*([\d.]+)'
            volume_ratio_match = re.search(volume_ratio_pattern, page_text)
            if volume_ratio_match:
                volume_ratio = float(volume_ratio_match.group(1))
            
            # 合理区间校验
            valid_range = {
                'QQQ': (1.2, 2.5),
                'SPY': (1.8, 3.2)
            }
            
            if ticker_symbol in valid_range:
                min_val, max_val = valid_range[ticker_symbol]
                if not (min_val <= oi_ratio_calculated <= max_val):
                    print(f"  [警告] {ticker_symbol} OI Ratio 抓取值 {oi_ratio_calculated} 超出合理区间 [{min_val}, {max_val}]，疑似抓取了分期日单行数据，本次跳过写入")
                    return volume_ratio, None
            
            return volume_ratio, oi_ratio_calculated
            
        except Exception as e:
            print(f"  {ticker_symbol} PCR 抓取异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    def get_qqq_pcr(self):
        """获取纳斯达克100 QQQ的Put/Call比率（主信号）"""
        return self.fetch_daily_pcr("QQQ")

    def get_spy_pcr(self):
        """获取标普500 SPY的Put/Call比率（辅助信号）"""
        return self.fetch_daily_pcr("SPY")

    def get_on_rrp_data(self):
        """获取美联储隔夜逆回购余额
        数据来源：FRED API (RRPONTSYD)
        返回：当前值，偏离50日均百分比
        注意：季度末ON RRP会出现跳升（如从0.x跳到8-16），属于短期操作而非趋势变化，
        计算MA50时需排除这些异常值，否则偏离率会失真。
        """
        print("  正在获取 ON RRP 数据 (FRED)...")
        try:
            response = requests.get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=RRPONTSYD', timeout=10)
            if response.status_code != 200:
                return None, None
            text = response.text.strip()
            lines = [line for line in text.split('\n') if line.strip() and ',' in line][1:]
            if not lines or len(lines) < 50:
                return None, None
            all_values = []
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        val = float(parts[1].strip())
                        if val > 0:
                            all_values.append(val)
                    except:
                        continue
            if len(all_values) < 10:
                return None, None
            current = all_values[-1]
            normal_values = [v for v in all_values if v <= 5.0]
            if len(normal_values) >= 50:
                ma50 = sum(normal_values[-50:]) / 50
            elif len(normal_values) >= 10:
                ma50 = sum(normal_values[-min(len(normal_values), 30):]) / min(len(normal_values), 30)
            else:
                return round(current, 2), None
            if ma50 <= 0:
                return round(current, 2), None
            if current > 5.0:
                effective_current = normal_values[-1] if normal_values else current
            else:
                effective_current = current
            deviation = ((effective_current - ma50) / ma50) * 100
            return round(current, 2), round(deviation, 2)
        except Exception as e:
            print(f"    ON RRP获取失败: {str(e)}")
            return None, None

    def get_ndx_spx_ratio(self, ndx_data, spx_data):
        """计算纳斯达克100 vs 标普500相对强弱
        返回：当前比率，偏离20日均百分比
        """
        if ndx_data is None or spx_data is None:
            return None, None
        if len(ndx_data['close_prices']) < 20 or len(spx_data['close_prices']) < 20:
            return None, None
        ratios = []
        for ndx_close, spx_close in zip(ndx_data['close_prices'][-100:], spx_data['close_prices'][-100:]):
            ratios.append(ndx_close / spx_close)
        if len(ratios) < 20:
            return None, None
        current = ratios[-1]
        ma20 = sum(ratios[-20:]) / 20
        deviation = ((current - ma20) / ma20) * 100
        return round(current, 4), round(deviation, 2)

    def get_iwm_spy_ratio(self):
        """计算小盘股相对表现
        IWM/SPY比率，返回：当前比率，偏离20日均百分比
        """
        print("  正在获取 IWM/SPY 数据...")
        try:
            iwm_data = self._get_yahoo_symbol_data('IWM')
            spy_data = self._get_yahoo_symbol_data('SPY')
            if iwm_data is None or spy_data is None:
                return None, None
            if len(iwm_data['close_prices']) < 20 or len(spy_data['close_prices']) < 20:
                return None, None
            ratios = []
            for iwm_close, spy_close in zip(iwm_data['close_prices'][-100:], spy_data['close_prices'][-100:]):
                ratios.append(iwm_close / spy_close)
            if len(ratios) < 20:
                return None, None
            current = ratios[-1]
            ma20 = sum(ratios[-20:]) / 20
            deviation = ((current - ma20) / ma20) * 100
            return round(current, 4), round(deviation, 2)
        except Exception as e:
            print(f"    IWM/SPY比率获取失败: {str(e)}")
            return None, None

    def get_aaii_sentiment(self):
        """从AAII网站抓取最新情绪调查数据
        数据来源：https://www.aaii.com/sentimentsurvey/sent_results
        返回：bullish百分比, bearish百分比
        """
        print("  正在获取 AAII 情绪调查数据...")
        try:
            url = 'https://www.aaii.com/sentimentsurvey/sent_results'
            aaii_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            resp = self.session.get(url, headers=aaii_headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    header_row = rows[0] if rows else None
                    if header_row:
                        header_texts = [c.get_text(strip=True) for c in header_row.find_all(['td', 'th'])]
                        if 'Bullish' in header_texts and 'Bearish' in header_texts:
                            bull_idx = header_texts.index('Bullish')
                            bear_idx = header_texts.index('Bearish')
                            if len(rows) > 1:
                                data_row = rows[1]
                                cells = data_row.find_all('td')
                                if len(cells) > max(bull_idx, bear_idx):
                                    bull_text = cells[bull_idx].get_text(strip=True).replace('%', '')
                                    bear_text = cells[bear_idx].get_text(strip=True).replace('%', '')
                                    bullish = float(bull_text)
                                    bearish = float(bear_text)
                                    print(f"    AAII数据: Bullish={bullish}%, Bearish={bearish}%")
                                    return bullish, bearish
        except Exception as e:
            print(f"    AAII网页抓取失败: {str(e)}")

        print("    AAII数据获取失败，使用默认值")
        return None, None
