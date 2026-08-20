"""In-memory storage and CRUD operations for the pilot application."""

from collections.abc import Iterable

from models.enums import LicenseeState
from models.person import Licensee
from models.rhu import RHU


class DataStore:
    """Hold the application's licensees and RHUs while it is running.

    The pilot does not require a database. This class gives the UI one simple
    place to manage its in-memory records, and is the single place that keeps
    a licensee's state consistent with their RHU residency.
    """

    def __init__(
        self,
        licensees: Iterable[Licensee] | None = None,
        rhus: Iterable[RHU] | None = None,
    ) -> None:
        self.licensees = list(licensees or [])
        self.rhus = list(rhus or [])

    # -- Licensees ---------------------------------------------------------

    def add_licensee(self, licensee: Licensee) -> None:
        """Add a licensee, rejecting a duplicate prison role ID."""
        if self.get_licensee(licensee.prison_role_id) is not None:
            raise ValueError(f"A licensee with ID {licensee.prison_role_id} already exists.")
        self._validate_residency(licensee)
        self.licensees.append(licensee)

    def update_licensee(self, licensee: Licensee) -> None:
        """Replace an existing licensee, keeping RHU residency consistent.

        A record cannot be saved as Allocated without an RHU on file. If the
        saved state is no longer Allocated, any existing RHU link is released
        so the bed is freed and costs stop accruing for them.
        """
        index = self._licensee_index(licensee.prison_role_id)
        self._validate_residency(licensee)
        if licensee.state != LicenseeState.ALLOCATED and licensee.current_rhu_name:
            self._release_rhu_link(licensee)
        self.licensees[index] = licensee

    def delete_licensee(self, prison_role_id: str) -> None:
        """Remove a licensee by prison role ID, releasing their RHU bed first."""
        licensee = self.get_licensee(prison_role_id)
        if licensee is not None and licensee.current_rhu_name:
            self._release_rhu_link(licensee)
        del self.licensees[self._licensee_index(prison_role_id)]

    def transition_licensee_state(self, prison_role_id: str, new_state: LicenseeState) -> None:
        """Move a licensee between Pending / Allocated / Exited.

        Used by the drag-and-drop board. A direct move into Allocated is only
        allowed when the licensee already has an RHU on record (e.g.
        re-activating them); a fresh placement must go through the Allocation
        tab, which assigns a specific RHU. Moving out of Allocated always
        releases the bed.
        """
        licensee = self.get_licensee(prison_role_id)
        if licensee is None:
            raise KeyError(f"No licensee with ID {prison_role_id} exists.")
        if new_state == LicenseeState.ALLOCATED and not licensee.current_rhu_name:
            raise ValueError(
                f"{licensee.name} has no RHU on record. Assign one from the Allocation tab."
            )
        if new_state != LicenseeState.ALLOCATED and licensee.current_rhu_name:
            self._release_rhu_link(licensee)
        licensee.state = new_state

    def list_licensees(self, state: LicenseeState | None = None) -> list[Licensee]:
        """Return all licensees, or only those in the requested state."""
        if state is None:
            return list(self.licensees)
        return [licensee for licensee in self.licensees if licensee.state == state]

    def search_licensees(self, text: str) -> list[Licensee]:
        """Search licensees by name, role ID, address, or current location."""
        query = text.strip().casefold()
        if not query:
            return self.list_licensees()
        return [
            licensee
            for licensee in self.licensees
            if query in licensee.name.casefold()
            or query in licensee.prison_role_id.casefold()
            or query in licensee.home_address.casefold()
            or query in licensee.current_location.casefold()
        ]

    def get_licensee(self, prison_role_id: str) -> Licensee | None:
        """Return one licensee by ID, or ``None`` when it is not present."""
        return next(
            (licensee for licensee in self.licensees if licensee.prison_role_id == prison_role_id),
            None,
        )

    # -- RHUs ----------------------------------------------------------------

    def add_rhu(self, rhu: RHU) -> None:
        """Add an RHU, rejecting a duplicate RHU name."""
        if self.get_rhu(rhu.name) is not None:
            raise ValueError(f"An RHU named {rhu.name} already exists.")
        self.rhus.append(rhu)

    def update_rhu(self, rhu: RHU) -> None:
        """Replace an existing RHU using its name."""
        index = self._rhu_index(rhu.name)
        self.rhus[index] = rhu

    def delete_rhu(self, name: str) -> None:
        """Remove an RHU, freeing residents and clearing shortlist references."""
        for licensee in self.licensees:
            if licensee.current_rhu_name == name:
                self._release_rhu_link(licensee)
                licensee.state = LicenseeState.PENDING
            if name in licensee.shortlist:
                licensee.shortlist.remove(name)
        del self.rhus[self._rhu_index(name)]
    def list_rhus(self) -> list[RHU]:
        """Return all RHUs without exposing the internal list."""
        return list(self.rhus)

    def search_rhus(self, text: str) -> list[RHU]:
        """Search RHUs by name, address, management group, or contact details."""
        query = text.strip().casefold()
        if not query:
            return self.list_rhus()
        return [
            rhu
            for rhu in self.rhus
            if query in rhu.name.casefold()
            or query in rhu.address.casefold()
            or query in rhu.management_group.casefold()
            or query in rhu.contact_name.casefold()
            or query in rhu.phone.casefold()
            or query in rhu.email.casefold()
        ]

    def get_rhu(self, name: str) -> RHU | None:
        """Return one RHU by name, or ``None`` when it is not present."""
        return next((rhu for rhu in self.rhus if rhu.name == name), None)

    # -- Internal helpers ------------------------------------------------

    def _validate_residency(self, licensee: Licensee) -> None:
        """Reject a record that claims Allocated without an RHU on file."""
        if licensee.state == LicenseeState.ALLOCATED and not licensee.current_rhu_name:
            raise ValueError(
                f"{licensee.name} cannot be saved as Allocated without an RHU. "
                "Assign one from the Allocation tab."
            )

    def _release_rhu_link(self, licensee: Licensee) -> None:
        """Detach a licensee from their current RHU's resident list."""
        if licensee.current_rhu_name:
            rhu = self.get_rhu(licensee.current_rhu_name)
            if rhu is not None and licensee.prison_role_id in rhu.resident_ids:
                rhu.resident_ids.remove(licensee.prison_role_id)
        licensee.current_rhu_name = None
        licensee.housing_exit_date = None

    def _licensee_index(self, prison_role_id: str) -> int:
        """Find a licensee index or raise a clear error for a missing record."""
        for index, licensee in enumerate(self.licensees):
            if licensee.prison_role_id == prison_role_id:
                return index
        raise KeyError(f"No licensee with ID {prison_role_id} exists.")

    def _rhu_index(self, name: str) -> int:
        """Find an RHU index or raise a clear error for a missing record."""
        for index, rhu in enumerate(self.rhus):
            if rhu.name == name:
                return index
        raise KeyError(f"No RHU named {name} exists.")