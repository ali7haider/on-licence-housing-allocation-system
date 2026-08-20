# On-Licence Housing Allocation System

## 1. Purpose

This is a PySide6 desktop pilot for the Durham allocation officer. It keeps fictional licensee and Rehabilitation Housing Unit (RHU) records in memory while the application is running. The system supports password-only access, licensee and RHU management, matching and ranking, allocation, release tracking, cost tracking, incident recording, and operational reports.

The project is deliberately a desktop pilot rather than a multi-user database system. No user ID, account creation, network service, or persistent database is required by the brief.

## 2. Starting the application

Run the application from the project directory:

```text
python3 main.py
```

The entry point in `main.py` creates a Qt `QApplication`, creates the password-only `LoginWindow`, displays it, and starts the Qt event loop.

The current password is defined by `PASSWORD` in `ui/login_window.py`:

```text
durham2026
```

There is intentionally no username field or user-management screen.

## 3. File-by-file guide

### `main.py`

Application entry point.

- Imports `QApplication` and `LoginWindow`.
- Defines `main()`, which creates the Qt application and login window.
- Calls `app.exec()` to keep the GUI event loop running.
- Runs `main()` only when the file is executed directly.

Connection: `main.py` starts `ui.login_window.LoginWindow`.

### `ui/login_window.py`

Password-only authentication screen.

- `LoginWindow(QWidget)` is the first screen.
- `PASSWORD` stores the pilot password.
- `_build_ui()` creates a password input and Log in button.
- Pressing Enter or clicking Log in calls `_login()`.
- A correct password creates and shows `MainWindow`, stores it in `self.main_window`, and closes the login window.
- An incorrect password displays a warning, clears the input, and returns focus to it.

Connection: successful login creates `ui.main_window.MainWindow`.

### `ui/main_window.py`

Main application shell and tab coordinator.

- `MainWindow(QMainWindow)` creates the application window.
- `generate_sample_data()` supplies the initial fictional dataset.
- `DataStore` becomes the shared in-memory source of truth.
- Creates one instance of each operational view:
  - `LicenseeListView`
  - `RHUListView`
  - `AllocationView`
  - `ReleaseListView`
  - `CostView`
  - `ReportView`
- Places those views in a `QTabWidget`.
- Connects change signals so related tabs refresh after edits, allocations, or release-date changes.

The views do not create separate stores. They all receive the same `DataStore` object.

### `ui/licensee_list_view.py`

Three-column licensee workflow and CRUD entry point.

Classes:

- `StateListWidget(QListWidget)` enables drag-and-drop between state columns.
- `LicenseeListView(QWidget)` displays Pending, Allocated, and Exited records.

Features:

- Search by name, prison role ID, home address, or current location.
- Sort by name or the relevant date.
- Pending records sort by prison release date.
- Allocated records sort by housing exit date.
- Exited records sort by name because they have no due date.
- Add a new licensee through `LicenseeEditor`.
- Double-click a licensee to edit or delete it.
- Drag records between state columns.
- Uses `record_changed` to tell the other views to refresh.

Important rule: moving a licensee directly into Allocated is rejected when no RHU has been assigned. A new allocation must be completed in the Allocation tab.

### `ui/licensee_editor.py`

Licensee create/edit/delete dialog.

- `LicenseeEditor(QDialog)` edits identifying, status, date, notes, and matching information.
- Required identity fields are name and prison role ID.
- Prison role IDs cannot be changed while editing an existing record.
- Uses `AttributeEditor` so the licensee and RHU forms share the same matching definitions.
- `_save()` creates a `Licensee` and calls `DataStore.add_licensee()` or `DataStore.update_licensee()`.
- `_delete()` confirms deletion and calls `DataStore.delete_licensee()`.
- `_enum_combo()` creates typed enum selectors.
- `_date_input()` creates calendar-enabled date fields.

### `ui/rhu_list_view.py`

RHU management and resident display.

- `RHUListView(QWidget)` lists RHUs in an expandable tree.
- Searches by RHU name, address, management group, contact, phone, or email.
- Add, edit, and delete RHUs through `RHUEditor` and `DataStore`.
- Displays current residents under each RHU.
- Residents are ordered by expected housing exit date.
- Double-clicking an RHU opens its editor.
- An RHU with residents cannot be deleted.
- A resident child row can open the incident editor.
- `_record_incident()` stores a per-resident violence or disturbance report.

Transfers are performed through the Allocation tab. `DataStore.allocate_licensee()` removes a resident from the old RHU before adding them to the new one.

### `ui/rhu_editor.py`

RHU create/edit dialog.

- `RHUEditor(QDialog)` records the RHU-only information required by the brief.
- Captures name, address, phone, email, management group, contact name, cost, standard capacity, emergency capacity, short-term beds, X/Y location, notes, and matching attributes.
- RHU names are fixed while editing so they remain stable references for residents and shortlists.
- Existing residents, incidents, costs, and payment date are preserved during edits.
- `_money_input()`, `_whole_number_input()`, and `_coordinate_input()` provide constrained numeric controls.

### `ui/attribute_editor.py`

Reusable matching-attribute form builder.

Classes:

- `ChoiceSetWidget` displays fixed choices such as categories and genders as checkboxes.
- `TagListWidget` adds and removes exclusion-zone tags without duplicates.
- `AttributeEditor` creates an appropriate Qt control for each `MatchAttribute` definition.

The editor chooses controls polymorphically:

- `YesNoAttribute` becomes a checkbox.
- `ZoneAttribute` becomes a tag-list editor.
- `TextAttribute` becomes a text input.
- Known category and gender fields become fixed choice checkboxes.

`set_values()` loads model data into the form and `values()` converts form data back into dictionaries stored on `Licensee` and `RHU` objects.

### `ui/allocation_view.py`

RHU ranking, shortlisting, and allocation.

- `AllocationView(QWidget)` lets the officer search for a licensee and select them from a picker.
- `rank_rhus_for()` evaluates every RHU and sorts the complete list by score.
- The table shows RHU, score, cost per day, and conflict warnings.
- The list is not filtered: unsuitable RHUs remain visible at the bottom.
- The officer can add up to five RHUs to a licensee shortlist.
- Selecting Allocate checks capacity and asks for confirmation when warnings exist.
- `DataStore.allocate_licensee()` performs the placement or transfer.
- `allocation_changed` causes licensee, RHU, release, cost, and report views to refresh.

### `ui/release_view.py`

Release and housing-exit management.

- `ReleaseDateDialog(QDialog)` edits one licensee's housing exit date.
- `ReleaseListView(QWidget)` groups allocated licensees by RHU.
- `upcoming_releases()` excludes records without a RHU or housing exit date and sorts each RHU's residents by date.
- Double-clicking a resident opens the date editor.
- `change_release_date()` returns a warning flag when the new date is later than the old date.
- Later dates display a warning because increases are unusual in the brief.
- `release_changed` refreshes the report view.

### `ui/cost_view.py`

Running cost and budget view.

- `CostView(QWidget)` displays residents, daily cost, total owed, last payment date, and budget status for each RHU.
- The budget input changes only the over-budget indicator.
- Add a day's cost calls `add_day()` for each occupied RHU.
- `add_day()` calculates `cost_per_bed_per_day * number_of_residents`.
- Mark selected as paid calls `mark_paid()` after confirmation.
- `mark_paid()` resets the RHU total to zero and updates `last_payment_date`.
- `is_overspending()` compares the total owed with the entered budget.

Cost accrual is intentionally manual because the pilot provides an explicit Add a day's cost action rather than a background clock.

### `ui/report_view.py`

Operational reporting and text export.

- `ReportView(QWidget)` displays a generated report.
- `build_operational_report()` includes licensee state counts, RHU occupancy, costs owed, upcoming exits, and incident reports.
- Generate report refreshes the preview.
- Save report writes the visible report to a user-selected `.txt` file.

### `logic/data_store.py`

The central in-memory application service.

Licensee operations:

- `add_licensee()` rejects duplicate prison role IDs.
- `update_licensee()` replaces an existing record and keeps residency consistent.
- `delete_licensee()` removes a record and frees its RHU bed.
- `transition_licensee_state()` supports the drag-and-drop state board.
- `list_licensees()` returns all or state-filtered records.
- `search_licensees()` searches identity and location fields.
- `get_licensee()` retrieves one record by prison role ID.

RHU operations:

- `add_rhu()` rejects duplicate names.
- `update_rhu()` replaces an existing RHU.
- `delete_rhu()` clears affected resident links and shortlist references.
- `allocate_licensee()` allocates or transfers a licensee and updates both sides of the relationship.
- `record_incident()` adds, replaces, or clears a resident incident.
- `list_rhus()`, `search_rhus()`, and `get_rhu()` provide read access.

Internal consistency rules:

- An Allocated licensee must have an RHU.
- Moving out of Allocated releases the RHU bed.
- RHU capacity includes standard plus emergency capacity for allocation.
- Deleting a licensee releases their bed.

### `logic/matching.py`

Matching rule registry and ranking algorithm.

- `MATCHING_RULES` is the central list of licensee-key/RHU-key/rule triples.
- `rank_rhus_for()` iterates through every RHU and every rule.
- Each result contains the RHU, total score, warnings, and daily cost.
- Results are sorted by score descending.
- Capacity does not affect suitability scores. It is enforced only when allocating: standard and emergency capacity together determine whether a placement is possible.
- Hard requirement mismatches receive a large penalty so they appear at the bottom without being filtered out.

The rule list is designed for extension: adding a matching criterion normally requires adding a tuple and corresponding editor values, not rewriting the ranking loop.

### `logic/costs.py`

Pure cost operations:

- `add_day()` accrues one day for all current residents of an RHU.
- `mark_paid()` returns the amount paid, resets the running total, and records today's date.
- `is_overspending()` reports whether the total exceeds a supplied budget.

### `logic/releases.py`

Release-date helpers:

- `upcoming_releases()` groups allocated residents by RHU and sorts them by housing exit date.
- `change_release_date()` updates a date and reports whether it was extended.

### `logic/reports.py`

`build_operational_report()` converts current model objects into a plain-text operational report. It reports all three licensee states, RHU occupancy and cost, upcoming exits, and recorded incidents.

### `logic/sample_data.py`

Deterministic fictional dataset generation.

- `generate_sample_data()` defaults to 4,000 licensees and 15 RHUs.
- `Random(seed)` makes the dataset repeatable.
- `_generate_rhus()` creates varied fictional RHUs, capacities, costs, services, genders, zones, and student-suggested attributes.
- `_generate_licensees()` creates unique IDs (`PR-00001`, etc.), dates, statuses, attributes, and residents.
- `_choose_available_rhu()` places allocated records only into RHUs with a free standard bed and compatible gender.

No real personal data is used.

### `models/person.py`

Object-oriented person hierarchy.

- `Person` is the base dataclass for shared name, home address, and gender data.
- `Licensee(Person)` inherits those fields and adds prison role ID, release dates, category, state, notes, matching attributes, RHU link, exit date, and shortlist.
- `Licensee.__post_init__()` converts valid string values into `Gender`, `Category`, and `LicenseeState` enum values.

### `models/rhu.py`

`RHU` dataclass containing facility details, matching attributes, residents, incidents, costs, and payment date.

### `models/enums.py`

Defines the controlled values used by the models:

- `LicenseeState`: Pending, Allocated, Exited.
- `Gender`: Male, Female, Mixed.
- `Category`: A, B, C.

### `models/attributes.py`

Polymorphic matching implementation.

- `MatchAttribute` is an abstract base class defining `matches()`.
- `YesNoAttribute` compares binary requirements.
- `TextAttribute` compares text or list values using shared values.
- `ZoneAttribute` detects overlap between exclusion-zone and nearby-zone tags.
- `HardRequirementAttribute` gives a severe penalty and conflict warning for category/gender mismatches.
- `MatchOutcome` carries score, explanation, and conflict status.
- `AttributeValue` is a small named-value model available for future use.
- `_normalise_values()` makes strings, lists, and scalar values comparable.

This is the clearest demonstration of inheritance and polymorphism in the project: `rank_rhus_for()` calls the same `matches()` interface while each subclass implements different comparison behaviour.

### `logic/__init__.py`, `models/__init__.py`, and `ui/__init__.py`

Package marker files. They allow Python to treat the folders as importable packages and contain no application behaviour.

## 4. How the files are connected

```text
main.py
  -> ui.login_window.LoginWindow
       -> ui.main_window.MainWindow
            -> logic.sample_data.generate_sample_data
            -> logic.data_store.DataStore
            -> all six UI views
                 -> shared DataStore
                 -> logic services and models
```

The most important connection is the shared `DataStore`:

```text
MainWindow
  -> DataStore
      -> LicenseeListView
      -> RHUListView
      -> AllocationView
      -> ReleaseListView
      -> CostView
      -> ReportView
```

The model and logic connections are:

```text
LicenseeEditor / RHUEditor
  -> AttributeEditor
  -> MATCHING_RULES
  -> Licensee / RHU
  -> DataStore

AllocationView
  -> rank_rhus_for()
      -> MATCHING_RULES
          -> MatchAttribute subclasses
  -> DataStore.allocate_licensee()

ReleaseListView -> releases.py -> DataStore.update_licensee()
CostView -> costs.py -> RHU totals
ReportView -> reports.py -> text output
```

## 5. Qt signal and refresh flow

### Allocation

1. The officer selects a licensee and an RHU.
2. `AllocationView._allocate_selected_rhu()` confirms warnings and capacity.
3. `DataStore.allocate_licensee()` updates the licensee and RHU.
4. `AllocationView.allocation_changed` is emitted.
5. `MainWindow` forwards that signal to `refresh()` on the licensee, RHU, release, cost, and report views.

### Licensee edit or drag-and-drop

1. The officer saves an editor or drops a record into another state.
2. `DataStore` performs the CRUD/state transition.
3. `LicenseeListView.record_changed` is emitted.
4. The RHU, allocation, release, cost, and report views refresh.

### Release-date change

1. The officer double-clicks a resident in the Releases tab.
2. `ReleaseDateDialog` returns the selected date.
3. `change_release_date()` updates the model and detects an extension.
4. `DataStore.update_licensee()` validates the record.
5. `ReleaseListView.release_changed` refreshes the report view.

### Cost changes

Cost controls refresh only the Cost tab directly. Allocation changes refresh costs through `allocation_changed`, so resident counts and cost calculations remain current.

## 6. Normal user workflow

1. Start `python3 main.py`.
2. Enter the password on the login screen.
3. Review licensees in the three state columns.
4. Search or sort the board as needed.
5. Add a new licensee or double-click an existing licensee to edit it.
6. Record dates, state, notes, and matching requirements in the editor.
7. Review RHUs and their residents in the RHUs tab.
8. Add or edit RHU capacity, costs, contacts, location, notes, and matching provisions.
9. Open Allocation and choose a licensee.
10. Review all RHUs ranked by suitability, cost, and warnings.
11. Add up to five options to the shortlist if follow-up is needed.
12. Select an RHU and allocate. Confirm warnings when human judgement accepts the risk.
13. Use drag-and-drop for later movement between Pending, Allocated, and Exited where the data rules permit it.
14. Use Releases to see upcoming exits grouped by RHU and edit dates.
15. Use Costs to accrue a day's cost, set a budget, identify overspending, and mark payments.
16. Use RHUs to record a resident violence or disturbance report.
17. Use Reports to generate and save a plain-text operational report.

## 7. Assessment requirement traceability

### Password-only Durham pilot

Achieved in `ui/login_window.py`.

- The first screen asks only for a password.
- `PASSWORD` is checked by `_login()`.
- No user ID, username, account creation, or multi-user administration exists.
- The interface is branded for the Durham allocation office.

### Use Python and Qt/PySide6

Achieved throughout the project.

- Python is used for all application code.
- Qt widgets and signals come from PySide6.
- `QApplication`, `QWidget`, `QMainWindow`, dialogs, trees, tables, lists, forms, buttons, and signals are used in the UI package.

### Use multiple classes and object-oriented design

Achieved in the `models`, `logic`, and `ui` packages.

- Inheritance: `Licensee(Person)`.
- Abstract interface: `MatchAttribute.matches()`.
- Polymorphism: `YesNoAttribute`, `TextAttribute`, `ZoneAttribute`, and `HardRequirementAttribute` override `matches()`.
- GUI inheritance: application views inherit from Qt widget classes.
- Dataclasses provide structured `Person`, `Licensee`, `RHU`, and `MatchOutcome` objects.
- `DataStore` encapsulates application state and business consistency rules.

### Licensee CRUDLS

Achieved across `ui/licensee_list_view.py`, `ui/licensee_editor.py`, and `logic/data_store.py`.

- Create: Add new licensee -> `LicenseeEditor._save()` -> `DataStore.add_licensee()`.
- Read/list: `LicenseeListView.refresh()` -> `list_licensees()`.
- Search: search box -> `search_licensees()`.
- Update: edit dialog -> `update_licensee()`.
- Delete: delete button -> `delete_licensee()`.
- Sort: `_sort_licensees()`.

### Three licensee states and movement

Achieved through `LicenseeState` in `models/enums.py` and the three columns in `LicenseeListView`.

- Pending means awaiting housing or release.
- Allocated means assigned to an RHU.
- Exited means no longer active in the housing workflow.
- `StateListWidget.dropEvent()` provides drag-and-drop.
- `DataStore.transition_licensee_state()` updates state and releases beds when necessary.
- New allocations require a specific RHU through `AllocationView`.

### Sort by time before transfer or housing requirement

Partially achieved in `LicenseeListView._sort_licensees()`.

- Pending records are ordered by prison release date.
- Allocated records are ordered by expected housing exit date.
- Exited records have no due date and are ordered by name.
- The UI shows dates, which lets the officer judge time remaining.
- It does not currently display a calculated “days remaining” number or provide a separate date-range filter.

### Licensee identifying details and notes

Achieved in `LicenseeEditor` and `Licensee`.

- Name, home address, gender, prison role ID, prison release date, expected licence end, current location, category, state, and notes are recorded.
- Duplicate names are allowed because prison role ID is the unique key.
- Generated role IDs are unique.
- A real deployment would need validation and secure handling for sensitive data.

### Matching attributes and editors

Achieved through `MATCHING_RULES`, `AttributeEditor`, `LicenseeEditor`, `RHUEditor`, and `models/attributes.py`.

Implemented matching areas include:

- Category.
- Gender, including RHU mixed-gender acceptance.
- Nighttime curfew.
- Weekend curfew.
- Victim exclusion zones.
- School exclusion zones.
- General exclusion zones.
- Associate/co-defendant proximity or exclusion zones.
- Disability support needs.
- Physical accessibility.
- Drug searches.
- Young offender suitability.
- Medical services.
- Transport links.
- Cultural or religious support.
- Mental health support.
- Family access.
- Prior RHU experience.
- Employment or training support.
- Specific offending-trigger avoidance.
- Licence period.
- Future Expansion 1, 2, and 3 placeholders.
- Student Suggested 1: digital/electronic monitoring support.
- Student Suggested 2: peer-environment compatibility.
- Notes/miscellaneous fields are stored but are not part of the scoring rules.

The shared `AttributeEditor` generates the corresponding licensee and RHU controls from the rule definitions.

### Location and exclusion-zone handling

Achieved using tag lists and `ZoneAttribute`.

- Licensees store excluded locations such as schools, victim areas, associates, or general zones.
- RHUs store nearby location tags.
- Overlapping tags generate a negative score and an explicit warning.
- Multiple tags are supported.
- RHU X/Y coordinates are stored in `RHU` and edited in `RHUEditor`, but ranking currently uses named zone tags rather than geographic distance calculations.

### RHU information and resident lists

Achieved in `RHU`, `RHUEditor`, `RHUListView`, and `DataStore`.

- RHU name, cost, standard capacity, emergency capacity, short-term beds, geographic location, address, phone, email, contact, management group, and notes are stored.
- Current residents are stored as prison role IDs and resolved to names through the shared store.
- Residents are shown under each RHU and sorted by expected exit date.
- RHUs with residents cannot be deleted.
- Transfers are handled by `allocate_licensee()`.

### RHU ranking and human decision-making

Achieved in `logic/matching.py` and `ui/allocation_view.py`.

- Every RHU is evaluated and shown.
- Scores and explanations are visible.
- Hard conflicts receive severe penalties but are not hidden.
- The officer is asked to confirm allocation when warnings exist.
- The officer remains responsible for the final decision.
- Shortlists support up to five RHUs per licensee.

### Cost management

Achieved in `logic/costs.py` and `ui/cost_view.py`.

- Daily cost is cost per bed per day multiplied by current residents.
- Add a day's cost accrues totals for occupied RHUs.
- Mark selected as paid resets an RHU total and records the payment date.
- A per-RHU budget indicates “Over budget” or “Within budget”.
- The system does not automatically forecast future overspending or accrue costs based on a real clock.

### Release management

Achieved in `logic/releases.py` and `ui/release_view.py`.

- Allocated licensees with housing exit dates are listed.
- They are grouped by RHU.
- Each group is ordered by nearest exit date.
- Dates can be changed through a dialog.
- A later date produces a warning.
- The report includes upcoming housing exits.

### Incidents and monitoring

Achieved in `RHU.incidents`, `DataStore.record_incident()`, `RHUListView._record_incident()`, and `reports.py`.

- A violence or disturbance report is stored per RHU and resident.
- Existing reports can be replaced or cleared.
- The RHU view indicates that an incident exists.
- The operational report includes incident details.

### Generated test data

Achieved in `logic/sample_data.py`.

- The default dataset contains approximately 4,000 fictional licensees and 15 RHUs.
- Prison role IDs are unique.
- A fixed random seed makes testing repeatable.
- The generated data covers Pending, Allocated, and Exited states.

## 8. Known limitations and sensible future improvements

These are useful to mention in an assessment explanation because they show conscious prioritisation.

- Data is in memory only and is lost when the program closes.
- The password is hardcoded for a single-user pilot.
- The UI does not calculate or display numeric days remaining.
- Matching uses tags and shared text values, not geographic distance from X/Y coordinates.
- Some generated records contain only a subset of all optional matching attributes; the editors still expose the full configured rule set.
- Notes are stored but not scored by matching.
- Reports export as text rather than PDF, spreadsheet, or email.
- Cost accrual is a manual action rather than an automatic date-based process.
- The optional licensee photo is not implemented.
- The report is suitable for internal monitoring but does not provide a dedicated inter-agency export format.
- RHU deletion requires residents to be transferred or exited first, which protects referential consistency.

## 9. Short demonstration script

For an assessment demonstration:

1. Launch the application and show that only a password is required.
2. Show the three licensee state columns and search/sort controls.
3. Add a licensee with a unique role ID and matching requirements.
4. Open an RHU and show capacity, cost, contacts, location, and matching attributes.
5. Select the new licensee in Allocation and explain why every RHU remains visible.
6. Show a conflict warning, add two or more RHUs to the shortlist, and allocate one.
7. Open RHUs to show the resident now appears under the selected RHU.
8. Drag the licensee to another permitted state and show the linked bed is released when leaving Allocated.
9. Open Releases, change an exit date later, and show the warning.
10. Add a day's cost, mark an RHU as paid, and show the budget status.
11. Record a resident incident and generate the operational report.
12. Save the report as a text file.
