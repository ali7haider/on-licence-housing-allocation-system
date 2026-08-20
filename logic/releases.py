"""Release-list and target exit-date helpers."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

from models.enums import LicenseeState
from models.person import Licensee


def upcoming_releases(licensees: Iterable[Licensee]) -> dict[str, list[Licensee]]:
    """Return allocated licensees due to leave housing, grouped by RHU name.

    Licensees without a current RHU or a recorded housing exit date are not
    included. Each RHU's list is ordered by the nearest exit date first.
    """
    grouped: defaultdict[str, list[Licensee]] = defaultdict(list)
    for licensee in licensees:
        if (
            licensee.state is LicenseeState.ALLOCATED
            and licensee.current_rhu_name
            and licensee.housing_exit_date
        ):
            grouped[licensee.current_rhu_name].append(licensee)

    return {
        rhu_name: sorted(residents, key=lambda resident: resident.housing_exit_date)
        for rhu_name, residents in sorted(grouped.items())
    }


def change_release_date(licensee: Licensee, new_date: date) -> bool:
    """Update a housing exit date and flag when it has been extended.

    ``True`` means the new date is later than the previously recorded date and
    the allocation officer should be shown a warning.
    """
    old_date = licensee.housing_exit_date
    warning_required = old_date is not None and new_date > old_date
    licensee.housing_exit_date = new_date
    return warning_required
