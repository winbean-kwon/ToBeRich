"""
PolicyAdapter 공통 인터페이스 — live_trading_loop_binance.py와 실제 정책 구현체
(crypto/inference/policy_v4.py 등) 양쪽에서 순환 import 없이 참조하기 위해 분리.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from crypto.broker.base import BrokerClient


class PolicyAdapter(ABC):
    """목표 비중 산출 정책 인터페이스."""

    @abstractmethod
    def target_weights(self, symbols: list[str], broker: BrokerClient) -> dict[str, float]:
        """심볼별 목표 비중 (합계 1.0 이하) 반환."""


class EqualWeightPolicy(PolicyAdapter):
    """브로커 연동 자체를 검증하기 위한 더미 정책 — 등가중 배분."""

    def target_weights(self, symbols: list[str], broker: BrokerClient) -> dict[str, float]:
        w = 1.0 / len(symbols)
        return {s: w for s in symbols}
