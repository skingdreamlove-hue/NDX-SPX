import requests
from bs4 import BeautifulSoup
import json
import time
import re

FUND_INFO = {
    "270042": {"name": "广发纳斯达克100ETF联接人民币(QDII)A", "type": "A", "purchase": "1.30%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.13%", "category": "nasdaq"},
    "040046": {"name": "华安纳斯达克100ETF联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.12%", "category": "nasdaq"},
    "018043": {"name": "天弘纳斯达克100指数发起(QDII)A", "type": "A", "purchase": "1.00%", "management": "0.50%", "custody": "0.10%", "sales": "0%", "total": "0.70%", "category": "nasdaq"},
    "016532": {"name": "嘉实纳斯达克100ETF发起联接(QDII)人民币A", "type": "A", "purchase": "1.00%", "management": "0.50%", "custody": "0.10%", "sales": "0%", "total": "0.70%", "category": "nasdaq"},
    "000834": {"name": "大成纳斯达克100ETF联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.12%", "category": "nasdaq"},
    "160213": {"name": "国泰纳斯达克100指数(QDII)", "type": "A", "purchase": "1.50%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.15%", "category": "nasdaq"},
    "016452": {"name": "南方纳斯达克100指数发起(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "nasdaq"},
    "019547": {"name": "招商纳斯达克100ETF发起式联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "nasdaq"},
    "016055": {"name": "博时纳斯达克100ETF发起式联接(QDII)人民币A", "type": "A", "purchase": "1.00%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.75%", "category": "nasdaq"},
    "539001": {"name": "建信纳斯达克100指数(QDII)人民币A", "type": "A", "purchase": "1.20%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.12%", "category": "nasdaq"},
    "019524": {"name": "华泰柏瑞纳斯达克100ETF发起式联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "nasdaq"},
    "161130": {"name": "易方达纳斯达克100LOF", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.10%", "sales": "0%", "total": "0.72%", "category": "nasdaq"},
    "018966": {"name": "汇添富纳斯达克100ETF发起式联接(QDII)人民币A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "nasdaq"},
    "019172": {"name": "摩根纳斯达克100指数(QDII)人民币A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.10%", "sales": "0%", "total": "0.72%", "category": "nasdaq"},
    "019736": {"name": "宝盈纳斯达克100指数发起(QDII)人民币", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "nasdaq"},
    "019441": {"name": "万家纳斯达克100指数发起式(QDII)A", "type": "A", "purchase": "1.00%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.75%", "category": "nasdaq"},
    "015299": {"name": "华夏纳斯达克100ETF发起式联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.60%", "custody": "0.20%", "sales": "0%", "total": "0.92%", "category": "nasdaq"},
    "006479": {"name": "广发纳斯达克100ETF联接人民币(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.80%", "custody": "0.20%", "sales": "0.20%", "total": "1.20%", "category": "nasdaq"},
    "014978": {"name": "华安纳斯达克100ETF联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.60%", "custody": "0.20%", "sales": "0.20%", "total": "1.00%", "category": "nasdaq"},
    "018044": {"name": "天弘纳斯达克100指数发起(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.10%", "sales": "0.20%", "total": "0.80%", "category": "nasdaq"},
    "016453": {"name": "南方纳斯达克100指数发起C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.10%", "total": "0.75%", "category": "nasdaq"},
    "008971": {"name": "大成纳斯达克100ETF联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.80%", "custody": "0.20%", "sales": "0.30%", "total": "1.30%", "category": "nasdaq"},
    "016533": {"name": "嘉实纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.10%", "sales": "0.25%", "total": "0.85%", "category": "nasdaq"},
    "016057": {"name": "博时纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.30%", "total": "0.95%", "category": "nasdaq"},
    "012752": {"name": "建信纳斯达克100指数(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.80%", "custody": "0.20%", "sales": "0.30%", "total": "1.30%", "category": "nasdaq"},
    "019525": {"name": "华泰柏瑞纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.25%", "total": "0.90%", "category": "nasdaq"},
    "018967": {"name": "汇添富纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.40%", "total": "1.05%", "category": "nasdaq"},
    "019173": {"name": "摩根纳斯达克100指数(QDII)人民币C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.10%", "sales": "0.30%", "total": "0.90%", "category": "nasdaq"},
    "019737": {"name": "宝盈纳斯达克100指数发起(QDII)人民币C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.10%", "sales": "0.25%", "total": "0.85%", "category": "nasdaq"},
    "019442": {"name": "万家纳斯达克100指数发起式(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.20%", "total": "0.85%", "category": "nasdaq"},
    "015300": {"name": "华夏纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.60%", "custody": "0.20%", "sales": "0.30%", "total": "1.10%", "category": "nasdaq"},
    "050025": {"name": "博时标普500ETF联接(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.60%", "custody": "0.20%", "sales": "0%", "total": "0.92%", "category": "sp500"},
    "017641": {"name": "摩根标普500指数(QDII)A", "type": "A", "purchase": "1.20%", "management": "0.50%", "custody": "0.15%", "sales": "0%", "total": "0.77%", "category": "sp500"},
    "161125": {"name": "易方达标普500指数LOF", "type": "A", "purchase": "1.20%", "management": "0.80%", "custody": "0.20%", "sales": "0%", "total": "1.12%", "category": "sp500"},
    "017028": {"name": "国泰标普500ETF发起式联接(QDII)A", "type": "A", "purchase": "1.00%", "management": "0.60%", "custody": "0.15%", "sales": "0%", "total": "0.85%", "category": "sp500"},
    "006075": {"name": "博时标普500ETF联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.60%", "custody": "0.20%", "sales": "0.35%", "total": "1.15%", "category": "sp500"},
    "019305": {"name": "摩根标普500指数(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.30%", "total": "0.95%", "category": "sp500"},
    "012860": {"name": "易方达标普500指数(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.80%", "custody": "0.20%", "sales": "0.35%", "total": "1.35%", "category": "sp500"},
    "017030": {"name": "国泰标普500ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.60%", "custody": "0.15%", "sales": "0.30%", "total": "1.05%", "category": "sp500"},
    "019548": {"name": "招商纳斯达克100ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.15%", "sales": "0.40%", "total": "1.05%", "category": "nasdaq"},
    "012870": {"name": "易方达纳斯达克100ETF联接(QDII-LOF)C(人民币)", "type": "C", "purchase": "0.00%", "management": "0.50%", "custody": "0.10%", "sales": "0.30%", "total": "0.90%", "category": "nasdaq"},
    "018064": {"name": "华夏标普500ETF发起式联接(QDII)A(人民币)", "type": "A", "purchase": "1.20%", "management": "0.60%", "custody": "0.15%", "sales": "0%", "total": "0.76%", "category": "sp500"},
    "018065": {"name": "华夏标普500ETF发起式联接(QDII)C", "type": "C", "purchase": "0.00%", "management": "0.60%", "custody": "0.15%", "sales": "0.30%", "total": "1.05%", "category": "sp500"},
}

result_data = []

print("开始爬取纳斯达克100和标普500场外基金数据...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive"
}

session = requests.Session()
session.headers.update(headers)

all_codes = list(FUND_INFO.keys())
total = len(all_codes)
print(f"总共需要爬取 {total} 只基金")

for idx, code in enumerate(all_codes, 1):
    try:
        print(f"[{idx}/{total}] 正在爬取基金 {code} ...")

        url = f"https://fund.eastmoney.com/{code}.html"
        response = session.get(url, timeout=8)
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        fund_name = FUND_INFO[code]["name"]

        nav_data = "N/A"
        daily_change = "N/A"
        nav_element = soup.find("div", class_="dataOfFund")
        if nav_element:
            nav_span = nav_element.find("span", class_="ui-font-large ui-color-red")
            if nav_span:
                nav_data = nav_span.text.strip()
            else:
                nav_span = nav_element.find("span", class_="ui-font-large")
                if nav_span:
                    nav_data = nav_span.text.strip()
            change_span = nav_element.find("span", class_="ui-font-middle ui-color-red")
            if change_span:
                daily_change = change_span.text.strip()
            else:
                change_span = nav_element.find("span", class_="ui-font-middle")
                if change_span:
                    daily_change = change_span.text.strip()

        nav_date = "N/A"
        date_element = soup.find("div", class_="dataOfFund")
        if date_element:
            date_text = date_element.text
            if "更新时间" in date_text:
                nav_date = date_text.split("：")[-1].strip()
            elif "净值日期" in date_text:
                nav_date = date_text.split("：")[-1].strip()

        trade_status = "N/A"
        status_elements = soup.find_all(string=lambda text: "交易状态" in text if text else False)
        for element in status_elements:
            parent = element.parent
            if parent:
                next_sibling = parent.next_sibling
                if next_sibling:
                    trade_status = next_sibling.text.strip()
                    break
                parent_next = parent.find_next_sibling()
                if parent_next:
                    trade_status = parent_next.text.strip()
                    break

        yearly_return = "N/A"
        html_text = response.text

        yearly_match = re.search(r'<span>近1年[：:]\s*</span><span[^>]*>([-+]?\d+\.\d+%)</span>', html_text)
        if yearly_match:
            yearly_return = yearly_match.group(1)

        if yearly_return == "N/A":
            yearly_match = re.search(r'<span>近1年</span>\s*<span[^>]*>([-+]?\d+\.\d+%)</span>', html_text)
            if yearly_match:
                yearly_return = yearly_match.group(1)

        if yearly_return == "N/A":
            yearly_match = re.search(r'<div>近1年</div></th><td[^>]*><div[^>]*>([-+]?\d+\.\d+%)</div></td>', html_text)
            if yearly_match:
                yearly_return = yearly_match.group(1)

        if yearly_return == "N/A":
            for span in soup.find_all('span', string=lambda text: text and '近1年' in text):
                next_span = span.find_next_sibling('span')
                if next_span and next_span.string and '%' in next_span.string:
                    yearly_return = next_span.string.strip()
                    break

        info = FUND_INFO[code]
        fund_data = {
            "基金代码": code,
            "基金名称": fund_name,
            "类型": info["type"],
            "最新净值": nav_data,
            "日涨跌幅": daily_change,
            "净值日期": nav_date,
            "交易状态": trade_status,
            "购买手续费": info["purchase"],
            "管理费率": info["management"],
            "托管费率": info["custody"],
            "销售服务费": info["sales"],
            "合计费率": info["total"],
            "近1年": yearly_return,
            "链接": url,
            "分类": info["category"]
        }

        result_data.append(fund_data)
        print(f"  OK: {fund_name} | 近1年: {yearly_return} | 合计费率:{info['total']}")

        time.sleep(0.5)

    except Exception as e:
        print(f"  FAIL: {e}")
        time.sleep(1)

if result_data:
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(BASE_DIR, "real_fund_data.json")
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"\n成功抓取 {len(result_data)}/{total} 只基金数据")
    print("数据已保存到 real_fund_data.json")
else:
    print("\n未抓取到任何数据，请检查网络连接或重试")
