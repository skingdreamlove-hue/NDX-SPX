import requests
from bs4 import BeautifulSoup
import yfinance as yf
import re
import time
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def fetch_from_yfinance():
    """来源7：Yahoo Finance 统计接口"""
    try:
        logging.info("测试来源7：Yahoo Finance SPXA200R/NDXA200R")
        
        # 尝试获取SPXA200R
        try:
            spx_breadth = yf.download('SPXA200R', period='5d', interval='1d', progress=False)
            if not spx_breadth.empty:
                spx_ratio = spx_breadth['Close'].iloc[-1]
                logging.info(f"SPXA200R最新值: {spx_ratio}")
            else:
                spx_ratio = None
                logging.warning("SPXA200R无数据")
        except Exception as e:
            spx_ratio = None
            logging.warning(f"SPXA200R获取失败: {e}")
        
        # 尝试获取NDXA200R
        try:
            ndx_breadth = yf.download('NDXA200R', period='5d', interval='1d', progress=False)
            if not ndx_breadth.empty:
                ndx_ratio = ndx_breadth['Close'].iloc[-1]
                logging.info(f"NDXA200R最新值: {ndx_ratio}")
            else:
                ndx_ratio = None
                logging.warning("NDXA200R无数据")
        except Exception as e:
            ndx_ratio = None
            logging.warning(f"NDXA200R获取失败: {e}")
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Yahoo Finance整体失败: {e}")
        return None, None

def fetch_from_barchart():
    """来源1：Barchart"""
    try:
        logging.info("测试来源1：Barchart")
        
        # NDX URL
        ndx_url = "https://www.barchart.com/indices/nasdaq-100-stocks/most-overbought"
        response = requests.get(ndx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Barchart NDX请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 搜索"Above 200-Day MA"相关内容
        ndx_ratio = None
        text = soup.get_text()
        
        # 尝试多种匹配方式
        patterns = [
            r'(\d+\.?\d*)%\s*Above\s*200-Day\s*MA',
            r'Above\s*200-Day\s*MA.*?(\d+\.?\d*)%',
            r'200-Day\s*MA.*?(\d+\.?\d*)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ndx_ratio = float(match.group(1))
                logging.info(f"Barchart NDX匹配到: {ndx_ratio}%")
                break
        
        # SPX URL
        spx_url = "https://www.barchart.com/indices/sp-500-stocks/most-overbought"
        response = requests.get(spx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Barchart SPX请求失败: {response.status_code}")
            return ndx_ratio, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        spx_ratio = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                spx_ratio = float(match.group(1))
                logging.info(f"Barchart SPX匹配到: {spx_ratio}%")
                break
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Barchart失败: {e}")
        return None, None

def fetch_from_finviz():
    """来源2：Finviz"""
    try:
        logging.info("测试来源2：Finviz")
        
        # NDX URL
        ndx_url = "https://finviz.com/screener.ashx?v=111&f=idx_ndx,ta_sma200_pa&ft=4"
        response = requests.get(ndx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Finviz NDX请求失败: {response.status_code}")
            return None, None
        
        # 查找"Total: XXX"
        text = response.text
        match = re.search(r'Total:\s*(\d+)', text)
        
        if match:
            ndx_count = int(match.group(1))
            ndx_ratio = (ndx_count / 100) * 100  # NDX有100只成分股
            logging.info(f"Finviz NDX: {ndx_count}只股票高于200日线 ({ndx_ratio}%)")
        else:
            ndx_ratio = None
            logging.warning("Finviz NDX未找到Total数量")
        
        time.sleep(3)  # Finviz访问频率限制
        
        # SPX URL
        spx_url = "https://finviz.com/screener.ashx?v=111&f=idx_sp500,ta_sma200_pa&ft=4"
        response = requests.get(spx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Finviz SPX请求失败: {response.status_code}")
            return ndx_ratio, None
        
        text = response.text
        match = re.search(r'Total:\s*(\d+)', text)
        
        if match:
            spx_count = int(match.group(1))
            spx_ratio = (spx_count / 500) * 100  # SPX有500只成分股
            logging.info(f"Finviz SPX: {spx_count}只股票高于200日线 ({spx_ratio}%)")
        else:
            spx_ratio = None
            logging.warning("Finviz SPX未找到Total数量")
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Finviz失败: {e}")
        return None, None

def fetch_from_investors():
    """来源3：MarketSmith / Investors.com"""
    try:
        logging.info("测试来源3：Investors.com")
        
        url = "https://www.investors.com/market-trend/stock-market-today/"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Investors.com请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索200-day相关数据
        patterns = [
            r'(\d+\.?\d*)%\s*of\s*S&P\s*500\s*stocks\s*above\s*their\s*200-day',
            r'(\d+\.?\d*)%\s*above\s*200.day',
            r'200.day.*?(\d+\.?\d*)%'
        ]
        
        ndx_ratio = None
        spx_ratio = None
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches) >= 2:
                    spx_ratio = float(matches[0])
                    ndx_ratio = float(matches[1])
                    logging.info(f"Investors.com SPX: {spx_ratio}%, NDX: {ndx_ratio}%")
                    break
                elif len(matches) == 1:
                    spx_ratio = float(matches[0])
                    logging.info(f"Investors.com SPX: {spx_ratio}%")
                    break
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Investors.com失败: {e}")
        return None, None

def fetch_from_optuma():
    """来源4：Optuma"""
    try:
        logging.info("测试来源4：Optuma")
        
        # 尝试多个可能的API端点
        urls = [
            "https://charts.optuma.com/api/breadth?index=SPX&period=200",
            "https://charts.optuma.com/api/breadth?index=NDX&period=200"
        ]
        
        spx_ratio = None
        ndx_ratio = None
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # 解析JSON结构
                    if 'value' in data:
                        ratio = float(data['value'])
                        if 'SPX' in url:
                            spx_ratio = ratio
                            logging.info(f"Optuma SPX: {spx_ratio}%")
                        elif 'NDX' in url:
                            ndx_ratio = ratio
                            logging.info(f"Optuma NDX: {ndx_ratio}%")
            except:
                continue
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Optuma失败: {e}")
        return None, None

def fetch_from_stockcharts():
    """来源5：Stockcharts"""
    try:
        logging.info("测试来源5：Stockcharts")
        
        # NDX URL
        ndx_url = "https://stockcharts.com/h-sc/ui?s=NDXA200R"
        response = requests.get(ndx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Stockcharts NDX请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索最新数值
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            ndx_ratio = float(match.group(1))
            logging.info(f"Stockcharts NDX: {ndx_ratio}%")
        else:
            ndx_ratio = None
            logging.warning("Stockcharts NDX未找到百分比")
        
        # SPX URL
        spx_url = "https://stockcharts.com/h-sc/ui?s=SPXA200R"
        response = requests.get(spx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Stockcharts SPX请求失败: {response.status_code}")
            return ndx_ratio, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            spx_ratio = float(match.group(1))
            logging.info(f"Stockcharts SPX: {spx_ratio}%")
        else:
            spx_ratio = None
            logging.warning("Stockcharts SPX未找到百分比")
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Stockcharts失败: {e}")
        return None, None

def fetch_from_fidelity():
    """来源6：Fidelity"""
    try:
        logging.info("测试来源6：Fidelity")
        
        url = "https://eresearch.fidelity.com/eresearch/markets_sectors/sectors/sectors_in_market.jhtml"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Fidelity请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索200-day相关数据
        patterns = [
            r'(\d+\.?\d*)%\s*above\s*200.day',
            r'200.day.*?(\d+\.?\d*)%'
        ]
        
        ndx_ratio = None
        spx_ratio = None
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches) >= 2:
                    spx_ratio = float(matches[0])
                    ndx_ratio = float(matches[1])
                    logging.info(f"Fidelity SPX: {spx_ratio}%, NDX: {ndx_ratio}%")
                    break
                elif len(matches) == 1:
                    spx_ratio = float(matches[0])
                    logging.info(f"Fidelity SPX: {spx_ratio}%")
                    break
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Fidelity失败: {e}")
        return None, None

def fetch_from_wsj():
    """来源10：WSJ"""
    try:
        logging.info("测试来源10：WSJ")
        
        url = "https://www.wsj.com/market-data/stocks/us/movers"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"WSJ请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索above和200相关数据
        patterns = [
            r'(\d+\.?\d*)%\s*above\s*200',
            r'200.*?(\d+\.?\d*)%'
        ]
        
        ndx_ratio = None
        spx_ratio = None
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches) >= 2:
                    spx_ratio = float(matches[0])
                    ndx_ratio = float(matches[1])
                    logging.info(f"WSJ SPX: {spx_ratio}%, NDX: {ndx_ratio}%")
                    break
                elif len(matches) == 1:
                    spx_ratio = float(matches[0])
                    logging.info(f"WSJ SPX: {spx_ratio}%")
                    break
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"WSJ失败: {e}")
        return None, None

def fetch_from_alphaquery():
    """来源11：Alphaquery"""
    try:
        logging.info("测试来源11：Alphaquery")
        
        # NDX URL
        ndx_url = "https://www.alphaquery.com/stock/QQQ/volatility-option-statistics/90-day/historical-volatility"
        response = requests.get(ndx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Alphaquery NDX请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索"% Above 200-day MA"
        match = re.search(r'(\d+\.?\d*)%\s*Above\s*200-day\s*MA', text, re.IGNORECASE)
        if match:
            ndx_ratio = float(match.group(1))
            logging.info(f"Alphaquery NDX: {ndx_ratio}%")
        else:
            ndx_ratio = None
            logging.warning("Alphaquery NDX未找到数据")
        
        # SPX URL
        spx_url = "https://www.alphaquery.com/stock/SPY/all-indicator-panel"
        response = requests.get(spx_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Alphaquery SPX请求失败: {response.status_code}")
            return ndx_ratio, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        match = re.search(r'(\d+\.?\d*)%\s*Above\s*200-day\s*MA', text, re.IGNORECASE)
        if match:
            spx_ratio = float(match.group(1))
            logging.info(f"Alphaquery SPX: {spx_ratio}%")
        else:
            spx_ratio = None
            logging.warning("Alphaquery SPX未找到数据")
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"Alphaquery失败: {e}")
        return None, None

def fetch_from_etf():
    """来源12：ETF.com"""
    try:
        logging.info("测试来源12：ETF.com")
        
        # QQQ URL
        qqq_url = "https://www.etf.com/QQQ"
        response = requests.get(qqq_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"ETF.com QQQ请求失败: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 搜索200-day相关数据
        match = re.search(r'(\d+\.?\d*)%\s*above\s*200', text, re.IGNORECASE)
        if match:
            ndx_ratio = float(match.group(1))
            logging.info(f"ETF.com NDX: {ndx_ratio}%")
        else:
            ndx_ratio = None
            logging.warning("ETF.com NDX未找到数据")
        
        # SPY URL
        spy_url = "https://www.etf.com/SPY"
        response = requests.get(spy_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"ETF.com SPY请求失败: {response.status_code}")
            return ndx_ratio, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        match = re.search(r'(\d+\.?\d*)%\s*above\s*200', text, re.IGNORECASE)
        if match:
            spx_ratio = float(match.group(1))
            logging.info(f"ETF.com SPX: {spx_ratio}%")
        else:
            spx_ratio = None
            logging.warning("ETF.com SPX未找到数据")
        
        return ndx_ratio, spx_ratio
        
    except Exception as e:
        logging.error(f"ETF.com失败: {e}")
        return None, None

def test_all_sources():
    """测试所有数据源"""
    results = {}
    
    # 按优先级顺序测试
    sources = [
        ("yfinance", fetch_from_yfinance),      # 来源7
        ("barchart", fetch_from_barchart),     # 来源1
        ("finviz", fetch_from_finviz),         # 来源2
        ("investors", fetch_from_investors),   # 来源3
        ("optuma", fetch_from_optuma),         # 来源4
        ("stockcharts", fetch_from_stockcharts), # 来源5
        ("fidelity", fetch_from_fidelity),     # 来源6
        ("wsj", fetch_from_wsj),               # 来源10
        ("alphaquery", fetch_from_alphaquery), # 来源11
        ("etf", fetch_from_etf),               # 来源12
    ]
    
    for name, func in sources:
        try:
            logging.info(f"\n=== 测试数据源：{name} ===")
            ndx_ratio, spx_ratio = func()
            
            results[name] = {
                'ndx_ratio': ndx_ratio,
                'spx_ratio': spx_ratio,
                'success': ndx_ratio is not None or spx_ratio is not None
            }
            
            if ndx_ratio is not None and spx_ratio is not None:
                logging.info(f"[成功] {name} → NDX:{ndx_ratio}% SPX:{spx_ratio}%")
            elif ndx_ratio is not None:
                logging.info(f"[部分成功] {name} → NDX:{ndx_ratio}% SPX:无数据")
            elif spx_ratio is not None:
                logging.info(f"[部分成功] {name} → NDX:无数据 SPX:{spx_ratio}%")
            else:
                logging.warning(f"[失败] {name} → 无有效数据")
            
            time.sleep(2)  # 避免请求过于频繁
            
        except Exception as e:
            logging.error(f"[异常] {name} → {str(e)}")
            results[name] = {
                'ndx_ratio': None,
                'spx_ratio': None,
                'success': False,
                'error': str(e)
            }
            time.sleep(2)
    
    return results

if __name__ == "__main__":
    print("开始测试所有数据源...")
    print("=" * 60)
    
    results = test_all_sources()
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    successful_sources = []
    for name, result in results.items():
        if result['success']:
            successful_sources.append(name)
            print(f"✓ {name}: NDX={result['ndx_ratio']}% SPX={result['spx_ratio']}%")
        else:
            print(f"✗ {name}: 失败")
    
    print(f"\n成功的数据源数量: {len(successful_sources)}/{len(results)}")
    print(f"成功的数据源: {', '.join(successful_sources)}")
    
    # 保存详细结果到文件
    with open('breadth_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n详细结果已保存到: breadth_test_results.json")