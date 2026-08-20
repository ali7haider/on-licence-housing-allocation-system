"""Simple running-cost calculations for Rehabilitation Housing Units."""

from datetime import date

from models.rhu import RHU


def add_day(rhu: RHU) -> float:
    """Add one day's placement cost to an RHU and return the amount added."""
    daily_cost = rhu.cost_per_bed_per_day * len(rhu.resident_ids)
    rhu.total_owed += daily_cost
    return daily_cost


def mark_paid(rhu: RHU) -> float:
    """Reset an RHU's accrued cost and return the amount that was paid."""
    paid_amount = rhu.total_owed
    rhu.total_owed = 0.0
    rhu.last_payment_date = date.today()
    return paid_amount


def is_overspending(rhu: RHU, budget: float) -> bool:
    """Return whether the RHU's running total is above the supplied budget."""
    return rhu.total_owed > budget


def projected_cost(rhu: RHU, days: int = 30) -> float:
    """Estimate future cost from the current resident count and daily rate."""
    return rhu.cost_per_bed_per_day * len(rhu.resident_ids) * days
