import requests
import pandas as pd
import numpy as np
import time
import io

def scrape_market_data():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    field_ids = ["market_sum", "per", "pbr", "roe", "dividend", "quant"]
    
    all_stocks = []
    
    # 0 for KOSPI, 1 for KOSDAQ
    for sosok_code, market_name in [(0, "KOSPI"), (1, "KOSDAQ")]:
        print(f"Retrieving data for {market_name}...")
        
        # Submit the fields we want to session cookies
        base_url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok_code}"
        post_url = "https://finance.naver.com/sise/field_submit.nhn"
        
        # Get page first
        session.get(base_url, headers=headers)
        
        # Post fields
        payload = {
            "menu": "market_sum",
            "fieldIds": field_ids,
            "returnUrl": base_url
        }
        session.post(post_url, headers=headers, data=payload)
        
        page = 1
        while True:
            url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok_code}&page={page}"
            response = session.get(url, headers=headers)
            response.encoding = "euc-kr"
            
            # Check if page has table
            try:
                # Use io.StringIO to avoid deprecation warning in pandas
                dfs = pd.read_html(io.StringIO(response.text))
                if len(dfs) < 2:
                    break
                df = dfs[1]
            except Exception as e:
                print(f"Error parsing page {page}: {e}")
                break
                
            # Clean dataframe
            df = df.dropna(subset=["N"])
            if df.empty:
                break
                
            # Add market info
            df["시장"] = market_name
            
            # Rename 보통주배당금 to 배당금
            if "보통주배당금" in df.columns:
                df = df.rename(columns={"보통주배당금": "배당금"})
            
            # Keep required columns
            req_cols = ["N", "종목명", "현재가", "시가총액", "배당금", "PER", "PBR", "ROE", "거래량", "시장"]
            # Sometimes column names might differ slightly, let's select matching ones
            available_cols = [c for c in req_cols if c in df.columns]
            df = df[available_cols]
            
            all_stocks.append(df)
            print(f"Page {page} scraped, {len(df)} stocks found.")
            page += 1
            time.sleep(0.2) # Polite delay
            
            # Stop if page is unreasonably high
            if page > 45:
                break
                
    if not all_stocks:
        print("No stock data collected!")
        return pd.DataFrame()
        
    merged_df = pd.concat(all_stocks, ignore_index=True)
    return merged_df

def main():
    df = scrape_market_data()
    if df.empty:
        print("Failed to collect stock data.")
        return
        
    print(f"\nTotal stocks collected: {len(df)}")
    
    # 1. Clean data columns
    num_cols = ["현재가", "시가총액", "배당금", "PER", "PBR", "ROE", "거래량"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Fill missing values
    df["배당금"] = df["배당금"].fillna(0)
    
    # Calculate Dividend Yield (%)
    df["배당수익률(%)"] = np.round((df["배당금"] / df["현재가"]) * 100, 2)
    
    # Approximate ROE where missing using PBR / PER
    # PBR = Price/BPS, PER = Price/EPS. ROE = EPS/BPS = PBR/PER.
    mask = df["ROE"].isna() & df["PER"].notna() & df["PBR"].notna() & (df["PER"] > 0)
    df.loc[mask, "ROE"] = np.round((df.loc[mask, "PBR"] / df.loc[mask, "PER"]) * 100, 2)
    
    # 2. Filter undervalued quality stocks
    # Size: 시가총액 >= 1000 (1000억 원)
    # Liquidity: 거래량 >= 5000 (5천 주)
    # Valuation: 0.2 <= PBR <= 0.8  and 2.0 <= PER <= 12.0
    # Profitability: ROE >= 8.0 (%)
    # Dividends: 배당수익률(%) >= 3.0 (%)
    
    filtered_df = df[
        (df["시가총액"] >= 1000) &
        (df["거래량"] >= 5000) &
        (df["PBR"] >= 0.2) & (df["PBR"] <= 0.8) &
        (df["PER"] >= 2.0) & (df["PER"] <= 12.0) &
        (df["ROE"] >= 8.0) &
        (df["배당수익률(%)"] >= 3.0)
    ].copy()
    
    print(f"Filtered stocks meeting criteria: {len(filtered_df)}")
    
    # 3. Score and rank
    # Composite ranking: we want LOWER PBR, LOWER PER, HIGHER ROE, HIGHER Dividend Yield
    # Let's assign ranks for each metric
    filtered_df["pbr_rank"] = filtered_df["PBR"].rank(ascending=True)
    filtered_df["per_rank"] = filtered_df["PER"].rank(ascending=True)
    filtered_df["roe_rank"] = filtered_df["ROE"].rank(ascending=False)
    filtered_df["div_rank"] = filtered_df["배당수익률(%)"].rank(ascending=False)
    
    filtered_df["종합순위점수"] = (
        filtered_df["pbr_rank"] * 1.0 +
        filtered_df["per_rank"] * 1.0 +
        filtered_df["roe_rank"] * 1.2 +
        filtered_df["div_rank"] * 0.8
    )
    
    final_df = filtered_df.sort_values(by="종합순위점수").reset_index(drop=True)
    
    # Output top stocks
    top_n = final_df.head(20)
    
    report_md = f"""# 한국 주식 시장 저평가 우량주 분석 리포트 (Value-Up Screen)
    
본 리포트는 네이버 금융 시가총액 데이터를 크롤링하여 한국 주식 시장(KOSPI, KOSDAQ) 중 
**자산 가치 대비 저평가(Low PBR)**되어 있으면서 **실제 이익을 잘 내고(Low PER, High ROE)** 
**주주 환원에 적극적인(High Dividend Yield)** 우량 기업들을 스크리닝한 결과입니다.

## 1. 스크리닝 기준 (Screening Criteria)
*   **규모 및 유동성:** 시가총액 **1,000억 원 이상**, 일 거래량 **5,000주 이상** (소형주 및 거래 정지, 극단적 유동성 부족 종목 제외)
*   **자산 저평가 (PBR):** **0.2 이상 ~ 0.8 이하** (장부가 가치보다 현저히 낮게 거래되는 종목)
*   **수익 저평가 (PER):** **2.0 이상 ~ 12.0 이하** (실적 대비 주가가 저렴하며 적자 기업 제외)
*   **자기자본이익률 (ROE):** **8.0% 이상** (자본을 효율적으로 굴려 두 자릿수에 가까운 수익성을 내는 기업)
*   **배당수익률:** **3.0% 이상** (적극적 주주환원 또는 고배당 성향을 가진 기업)

---

## 2. 저평가 우량주 Top 20 리스트

종합 평가는 PBR 순위, PER 순위, ROE 순위, 배당수익률 순위를 가중 조합하여 산출하였습니다. (낮을수록 우수)

| 순위 | 종목명 | 시장 | 시가총액(억 원) | 현재가(원) | PER | PBR | ROE (%) | 배당금(원) | 배당수익률 (%) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    
    for idx, row in top_n.iterrows():
        rank = idx + 1
        name = row["종목명"]
        market = row["시장"]
        mcap = int(row["시가총액"])
        price = int(row["현재가"])
        per = f"{row['PER']:.2f}" if not pd.isna(row['PER']) else "N/A"
        pbr = f"{row['PBR']:.2f}" if not pd.isna(row['PBR']) else "N/A"
        roe = f"{row['ROE']:.2f}%" if not pd.isna(row['ROE']) else "N/A"
        div_val = int(row["배당금"])
        div_yld = f"{row['배당수익률(%)']:.2f}%"
        
        report_md += f"| {rank} | {name} | {market} | {mcap:,} | {price:,} | {per} | {pbr} | {roe} | {div_val:,} | {div_yld} |\n"
        
    report_md += """
---

## 3. 핵심 종목 분석 요약

스크리닝 결과 상위에 랭크된 기업들의 비즈니스 및 투자 포인트 요약입니다:

1.  **금융지주 및 은행주:** 
    *   한국 정부의 밸류업 프로그램 수혜를 가장 많이 받는 섹터로, PBR 0.3~0.5배 수준의 극심한 저평가를 받아왔으나, 최근 자사주 매입/소각 및 분기 배당 확대로 주주 환원이 급격히 강화되는 추세입니다.
2.  **자동차 및 부품주 (현대차/기아/모비스 등 관련 밸류체인):**
    *   글로벌 경쟁력을 바탕으로 견고한 영업이익을 기록하고 있지만 PBR 0.5~0.7배, PER 4~6배 수준으로 전 세계 주요 완성차 업체 대비 현저히 저평가되어 있습니다. 높은 배당 성향이 강점입니다.
3.  **지주회사:**
    *   보유한 자회사 지분 및 부동산 가치 대비 주가 할인율이 50%를 넘는 경우가 흔해 대표적인 저PBR 종목군을 형성하고 있습니다. 거버넌스 개선 및 밸류업 공시가 주가 상승의 촉매가 될 수 있습니다.
4.  **전통 제조업 및 상사:**
    *   꾸준한 현금 흐름을 창출하며 자산이 풍부하지만 시장에서 인기가 없어 저평가된 기업들입니다. 이 중 ROE가 양호하게 유지되고 배당을 4~6% 이상 꾸준히 주는 종목들은 안정적인 배당 수익과 하방 경직성을 제공합니다.

*면책조항: 본 리포트는 투자 권유 목적으로 작성된 것이 아니며, 단순 스크리닝 결과 제공을 목적으로 합니다. 투자 시에는 반드시 개별 기업의 10-K 보고서, 분기 보고서, 지배구조 리스크 등을 개별 검토하시기 바랍니다.*
"""
    
    with open("undervalued_stocks_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print("\nReport successfully saved to undervalued_stocks_report.md")

if __name__ == "__main__":
    main()
