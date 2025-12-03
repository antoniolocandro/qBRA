# qBRA

QBRA is a collection of QGIS tools for aviation procedures. This
repository currently includes the `QBRA ILS/LLZ` plugin, which
creates BRA (Basic Radio Aids) areas around a selected navaid using
the same calculations as the original QGIS script.

## QBRA ILS/LLZ plugin

### Folder structure

The plugin lives in the `qbra_ils_llz` folder and follows the same
structure as other QBRA/qpansopy plugins:

- `qbra_ils_llz/qbra_plugin.py` – main plugin entry class.
- `qbra_ils_llz/modules/ils_llz_logic.py` – all BRA geometry
  calculations (ported from the legacy script).
- `qbra_ils_llz/dockwidgets/ils/ils_llz_dockwidget.py` – controller for
  the dock panel.
- `qbra_ils_llz/ui/ils/ils_llz_panel.ui` – Qt Designer UI for the
  panel.
- `qbra_ils_llz/icons/ils_llz.svg` – plugin icon.
- `qbra_ils_llz/metadata.txt` – QGIS plugin metadata.

### Installation in QGIS

1. Create a ZIP file that contains the `qbra_ils_llz` folder at the
   root (for example `qbra_ils_llz.zip`).
2. In QGIS, open `Plugins` → `Manage and Install Plugins...`.
3. Choose `Install from ZIP` and select the ZIP you created.
4. Enable the `QBRA ILS/LLZ` plugin in the Plugins list.

### Usage

1. Load your navaid point layer and routing/runway line layer into the
   QGIS project.
2. Make sure the navaid layer has the same attribute order as the
   original script (site elevation in field 4, runway identifier in
   field 5).
3. Select one navaid feature and one routing/runway feature.
4. Click the `QBRA ILS/LLZ` toolbar button or menu entry to open the
   dock panel.
5. Choose the navaid and routing layers in the panel (they default to
   the active layers), then press `Calculate`.
6. The plugin will create a new memory layer with the BRA polygons and
   add it to the project.

The calculations and resulting geometries are intended to match the
original `ILS_LLZ_single_frequency.py` script.
