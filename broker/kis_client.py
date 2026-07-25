"""
한국투자증권(KIS) Open API REST 클라이언트.

⚠️ 실행 전 필수 확인:
  이 파일의 TR_ID(FHKST01010100, FHKST03010200, TTTC0802U 등)는 KIS Developers
  공식 문서(https://apiportal.koreainvestment.com) 및 공식 GitHub
  (https://github.com/koreainvestment/open-trading-api)의 최신 예제와 대조 후
  실계좌 주문에 사용할 것. 여기 값은 계획 수립 시점 기준 통용되는 값으로,
  API 스펙 변경 여부를 사용자가 직접 재확인해야 한다.

환경변수:
  KIS_APP_KEY, KIS_APP_SECRET   : KIS Developers 발급 앱키/시크릿
  KIS_ACCOUNT_NO                : 계좌번호 앞 8자리
  KIS_ACCOUNT_PRODUCT_CD        : 계좌상품코드 뒤 2자리 (보통 "01")
  KIS_LIVE_MODE                 : "real"이면 실전투자, 그 외(기본값)는 모의투자
"""

from __future__ import annotations

import os
import time

import requests

from broker.base import BrokerClient, OrderResult, OrderSide, Position

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
VIRTUAL_BASE_URL = "https://openapivts.koreainvestment.com:29443"

TR_ID = {
    "price": "FHKST01010100",
    "minute_bars": "FHKST03010200",
    "balance": {"real": "TTTC8434R", "virtual": "VTTC8434R"},
    "buy": {"real": "TTTC0802U", "virtual": "VTTC0802U"},
    "sell": {"real": "TTTC0801U", "virtual": "VTTC0801U"},
}


class KISBrokerClient(BrokerClient):
    def __init__(
        self,
        app_key: str | None = None,
        app_secret: str | None = None,
        account_no: str | None = None,
        account_product_cd: str | None = None,
        live: bool | None = None,
    ):
        self.app_key = app_key or os.environ["KIS_APP_KEY"]
        self.app_secret = app_secret or os.environ["KIS_APP_SECRET"]
        self.account_no = account_no or os.environ["KIS_ACCOUNT_NO"]
        self.account_product_cd = account_product_cd or os.environ.get(
            "KIS_ACCOUNT_PRODUCT_CD", "01"
        )
        self._live = (
            live if live is not None else os.environ.get("KIS_LIVE_MODE") == "real"
        )
        self.base_url = REAL_BASE_URL if self._live else VIRTUAL_BASE_URL

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

        if self._live:
            print(
                "[KISBrokerClient] ⚠️ 실전투자 모드로 초기화됨 — 실제 주문이 실계좌에 반영됩니다."
            )

    @property
    def is_live(self) -> bool:
        return self._live

    def _tr_id(self, key: str) -> str:
        val = TR_ID[key]
        if isinstance(val, dict):
            return val["real" if self._live else "virtual"]
        return val

    # ── 인증 ──────────────────────────────────────────────────────────

    def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        resp = requests.post(
            f"{self.base_url}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        # expires_in(초) 만료 1분 전에 미리 갱신
        self._token_expires_at = time.time() + int(data.get("expires_in", 86400)) - 60
        return self._access_token

    def _headers(self, tr_id: str) -> dict:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._ensure_token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    # ── 시세 조회 ─────────────────────────────────────────────────────

    def get_current_price(self, ticker: str) -> float:
        tr_id = self._tr_id("price")
        resp = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=self._headers(tr_id),
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
            timeout=10,
        )
        resp.raise_for_status()
        return float(resp.json()["output"]["stck_prpr"])

    def get_minute_bars(self, ticker: str, n_bars: int = 30) -> list[dict]:
        """당일 분봉만 조회 가능 (KIS API 제약 — 과거 분봉 히스토리 API 없음)."""
        tr_id = self._tr_id("minute_bars")
        resp = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            headers=self._headers(tr_id),
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
                "FID_INPUT_HOUR_1": "",  # 빈 값 = 최신 시각 기준
                "FID_PW_DATA_INCU_YN": "N",
            },
            timeout=10,
        )
        resp.raise_for_status()
        rows = resp.json().get("output2", [])[:n_bars]
        return [
            {
                "time": r["stck_cntg_hour"],
                "open": float(r["stck_oprc"]),
                "high": float(r["stck_hgpr"]),
                "low": float(r["stck_lwpr"]),
                "close": float(r["stck_prpr"]),
                "volume": int(r["cntg_vol"]),
            }
            for r in rows
        ]

    # ── 잔고/포지션 ───────────────────────────────────────────────────

    def get_positions(self) -> list[Position]:
        tr_id = self._tr_id("balance")
        resp = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance",
            headers=self._headers(tr_id),
            params={
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.account_product_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            timeout=10,
        )
        resp.raise_for_status()
        rows = resp.json().get("output1", [])
        return [
            Position(
                ticker=r["pdno"],
                quantity=int(r["hldg_qty"]),
                avg_price=float(r["pchs_avg_pric"]),
                current_price=float(r["prpr"]),
            )
            for r in rows
            if int(r["hldg_qty"]) > 0
        ]

    def get_cash_balance(self) -> float:
        tr_id = self._tr_id("balance")
        resp = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance",
            headers=self._headers(tr_id),
            params={
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.account_product_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            timeout=10,
        )
        resp.raise_for_status()
        output2 = resp.json().get("output2", [{}])
        return float(output2[0].get("dnca_tot_amt", 0)) if output2 else 0.0

    # ── 주문 ─────────────────────────────────────────────────────────

    def place_order(self, ticker: str, side: OrderSide, quantity: int) -> OrderResult:
        if quantity <= 0:
            raise ValueError("quantity는 양수여야 합니다")

        tr_id = self._tr_id("buy" if side == OrderSide.BUY else "sell")
        resp = requests.post(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash",
            headers=self._headers(tr_id),
            json={
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.account_product_cd,
                "PDNO": ticker,
                "ORD_DVSN": "01",  # 시장가
                "ORD_QTY": str(quantity),
                "ORD_UNPR": "0",
            },
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        accepted = body.get("rt_cd") == "0"
        return OrderResult(
            ticker=ticker,
            side=side,
            quantity=quantity,
            order_id=body.get("output", {}).get("ODNO", ""),
            accepted=accepted,
            message=body.get("msg1", ""),
        )
