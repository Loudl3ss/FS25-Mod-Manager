"""Settings selection page for New Game wizard."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.new_game_session import NewGameSession
from ui.assets import Icons


SECTION_LABEL_STYLE = (
    "color: #ffffff;"
    "font-size: 10px;"
    "font-weight: 700;"
    "letter-spacing: 1px;"
)

DIFFICULTY_OPTIONS = [("Easy", 1), ("Normal", 2), ("Hard", 3)]
TIMESCALE_OPTIONS = ["Real Time", "5x", "15x", "30x", "60x", "120x"]
AUTOSAVE_OPTIONS = [("Off", 0), ("5 min", 5), ("10 min", 10), ("15 min", 15)]
STARTING_CASH_OPTIONS = [("100k", 100000), ("500k", 500000), ("1M", 10000000), ("5M", 50000000)]
STARTING_LOAN_OPTIONS = [("0", 0), ("100k", 100000), ("250k", 250000), ("500k", 500000)]
TOGGLE_OPTIONS = [("Off", False), ("On", True)]
SEASONAL_GROWTH_OPTIONS = [("Yes", 1), ("No", 2), ("Paused", 3)]
DISASTER_DESTRUCTION_OPTIONS = [("Disabled", 0), ("Visuals Only", 1), ("Enabled", 2)]
DIRT_OPTIONS = [("Normal", 1), ("Fast", 2), ("Slow", 3), ("Off", 4)]
FUEL_USAGE_OPTIONS = [("Low", 1), ("Normal", 2), ("High", 3)]
AI_REFILL_OPTIONS = [("Off", 0), ("Buy", 1)]


class SettingsGroupWidget(QFrame):
    """A styled section container for grouped settings."""

    def __init__(self, title: str, parent=None, embed_title: bool = True):
        super().__init__(parent)
        self.setObjectName("SettingsGroup")
        self.setStyleSheet(
            "QFrame#SettingsGroup {"
            "background-color: #0e1116;"
            "border: 1px solid #161a21;"
            "border-radius: 18px;"
            "}"
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        container = QVBoxLayout(self)
        container.setContentsMargins(15, 15, 15, 15)
        container.setSpacing(10)

        if embed_title:
            title_lbl = QLabel(f"• {title}")
            title_lbl.setObjectName("SettingsGroupTitle")
            title_lbl.setStyleSheet(
                "color: #ffffff;"
                "font-weight: 700;"
                "text-transform: uppercase;"
                "letter-spacing: 0.7px;"
            )
            container.addWidget(title_lbl)

        self.body = QWidget()
        self.body_layout = QFormLayout(self.body)
        self.body_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.body_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.body_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.body_layout.setHorizontalSpacing(20)
        self.body_layout.setVerticalSpacing(12)
        self.body_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        container.addWidget(self.body)

    def add_row(self, label: str, widget: QWidget):
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #ffffff; font-weight: 600; padding: 5px 0px;")

        row_container = QWidget()
        row_layout = QHBoxLayout(row_container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        row_layout.addStretch()
        row_layout.addWidget(widget)

        self.body_layout.addRow(label_widget, row_container)


class GameplaySettingsView(QWidget):
    """Step 2: Gameplay settings configuration."""

    request_next_step = pyqtSignal()
    request_previous_step = pyqtSignal()

    def __init__(self, session: NewGameSession, parent=None):
        super().__init__(parent)
        self.session = session
        self._button_groups: dict[str, QButtonGroup] = {}
        self._custom_inputs: dict[str, QLineEdit] = {}
        self._slider_labels: dict[str, QLabel] = {}
        self._sliders: dict[str, QSlider] = {}

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setObjectName("WizardTopNav")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(24, 12, 24, 12)

        step_label = QLabel("Step 2 of 3")
        step_label.setObjectName("WizardStepLabel")
        nav_layout.addWidget(step_label)

        nav_layout.addStretch()

        self.btn_back = QPushButton("← Back")
        self.btn_back.setObjectName("WizardNavSecondaryBtn")
        self.btn_back.clicked.connect(self.request_previous_step.emit)
        nav_layout.addWidget(self.btn_back)

        self.btn_next = QPushButton("Next →")
        self.btn_next.setObjectName("WizardNavPrimaryBtn")
        self.btn_next.clicked.connect(self.request_next_step.emit)
        nav_layout.addWidget(self.btn_next)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        title_icon = QLabel()
        title_icon.setPixmap(Icons.get_qicon(Icons.COUNTER_2).pixmap(22, 22))
        title_row.addWidget(title_icon)

        title = QLabel("Gameplay Settings")
        title.setObjectName("PageTitle")
        title.setStyleSheet(
            "color: #ffffff;"
            "font-size: 22px;"
            "font-weight: 700;"
        )
        title_row.addWidget(title)
        title_row.addStretch(1)
        header_layout.addLayout(title_row)

        subtitle = QLabel("Configure your game world settings")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setStyleSheet(
            "color: #7d8694;"
            "font-size: 13px;"
        )
        header_layout.addWidget(subtitle)

        content_layout.addWidget(header)

        self._add_settings_section(content_layout, "General", self._build_general_group)
        self._add_settings_section(content_layout, "Seasons", self._build_seasons_group)
        self._add_settings_section(content_layout, "Crops and Growth", self._build_crops_growth_group)
        self._add_settings_section(content_layout, "Vehicle Controls", self._build_vehicle_controls_group)
        self._add_settings_section(content_layout, "AI Workers", self._build_ai_workers_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        root_layout.addWidget(scroll)
        root_layout.addWidget(nav_bar)

    def _add_settings_section(self, content_layout: QVBoxLayout, title: str, builder) -> None:
        label = QLabel(f"· {title}")
        label.setStyleSheet(SECTION_LABEL_STYLE)
        content_layout.addWidget(label)
        content_layout.addWidget(builder())

    def _build_general_group(self) -> SettingsGroupWidget:
        general = SettingsGroupWidget("General", embed_title=False)

        self.savegame_name_input = self._make_line_edit("Farm Name")
        general.add_row("Farm Name", self.savegame_name_input)

        self.difficulty_group = self._make_segmented_button_group(
            DIFFICULTY_OPTIONS,
            "difficulty",
        )
        general.add_row("Economic Difficulty", self.difficulty_group)

        self.time_scale_dropdown = self._make_dropdown(
            TIMESCALE_OPTIONS,
            "timeScale",
        )
        general.add_row("Timescale", self.time_scale_dropdown)

        self.autosave_group = self._make_segmented_button_group(
            AUTOSAVE_OPTIONS,
            "autoSaveInterval",
        )
        general.add_row("Autosave Interval", self.autosave_group)

        self.starting_cash_widget = self._make_segmented_with_custom(
            STARTING_CASH_OPTIONS,
            "money",
        )
        general.add_row("Starting Cash", self.starting_cash_widget)

        self.starting_loan_widget = self._make_segmented_with_custom(
            STARTING_LOAN_OPTIONS,
            "loan",
        )
        general.add_row("Starting Loan", self.starting_loan_widget)

        self.traffic_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "trafficEnabled",
        )
        general.add_row("Traffic", self.traffic_group)

        self.snow_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "snowEnabled",
        )
        general.add_row("Snow", self.snow_group)

        return general

    def _build_seasons_group(self) -> SettingsGroupWidget:
        seasons = SettingsGroupWidget("Seasons", embed_title=False)

        self.seasonal_growth_group = self._make_segmented_button_group(
            SEASONAL_GROWTH_OPTIONS,
            "seasonalGrowth",
        )
        seasons.add_row("Season Growth", self.seasonal_growth_group)

        self.days_per_month_widget = self._make_slider_with_label(1, 28, "daysPerMonth")
        seasons.add_row("Days Per Month", self.days_per_month_widget)

        self.fixed_visual_month_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "fixedVisualMonth",
        )
        seasons.add_row("Fixed Visual Month", self.fixed_visual_month_group)

        return seasons

    def _build_crops_growth_group(self) -> SettingsGroupWidget:
        crops = SettingsGroupWidget("Crops and Growth", embed_title=False)

        self.crop_destruction_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "cropDestruction",
        )
        crops.add_row("Crop Destruction", self.crop_destruction_group)

        self.plowing_required_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "plowingRequired",
        )
        crops.add_row("Periodic Plowing Required", self.plowing_required_group)

        self.fieldstone_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "fieldstoneEnabled",
        )
        crops.add_row("Fieldstone", self.fieldstone_group)

        self.lime_required_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "limeRequired",
        )
        crops.add_row("Lime Required", self.lime_required_group)

        self.weed_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "weedsEnabled",
        )
        crops.add_row("Weed", self.weed_group)

        self.disaster_destruction_group = self._make_segmented_button_group(
            DISASTER_DESTRUCTION_OPTIONS,
            "disasterDestruction",
        )
        crops.add_row("Disaster Destruction", self.disaster_destruction_group)

        return crops

    def _build_vehicle_controls_group(self) -> SettingsGroupWidget:
        vehicles = SettingsGroupWidget("Vehicle Controls", embed_title=False)

        self.dirt_group = self._make_segmented_button_group(
            DIRT_OPTIONS,
            "dirtInterval",
        )
        vehicles.add_row("Dirt", self.dirt_group)

        self.auto_engine_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "autoEngineStart",
        )
        vehicles.add_row("Automatic Engine Start", self.auto_engine_group)

        self.stop_go_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "stopAndGoBraking",
        )
        vehicles.add_row("Stop & Go Braking", self.stop_go_group)

        self.trailer_fill_group = self._make_segmented_button_group(
            TOGGLE_OPTIONS,
            "trailerFillLimit",
        )
        vehicles.add_row("Trailer Fill Limit", self.trailer_fill_group)

        self.fuel_usage_group = self._make_segmented_button_group(
            FUEL_USAGE_OPTIONS,
            "fuelUsage",
        )
        vehicles.add_row("Fuel Usage", self.fuel_usage_group)

        return vehicles

    def _build_ai_workers_group(self) -> SettingsGroupWidget:
        ai = SettingsGroupWidget("AI Workers", embed_title=False)

        self.ai_fuel_group = self._make_segmented_button_group(
            AI_REFILL_OPTIONS,
            "aiRefillFuel",
        )
        ai.add_row("AI Worker Refill - Fuel", self.ai_fuel_group)

        self.ai_seeds_group = self._make_segmented_button_group(
            AI_REFILL_OPTIONS,
            "aiRefillSeeds",
        )
        ai.add_row("AI Worker Refill - Seeds", self.ai_seeds_group)

        self.ai_fertilizer_group = self._make_segmented_button_group(
            AI_REFILL_OPTIONS,
            "aiRefillFertilizer",
        )
        ai.add_row("AI Worker Refill - Fertilizer", self.ai_fertilizer_group)

        self.ai_slurry_group = self._make_segmented_button_group(
            AI_REFILL_OPTIONS,
            "aiRefillSlurry",
        )
        ai.add_row("AI Worker Refill - Slurry", self.ai_slurry_group)

        self.ai_manure_group = self._make_segmented_button_group(
            AI_REFILL_OPTIONS,
            "aiRefillManure",
        )
        ai.add_row("AI Worker Refill - Manure", self.ai_manure_group)

        return ai

    def _make_line_edit(self, setting_key: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText("Enter a name for this farm")
        edit.setStyleSheet(
            "QLineEdit { background: #0e1116; color: #ffffff; border: 1px solid #161a21; border-radius: 10px; padding: 10px; }"
            "QLineEdit:focus { border-color: #3f7d51; background: #161a21; }"
        )
        edit.textChanged.connect(lambda value, key=setting_key: self._on_text_changed(key, value))
        return edit

    def _make_segmented_button_group(self, options: list[tuple[str, int]], setting_key: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        button_group = QButtonGroup(self)
        self._button_groups[setting_key] = button_group

        for label, value in options:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty("segment", value)
            button.setStyleSheet(self._segment_button_stylesheet())
            button.clicked.connect(lambda checked, key=setting_key, val=value: self._on_segmented_changed(key, val))
            layout.addWidget(button)
            button_group.addButton(button)

        return container

    def _make_dropdown(self, options: list[str], setting_key: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(options)
        combo.currentTextChanged.connect(lambda value, key=setting_key: self._on_dropdown_changed(key, value))
        combo.setStyleSheet(
            "QComboBox { background: #0e1116; color: #c2c9d3; padding: 8px; border-radius: 10px; border: 1px solid #2b313b; }"
            "QComboBox QAbstractItemView { background: #161a21; color: #c2c9d3; selection-background-color: #3f7d51; }"
        )
        return combo

    def _make_segmented_with_custom(self, options: list[tuple[str, int]], setting_key: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        button_group = QButtonGroup(self)
        self._button_groups[setting_key] = button_group

        for label, value in options:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty("segment", value)
            button.setStyleSheet(self._segment_button_stylesheet())
            button.clicked.connect(lambda checked, key=setting_key, val=value: self._on_segmented_changed(key, val))
            layout.addWidget(button)
            button_group.addButton(button)

        custom_input = QLineEdit()
        custom_input.setPlaceholderText("")
        custom_input.setFixedWidth(100)
        custom_input.setStyleSheet(
            "QLineEdit { background: #0e1116; color: #ffffff; border: 1px solid #161a21; border-radius: 10px; padding: 8px; }"
            "QLineEdit:focus { border-color: #3f7d51; background: #161a21; }"
        )
        custom_input.textChanged.connect(lambda value, key=setting_key: self._on_custom_value_changed(key, value))
        layout.addWidget(custom_input)
        self._custom_inputs[setting_key] = custom_input

        return container



    def _make_slider_with_label(self, minimum: int, maximum: int, setting_key: str, step: int = 1) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setSingleStep(step)
        slider.setStyleSheet("QSlider::handle:horizontal {background: #3f7d51; width: 14px;}")
        layout.addWidget(slider, stretch=1)

        value_label = QLabel(str(minimum))
        value_label.setStyleSheet("color: #d5dbe3; min-width: 40px;")
        layout.addWidget(value_label)

        slider.valueChanged.connect(lambda value, key=setting_key, label=value_label: self._on_slider_changed(key, value, label))

        self._slider_labels[setting_key] = value_label
        self._sliders[setting_key] = slider
        return container

    def _segment_button_stylesheet(self) -> str:
        return (
            "QPushButton {"
            "background-color: #0e1116;"
            "color: #c2c9d3;"
            "border: 1px solid #2b313b;"
            "border-radius: 8px;"
            "padding: 8px 14px;"
            "}"
            "QPushButton:checked {"
            "background-color: #3f7d51;"
            "color: white;"
            "border-color: #5a9e6b;"
            "}"
            "QPushButton:hover {"
            "background-color: #161a21;"
            "}"
        )

    def _on_text_changed(self, key: str, value: str):
        self.session.settings[key] = value

    def _on_segmented_changed(self, key: str, value: int):
        self.session.settings[key] = value
        self._clear_custom_input_if_needed(key, value)

    def _on_slider_changed(self, key: str, value: int, label: QLabel):
        self.session.settings[key] = value
        label.setText(str(value))

    def _on_dropdown_changed(self, key: str, value: str):
        self.session.settings[key] = value

    def _on_custom_value_changed(self, key: str, value: str):
        if value.strip():
            try:
                self.session.settings[key] = int(value.replace("$", "").replace(",", ""))
            except ValueError:
                pass

    def _clear_custom_input_if_needed(self, key: str, selected_value: int):
        custom_input = self._custom_inputs.get(key)
        if custom_input and custom_input.text():
            custom_input.blockSignals(True)
            custom_input.clear()
            custom_input.blockSignals(False)

    def _load_values(self):
        settings = self.session.settings

        if "savegameName" in settings:
            self.savegame_name_input.setText(str(settings["savegameName"]))

        self._restore_segmented_value("difficulty", settings.get("difficulty", 2))
        self._restore_segmented_value("autoSaveInterval", settings.get("autoSaveInterval", 0))

        if "timeScale" in settings:
            idx = self.time_scale_dropdown.findText(str(settings["timeScale"]))
            if idx >= 0:
                self.time_scale_dropdown.setCurrentIndex(idx)

        if "money" in settings:
            self._restore_segmented_value("money", settings.get("money", 50000))
            self._custom_inputs.get("money") and self._custom_inputs["money"].setText(str(settings["money"]))

        if "loan" in settings:
            self._restore_segmented_value("loan", settings.get("loan", 0))
            self._custom_inputs.get("loan") and self._custom_inputs["loan"].setText(str(settings["loan"]))

        if "trafficEnabled" in settings:
            self._restore_segmented_value("trafficEnabled", settings["trafficEnabled"])

        if "snowEnabled" in settings:
            self._restore_segmented_value("snowEnabled", settings["snowEnabled"])

        self._restore_segmented_value("dirtInterval", settings.get("dirtInterval", 1))

        # Restore Seasons settings
        self._restore_segmented_value("seasonalGrowth", settings.get("seasonalGrowth", 1))
        self._restore_slider_value("daysPerMonth", settings.get("daysPerMonth", 1))
        self._restore_segmented_value("fixedVisualMonth", settings.get("fixedVisualMonth", False))

        # Restore Crops and Growth settings
        self._restore_segmented_value("cropDestruction", settings.get("cropDestruction", False))
        self._restore_segmented_value("plowingRequired", settings.get("plowingRequired", True))
        self._restore_segmented_value("fieldstoneEnabled", settings.get("fieldstoneEnabled", True))
        self._restore_segmented_value("limeRequired", settings.get("limeRequired", True))
        self._restore_segmented_value("weedsEnabled", settings.get("weedsEnabled", True))
        self._restore_segmented_value("disasterDestruction", settings.get("disasterDestruction", 0))

        # Restore Vehicle settings
        self._restore_segmented_value("dirtInterval", settings.get("dirtInterval", 1))
        self._restore_segmented_value("autoEngineStart", settings.get("autoEngineStart", True))
        self._restore_segmented_value("stopAndGoBraking", settings.get("stopAndGoBraking", True))
        self._restore_segmented_value("trailerFillLimit", settings.get("trailerFillLimit", False))
        self._restore_segmented_value("fuelUsage", settings.get("fuelUsage", 2))

        # Restore AI Workers settings
        self._restore_segmented_value("aiRefillFuel", settings.get("aiRefillFuel", 0))
        self._restore_segmented_value("aiRefillSeeds", settings.get("aiRefillSeeds", 0))
        self._restore_segmented_value("aiRefillFertilizer", settings.get("aiRefillFertilizer", 0))
        self._restore_segmented_value("aiRefillSlurry", settings.get("aiRefillSlurry", 0))
        self._restore_segmented_value("aiRefillManure", settings.get("aiRefillManure", 0))

    def _restore_segmented_value(self, key: str, value: int):
        button_group = self._button_groups.get(key)
        if not button_group:
            return
        for button in button_group.buttons():
            if button.property("segment") == value:
                button.setChecked(True)
            else:
                button.setChecked(False)

    def _restore_slider_value(self, key: str, value: int):
        slider = self._sliders.get(key)
        label = self._slider_labels.get(key)
        if slider:
            slider.setValue(int(value))
        if label:
            label.setText(str(value))

    def showEvent(self, event):
        super().showEvent(event)
        self._load_values()