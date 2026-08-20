"""Generate plain-text operational reports for the allocation office."""

from collections.abc import Iterable
from datetime import date

from models.enums import LicenseeState
from models.history import AuditEvent
from models.person import Licensee
from models.rhu import RHU
from logic.costs import projected_cost


def build_operational_report(
    licensees: Iterable[Licensee],
    rhus: Iterable[RHU],
    audit_events: Iterable[AuditEvent] = (),
) -> str:
    """Return a concise report covering placements, releases, incidents, and costs."""
    licensee_list = list(licensees)
    rhu_list = list(rhus)
    lines = [
        "ON-LICENCE HOUSING ALLOCATION REPORT",
        f"Generated: {date.today():%d %b %Y}",
        "",
        "LICENSEE SUMMARY",
    ]
    for state in LicenseeState:
        lines.append(f"{state.value}: {sum(item.state is state for item in licensee_list)}")

    lines.extend(["", "RHU SUMMARY"])
    for rhu in rhu_list:
        lines.append(
            f"{rhu.name}: {len(rhu.resident_ids)}/{rhu.capacity} standard beds, "
            f"£{rhu.total_owed:.2f} owed, {len(rhu.incidents)} incident report(s)"
        )

    lines.extend(["", "COST FORECAST (NEXT 30 DAYS)"])
    for rhu in rhu_list:
        lines.append(f"{rhu.name}: £{projected_cost(rhu):.2f} projected")

    lines.extend(["", "UPCOMING HOUSING EXITS"])
    exits = sorted(
        (
            resident.housing_exit_date,
            resident.name,
            resident.prison_role_id,
            resident.current_rhu_name,
        )
        for resident in licensee_list
        if resident.state is LicenseeState.ALLOCATED
        and resident.housing_exit_date is not None
        and resident.current_rhu_name
    )
    if exits:
        lines.extend(
            f"{exit_date:%d %b %Y}: {name} ({role_id}) - {rhu_name}"
            for exit_date, name, role_id, rhu_name in exits
        )
    else:
        lines.append("No upcoming housing exits recorded.")

    lines.extend(["", "INCIDENT REPORTS"])
    incident_count = 0
    for rhu in rhu_list:
        for role_id, details in rhu.incidents.items():
            resident = next((item for item in licensee_list if item.prison_role_id == role_id), None)
            resident_name = resident.name if resident else "Unknown licensee"
            lines.append(f"{rhu.name} - {resident_name} ({role_id}): {details}")
            incident_count += 1
    if incident_count == 0:
        lines.append("No violence or disturbance reports recorded.")

    lines.extend(["", "LICENCE-CONDITION BREACHES"])
    breach_count = 0
    for licensee in licensee_list:
        for breach in licensee.breaches:
            lines.append(
                f"{breach.recorded_at:%d %b %Y %H:%M} - "
                f"{licensee.name} ({licensee.prison_role_id}): {breach.details}"
            )
            breach_count += 1
    if breach_count == 0:
        lines.append("No licence-condition breaches recorded.")

    lines.extend(["", "AUDIT HISTORY"])
    audit_count = 0
    for event in audit_events:
        location_change = f" ({event.from_rhu or 'None'} -> {event.to_rhu or 'None'})" \
            if event.from_rhu != event.to_rhu else ""
        state_change = f" [{event.from_state or 'None'} -> {event.to_state or 'None'}]" \
            if event.from_state != event.to_state and (event.from_state or event.to_state) else ""
        detail = f": {event.details}" if event.details else ""
        lines.append(
            f"{event.timestamp:%d %b %Y %H:%M} - {event.prison_role_id} - "
            f"{event.action}{state_change}{location_change}{detail}"
        )
        audit_count += 1
    if audit_count == 0:
        lines.append("No audit events recorded during this session.")

    return "\n".join(lines)
