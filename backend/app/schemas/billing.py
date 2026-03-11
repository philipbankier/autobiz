from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel

from app.models.cost_event import CostType


class BalanceRead(BaseModel):
    credits_balance: Decimal


class UsageItem(BaseModel):
    type: CostType
    total_amount: Decimal
    event_count: int


class UsageRead(BaseModel):
    items: list[UsageItem]
    total_spent: Decimal
    period_start: datetime
    period_end: datetime
