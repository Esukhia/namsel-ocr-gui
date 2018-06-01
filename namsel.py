from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys
import os
from tempfile import gettempdir
from shutil import copy, rmtree

import gettext

from re import sub
import docx

# Sharing folders with PyInstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

languages = {
    "bo":gettext.translation("namsel-ocr-gui", localedir=resource_path("locales"), languages=["bo"]),
    "en":gettext.translation("namsel-ocr-gui", localedir=resource_path("locales"), languages=["en"]),
    "fr":gettext.translation("namsel-ocr-gui", localedir=resource_path("locales"), languages=["fr"]),
    "zh_CN":gettext.translation("namsel-ocr-gui", localedir=resource_path("locales"), languages=["zhs"]),
    "zh_TW":gettext.translation("namsel-ocr-gui", localedir=resource_path("locales"), languages=["zht"])
}
lang = languages["en"]
work_directory = os.path.join(gettempdir(), "namsel")
print("\nWorking directory: %s" % work_directory)

def setEnvironment():
    global docker

    for l in [l for i, l in languages.items() if l]:
        l.install()

    if os.path.isdir(work_directory):
        rmtree(work_directory)
    os.mkdir(work_directory)
    os.chdir(work_directory)

    docker = Docker("thubtenrigzin/docker-namsel-ocr:latest", "namsel-ocr")

class Docker(object):
    def __init__(self, namsel_ocr_image, namsel_ocr_container):
        self.etat = ""
        self.docker_process = QProcess()

        if "\\" in work_directory:
            docker_namsel_path = "/" + work_directory[:1].lower()+work_directory[1:].replace("\\", "/").replace(":/", "/")

        self.etat = "Init"
        print(lang.gettext("\nRunning the container..."))
        self.docker_process.start("docker run -itd --rm --name "+namsel_ocr_container+" -v "\
                                  +docker_namsel_path+":/home/namsel-ocr/data "\
                                  +namsel_ocr_image+" bash")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        self.etat = ""
        print(lang.gettext("Docker Namsel Ocr is now running!\n"))

    def preprocess(self, arg={}):
        arg["page_type"] = arg ["line_break_method"] = ""
        self.exec(text="Preprocess is running...", param="preprocess", arg=arg)

    def ocr(self, arg={}):
        self.exec(text="Ocr is running...", param="recognize-volume --format text", arg=arg)

    def exec(self, text="", param="", arg={}):
        arg = " " + " ".join(["--" + k + " " + str(v) for k, v in arg.items() if v])
        print(lang.gettext("\n" + text))
        #print(arg)
        self.docker_process.start("docker exec namsel-ocr ./namsel-ocr " + param + arg)

    def stop(self):
        print(lang.gettext("\nStopping the container..."))
        self.etat = "Stop"
        self.docker_process.start("docker stop namsel-ocr")
        self.docker_process.waitForFinished()

    def endProcess(self):
        self.docker_process.close()
        if self.etat == "Stop":
            print(lang.gettext("The container has been stopped and cleared!\n"))
        else:
            print(lang.gettext("...is now finished!"))
        self.etat = ""

class NamselOcr(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(NamselOcr, self).__init__(*args, **kwargs)

        self.arg = {"threshold":"","layout":"","page_type":"pecha","line_break_method":"line_cluster",\
                        "clear_hr":"", "low_ink":"", "break_width":""}
        self.petat = self.oetat = self.aetat = ""
        self.pvolume = False
        self.aloop = 0
        self.athreshold = [0]

        # Title
        self.setWindowTitle(lang.gettext("Namsel Ocr"))

        # Set the statusbar on
        self.setStatusBar(QStatusBar(self))

        # Size : 70 % of the screen
        self.dw = QDesktopWidget()
        self.x_wsize = self.dw.width() * 0.7
        self.y_wsize = self.dw.height() * 0.7
        self.setFixedSize(self.x_wsize, self.y_wsize)

        # Menu
        self.menu = self.menuBar()
        self.menu.setNativeMenuBar(False)
            # File
        self.file_menu = self.menu.addMenu(lang.gettext("&File"))
        self.new_subaction = QAction(lang.gettext("New"), self)
        self.new_subaction.setStatusTip(lang.gettext("Open a new window"))
        self.open_file_subaction = QAction(lang.gettext("open an image..."), self)
        self.open_file_subaction.setStatusTip(lang.gettext("Open a scan image file"))
        self.open_dir_subaction = QAction(lang.gettext("Select a directory..."), self)
        self.open_dir_subaction.setStatusTip(lang.gettext("Select a directory containing the images of a volume"))
        self.exit_subaction = QAction(lang.gettext("Exit"), self)
        self.exit_subaction.setStatusTip(lang.gettext("Exit Namsel OCR"))
        self.file_menu.addAction(self.new_subaction)
        self.file_menu.addAction(self.open_file_subaction)
        self.file_menu.addAction(self.open_dir_subaction)
        self.file_menu.addAction(self.exit_subaction)
            # Edit
        self.edit_menu = self.menu.addMenu(lang.gettext("&Edit"))
        self.pref_subaction = QAction(lang.gettext("Preferences..."), self)
        self.pref_subaction.setStatusTip(lang.gettext("Preprocess and Ocr settings..."))
        self.edit_menu.addAction(self.pref_subaction)
            # Options
        self.option_menu = self.menu.addMenu(lang.gettext("&Option"))
                # Modes
        self.mode_subactiongroup = QActionGroup(self)
        self.auto_subaction = QAction(lang.gettext("Auto mode"), self)
        self.auto_subaction.setStatusTip(lang.gettext("open the auto mode window"))
        self.prep_subaction = QAction(lang.gettext("Preprocess mode"), self)
        self.prep_subaction.setStatusTip(lang.gettext("open the preprocess mode window"))
        self.ocr_subaction = QAction(lang.gettext("Ocr mode"), self)
        self.ocr_subaction.setStatusTip(lang.gettext("open the ocr mode window"))
        self.convert_subaction = QAction(lang.gettext("Convert mode"), self)
        self.convert_subaction.setStatusTip(lang.gettext("Convert the result file to a final clean state."))
        self.auto_subaction.setCheckable(True)
        self.prep_subaction.setCheckable(True)
        self.ocr_subaction.setCheckable(True)
        self.mode_subactiongroup.addAction(self.auto_subaction)
        self.mode_subactiongroup.addAction(self.prep_subaction)
        self.mode_subactiongroup.addAction(self.ocr_subaction)
        self.prep_subaction.setChecked(True)
        self.option_menu.addActions(self.mode_subactiongroup.actions())
        self.option_menu.addSeparator()
                # Language
        self.lang_submenu = self.option_menu.addMenu(lang.gettext("&Language"))
        self.lang_subactiongroup = QActionGroup(self)
                    #Tibetan
        self.bo_lang_subaction = QAction("བོད་ཡིག", self)
        self.bo_lang_subaction.setIconText("bo")
        self.font = QFont()
        self.font.setFamily('Microsoft Himalaya')
        self.bo_lang_subaction.setFont(self.font)
                    # Other languages
        self.en_lang_subaction = QAction("English", self)
        self.en_lang_subaction.setIconText("en")
        self.fr_lang_subaction = QAction("Français", self)
        self.fr_lang_subaction.setIconText("fr")
        self.zhs_lang_subaction = QAction("简体字", self)
        self.zhs_lang_subaction.setIconText("zh_CN")
        self.zht_lang_subaction = QAction("繁體字", self)
        self.zht_lang_subaction.setIconText("zh_TW")
        self.lang_subactiongroup.addAction(self.bo_lang_subaction)
        self.lang_subactiongroup.addAction(self.en_lang_subaction)
        self.lang_subactiongroup.addAction(self.fr_lang_subaction)
        self.lang_subactiongroup.addAction(self.zhs_lang_subaction)
        self.lang_subactiongroup.addAction(self.zht_lang_subaction)

        for c in self.lang_subactiongroup.actions():
            if c.iconText() == lang.info()["language"]:
                c.setCheckable(True)
                c.setChecked(True)

        self.lang_submenu.addActions(self.lang_subactiongroup.actions())
            # ?
        self.help_menu = self.menu.addMenu(lang.gettext("&?"))
        self.about_subaction = QAction(lang.gettext("About..."), self)
        self.about_subaction.setStatusTip(lang.gettext("Version & credits of Namsel Ocr"))
        self.help_menu.addAction(self.about_subaction)
        self.help_subaction = QAction(lang.gettext("help..."), self)
        self.help_subaction.setStatusTip(lang.gettext("Some useful helps"))
        self.help_menu.addAction(self.help_subaction)

        # Page
            # Auto mode, Preprocess & Ocr page
                # Auto mode
                    # Option
                        # Pecha - Book radiobuttons
        self.a_option_pecha_button = QRadioButton(lang.gettext("Pecha"))
        self.a_option_pecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.a_option_book_button = QRadioButton(lang.gettext("Book"))
        self.a_option_book_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.a_option_pecha_button.setCheckable(True)
        self.a_option_book_button.setCheckable(True)
        self.a_option_pecha_button.setChecked(True)

        self.a_option_pecha_book_layout = QVBoxLayout()
        self.a_option_pecha_book_layout.addWidget(self.a_option_pecha_button)
        self.a_option_pecha_book_layout.addWidget(self.a_option_book_button)

        self.a_option_pecha_book_group = QGroupBox()
        self.a_option_pecha_book_group.setLayout(self.a_option_pecha_book_layout)

                        # Low ink
        self.a_option_lowink_check = QCheckBox(lang.gettext("Low ink"))
        self.a_option_lowink_check.setStatusTip(lang.gettext("Check if the scan image is a bit of low quality"))

        self.a_option_lowink_layout = QVBoxLayout()
        self.a_option_lowink_layout.addWidget(self.a_option_lowink_check)

        self.a_option_lowink_group = QGroupBox()
        self.a_option_lowink_group.setLayout(self.a_option_lowink_layout)

                        # Checks and manual
                            # Automatic checks
                                # Choice
        self.a_option_auto_choice_m40_check = QCheckBox(lang.gettext("-40"))
        self.a_option_auto_choice_m30_check = QCheckBox(lang.gettext("-30"))
        self.a_option_auto_choice_m20_check = QCheckBox(lang.gettext("-20"))
        self.a_option_auto_choice_m10_check = QCheckBox(lang.gettext("-10"))
        self.a_option_auto_choice_0_check = QCheckBox(lang.gettext("0"))
        self.a_option_auto_choice_p10_check = QCheckBox(lang.gettext("+10"))
        self.a_option_auto_choice_p20_check = QCheckBox(lang.gettext("+20"))
        self.a_option_auto_choice_p30_check = QCheckBox(lang.gettext("+30"))
        self.a_option_auto_choice_p40_check = QCheckBox(lang.gettext("+40"))

        self.a_option_auto_choice_m40_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -40"))
        self.a_option_auto_choice_m30_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -30"))
        self.a_option_auto_choice_m20_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -20"))
        self.a_option_auto_choice_m10_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -10"))
        self.a_option_auto_choice_0_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 0"))
        self.a_option_auto_choice_p10_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 10"))
        self.a_option_auto_choice_p20_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 20"))
        self.a_option_auto_choice_p30_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 30"))
        self.a_option_auto_choice_p40_check.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 40"))

        self.a_option_auto_choice_0_check.setDisabled(True)
        self.a_option_auto_choice_0_check.setChecked(True)

        self.a_option_auto_choice_layout = QHBoxLayout()
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_m40_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_m30_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_m20_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_m10_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_0_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_p10_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_p20_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_p30_check)
        self.a_option_auto_choice_layout.addWidget(self.a_option_auto_choice_p40_check)

        self.a_option_auto_choice_group = QGroupBox()
        self.a_option_auto_choice_group.setFixedHeight(100)
        self.a_option_auto_choice_group.setLayout(self.a_option_auto_choice_layout)

                                # Switch Buttons
        self.a_option_auto_tomanual_button = QPushButton(lang.gettext("Manual"))
        self.a_option_auto_tomanual_button.setStatusTip(lang.gettext("Switch to Manual settings"))
        self.a_option_auto_tomanual_button.setFixedWidth(100)

                            # All together
        self.a_option_auto_choice_tomanual_layer = QVBoxLayout()

        self.a_option_auto_choice_tomanual_widget = QWidget()

        self.a_option_auto_choice_tomanual_layer.addWidget(self.a_option_auto_choice_group)
        self.a_option_auto_choice_tomanual_layer.addWidget(self.a_option_auto_tomanual_button, 0, Qt.AlignCenter)
        self.a_option_auto_choice_tomanual_layer.setContentsMargins(0, 0, 0, 0)
        self.a_option_auto_choice_tomanual_widget.setLayout(self.a_option_auto_choice_tomanual_layer)

                            # Manual settings
                                # Label & Slider
        self.a_option_manual_sliderlabel = QLabel(lang.gettext("Thickness: "))
        self.a_option_manual_sliderlcd = QLCDNumber()
        self.a_option_manual_sliderlcd.setStatusTip(lang.gettext("The thickness value during the preprocess"))
        self.a_option_manual_sliderlcd.setSegmentStyle(QLCDNumber.Flat)
        self.a_option_manual_sliderlcd.setFixedWidth(40)

        self.a_option_manual_slider = QSlider(Qt.Horizontal)
        self.a_option_manual_slider.setRange(-40, 40)
        self.a_option_manual_slider.setSingleStep(1)
        self.a_option_manual_slider.setTickPosition(QSlider.TicksBelow)
        self.a_option_manual_slider.setTickInterval(5)
        self.a_option_manual_slider.setStatusTip(lang.gettext("Set the thickness of the scan image"))

        self.a_option_manual_sliderlabel_sliderlcd_widget = QWidget()
        self.a_option_manual_sliderlabel_sliderlcd_layout = QHBoxLayout()
        self.a_option_manual_sliderlabel_sliderlcd_layout.addWidget(self.a_option_manual_sliderlabel)
        self.a_option_manual_sliderlabel_sliderlcd_layout.addWidget(self.a_option_manual_sliderlcd)
        self.a_option_manual_sliderlabel_sliderlcd_layout.setAlignment(Qt.AlignCenter)
        self.a_option_manual_sliderlabel_sliderlcd_widget.setLayout(self.a_option_manual_sliderlabel_sliderlcd_layout)

        self.a_option_manual_slider_group = QGroupBox()
        self.a_option_manual_slider_group.setFixedHeight(100)
        self.a_option_manual_slider_layout = QVBoxLayout()
        self.a_option_manual_slider_layout.addWidget(self.a_option_manual_sliderlabel_sliderlcd_widget)
        self.a_option_manual_slider_layout.addWidget(self.a_option_manual_slider)
        self.a_option_manual_slider_group.setLayout(self.a_option_manual_slider_layout)

                                # Switch Buttons
        self.a_option_manual_toauto_button = QPushButton(lang.gettext("Auto"))
        self.a_option_manual_toauto_button.setStatusTip(lang.gettext("Switch to Auto settings"))
        self.a_option_manual_toauto_button.setFixedWidth(100)

                            # All together
        self.a_option_manual_slider_toauto_layout = QVBoxLayout()
        self.a_option_manual_slider_toauto_widget = QWidget()
        
        self.a_option_manual_slider_toauto_layout.addWidget(self.a_option_manual_slider_group)
        self.a_option_manual_slider_toauto_layout.addWidget(self.a_option_manual_toauto_button, 0, Qt.AlignCenter)
        self.a_option_manual_slider_toauto_layout.setContentsMargins(0, 0, 0, 0)
        self.a_option_manual_slider_toauto_widget.setLayout(self.a_option_manual_slider_toauto_layout)

                        # StackedLayout together
        self.a_option_manual_auto_switch_widget = QWidget()
        self.a_option_manual_auto_switch_layout = QStackedLayout(self.a_option_manual_auto_switch_widget)
        self.a_option_manual_auto_switch_layout.addWidget(self.a_option_auto_choice_tomanual_widget)
        self.a_option_manual_auto_switch_layout.addWidget(self.a_option_manual_slider_toauto_widget)

        self.a_option_manual_auto_switch_layout.setCurrentWidget(self.a_option_manual_slider_toauto_widget)

                        # Label and the dial value
        self.a_option_dial_label = QLabel(lang.gettext("Break width: "))
        self.a_option_diallcd = QLCDNumber()
        self.a_option_diallcd.setStatusTip(lang.gettext("The break-Width value"))
        self.a_option_diallcd.setSegmentStyle(QLCDNumber.Flat)
        self.a_option_diallcd.setFixedWidth(40)
        self.a_option_diallcd.display(lang.gettext("Off"))

        self.a_option_dial_label_diallcd__layout = QHBoxLayout()
        self.a_option_dial_label_diallcd__layout.addWidget(self.a_option_dial_label)
        self.a_option_dial_label_diallcd__layout.addWidget(self.a_option_diallcd)
        self.a_option_dial_label_diallcd__layout.setAlignment(Qt.AlignCenter)

                        # QDial
        self.a_option_dial = QDial()
        self.a_option_dial.setRange(0, 8)
        self.a_option_dial.setNotchesVisible(True)
        self.a_option_dial.setStatusTip(lang.gettext("To controls how horizontally-connected stacks will be segmented"))

        self.a_option_dial_layout = QHBoxLayout()
        self.a_option_dial_layout.addLayout(self.a_option_dial_label_diallcd__layout)
        self.a_option_dial_layout.addWidget(self.a_option_dial)

        self.a_option_dial_group = QGroupBox()
        self.a_option_dial_group.setLayout(self.a_option_dial_layout)

                        # Run the Auto mode
        self.a_option_double_page_check = QCheckBox(lang.gettext("Double page"))
        self.a_option_double_page_check.setStatusTip(lang.gettext("The scan image is a double page"))

        self.a_option_clearhr_check = QCheckBox(lang.gettext("Clear HR"))
        self.a_option_clearhr_check.setStatusTip(lang.gettext("The scan image is a double page"))

        self.a_option_run_button = QPushButton(lang.gettext("Run"))
        self.a_option_run_button.setStatusTip(lang.gettext("Run the ocr"))

        self.a_option_double_page_clearhr_layout = QHBoxLayout()
        self.a_option_double_page_clearhr_layout.addWidget(self.a_option_double_page_check)
        self.a_option_double_page_clearhr_layout.addWidget(self.a_option_clearhr_check)

        self.a_option_double_page_clearhr_widget = QWidget()
        self.a_option_double_page_clearhr_widget.setLayout(self.a_option_double_page_clearhr_layout)
        self.a_option_double_page_clearhr_widget.hide()

        self.a_option_double_page_clearhr_run_layout = QVBoxLayout()
        self.a_option_double_page_clearhr_run_layout.addWidget(self.a_option_double_page_clearhr_widget)
        self.a_option_double_page_clearhr_run_layout.addWidget(self.a_option_run_button)

        self.a_option_double_page_clearhr_run_group = QGroupBox()
        self.a_option_double_page_clearhr_run_group.setLayout(self.a_option_double_page_clearhr_run_layout)

                    # Option layout & widget
        self.a_option_layout = QHBoxLayout()
        self.a_option_layout.addWidget(self.a_option_pecha_book_group)
        self.a_option_layout.addWidget(self.a_option_lowink_group)
        self.a_option_layout.addWidget(self.a_option_manual_auto_switch_widget)
        self.a_option_layout.addWidget(self.a_option_dial_group)
        self.a_option_layout.addWidget(self.a_option_double_page_clearhr_run_group)

        self.a_option_widget = QWidget()
        self.a_option_widget.setFixedHeight(160)
        self.a_option_widget.setLayout(self.a_option_layout)

                    # Image-text
                        # Scan image widget
        self.a_scan_image_label1 = QLabel()
        self.a_scan_image_label2 = QLabel()
        self.a_scan_image_label1.setStatusTip(lang.gettext("The scan image"))
        self.a_scan_image_label2.setStatusTip(lang.gettext("The scan image"))

                        # Result text widget & layout
        self.a_result_auto_widget1 = QWidget()
        self.a_result_auto_widget2 = QWidget()

                                # Left
        self.a_result_tool_text_left_widget = QWidget()
                                    # Toolbar for file comparison
        self.a_result_auto_tool_left_widget = QWidget()

        self.a_result_auto_tool_left_m40_radio = QRadioButton("-40")
        self.a_result_auto_tool_left_m30_radio = QRadioButton("-30")
        self.a_result_auto_tool_left_m20_radio = QRadioButton("-20")
        self.a_result_auto_tool_left_m10_radio = QRadioButton("-10")
        self.a_result_auto_tool_left_0_radio = QRadioButton("0")
        self.a_result_auto_tool_left_p10_radio = QRadioButton("10")
        self.a_result_auto_tool_left_p20_radio = QRadioButton("20")
        self.a_result_auto_tool_left_p30_radio = QRadioButton("30")
        self.a_result_auto_tool_left_p40_radio = QRadioButton("40")

        self.a_result_auto_tool_left_m40_radio.hide()
        self.a_result_auto_tool_left_m30_radio.hide()
        self.a_result_auto_tool_left_m20_radio.hide()
        self.a_result_auto_tool_left_m10_radio.hide()
        self.a_result_auto_tool_left_p10_radio.hide()
        self.a_result_auto_tool_left_p20_radio.hide()
        self.a_result_auto_tool_left_p30_radio.hide()
        self.a_result_auto_tool_left_p40_radio.hide()

        self.a_result_auto_tool_left_layout = QHBoxLayout()
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_m40_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_m30_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_m20_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_m10_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_0_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_p10_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_p20_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_p30_radio)
        self.a_result_auto_tool_left_layout.addWidget(self.a_result_auto_tool_left_p40_radio)

        self.a_result_auto_tool_left_widget.setLayout(self.a_result_auto_tool_left_layout)

                                    # Text
        self.a_result_text_left_textedit = QTextEdit()
        self.a_result_text_left_textedit.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_left_textedit.setFont(self.font)
        self.a_result_text_left_textedit.setFontPointSize(18)

        self.a_result_tool_text_left_layout = QVBoxLayout()
        self.a_result_tool_text_left_layout.addWidget(self.a_result_auto_tool_left_widget)
        self.a_result_tool_text_left_layout.addWidget(self.a_result_text_left_textedit)
        self.a_result_tool_text_left_widget.setLayout(self.a_result_tool_text_left_layout)

                                # Right
        self.a_result_tool_text_right_widget = QWidget()
                                    # Toolbar for file comparison
        self.a_result_auto_tool_right_widget = QWidget()

        self.a_result_auto_tool_right_m40_radio = QRadioButton("-40")
        self.a_result_auto_tool_right_m30_radio = QRadioButton("-30")
        self.a_result_auto_tool_right_m20_radio = QRadioButton("-20")
        self.a_result_auto_tool_right_m10_radio = QRadioButton("-10")
        self.a_result_auto_tool_right_0_radio = QRadioButton("0")
        self.a_result_auto_tool_right_p10_radio = QRadioButton("10")
        self.a_result_auto_tool_right_p20_radio = QRadioButton("20")
        self.a_result_auto_tool_right_p30_radio = QRadioButton("30")
        self.a_result_auto_tool_right_p40_radio = QRadioButton("40")

        self.a_result_auto_tool_right_m40_radio.hide()
        self.a_result_auto_tool_right_m30_radio.hide()
        self.a_result_auto_tool_right_m20_radio.hide()
        self.a_result_auto_tool_right_m10_radio.hide()
        self.a_result_auto_tool_right_p10_radio.hide()
        self.a_result_auto_tool_right_p20_radio.hide()
        self.a_result_auto_tool_right_p30_radio.hide()
        self.a_result_auto_tool_right_p40_radio.hide()

        self.a_result_auto_tool_right_layout = QHBoxLayout()
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_m40_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_m30_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_m20_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_m10_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_0_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_p10_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_p20_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_p30_radio)
        self.a_result_auto_tool_right_layout.addWidget(self.a_result_auto_tool_right_p40_radio)

        self.a_result_auto_tool_right_widget.setLayout(self.a_result_auto_tool_right_layout)

                                   # Text
        self.a_result_text_right_textedit = QTextEdit()
        self.a_result_text_right_textedit.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_right_textedit.setFont(self.font)
        self.a_result_text_right_textedit.setFontPointSize(18)

        self.a_result_tool_text_right_layout = QVBoxLayout()
        self.a_result_tool_text_right_layout.addWidget(self.a_result_auto_tool_right_widget)
        self.a_result_tool_text_right_layout.addWidget(self.a_result_text_right_textedit)
        self.a_result_tool_text_right_widget.setLayout(self.a_result_tool_text_right_layout)

                            # Result layer1
        self.a_result_auto_layer1_layout = QHBoxLayout()
        self.a_result_auto_layer1_layout.addWidget(self.a_result_tool_text_left_widget)
        self.a_result_auto_layer1_layout.addWidget(self.a_result_tool_text_right_widget)

        self.a_result_auto_widget1.setLayout(self.a_result_auto_layer1_layout)

                                # Up
        self.a_result_tool_text_up_widget = QWidget()
                                    # Toolbar for file comparison
        self.a_result_auto_tool_up_widget = QWidget()

        self.a_result_auto_tool_up_m40_radio = QRadioButton("-40")
        self.a_result_auto_tool_up_m30_radio = QRadioButton("-30")
        self.a_result_auto_tool_up_m20_radio = QRadioButton("-20")
        self.a_result_auto_tool_up_m10_radio = QRadioButton("-10")
        self.a_result_auto_tool_up_0_radio = QRadioButton("0")
        self.a_result_auto_tool_up_p10_radio = QRadioButton("10")
        self.a_result_auto_tool_up_p20_radio = QRadioButton("20")
        self.a_result_auto_tool_up_p30_radio = QRadioButton("30")
        self.a_result_auto_tool_up_p40_radio = QRadioButton("40")

        self.a_result_auto_tool_up_m40_radio.hide()
        self.a_result_auto_tool_up_m30_radio.hide()
        self.a_result_auto_tool_up_m20_radio.hide()
        self.a_result_auto_tool_up_m10_radio.hide()
        self.a_result_auto_tool_up_p10_radio.hide()
        self.a_result_auto_tool_up_p20_radio.hide()
        self.a_result_auto_tool_up_p30_radio.hide()
        self.a_result_auto_tool_up_p40_radio.hide()

        self.a_result_auto_tool_up_layout = QHBoxLayout()
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_m40_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_m30_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_m20_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_m10_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_0_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_p10_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_p20_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_p30_radio)
        self.a_result_auto_tool_up_layout.addWidget(self.a_result_auto_tool_up_p40_radio)

        self.a_result_auto_tool_up_widget.setLayout(self.a_result_auto_tool_up_layout)

                                    # Text
        self.a_result_text_up_textedit = QTextEdit()
        self.a_result_text_up_textedit.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_up_textedit.setFont(self.font)
        self.a_result_text_up_textedit.setFontPointSize(18)

        self.a_result_tool_text_up_layout = QVBoxLayout()
        self.a_result_tool_text_up_layout.addWidget(self.a_result_auto_tool_up_widget)
        self.a_result_tool_text_up_layout.addWidget(self.a_result_text_up_textedit)
        self.a_result_tool_text_up_widget.setLayout(self.a_result_tool_text_up_layout)

                                # Down
        self.a_result_tool_text_down_widget = QWidget()
                                    # Toolbar for file comparison
        self.a_result_auto_tool_down_widget = QWidget()

        self.a_result_auto_tool_down_m40_radio = QRadioButton("-40")
        self.a_result_auto_tool_down_m30_radio = QRadioButton("-30")
        self.a_result_auto_tool_down_m20_radio = QRadioButton("-20")
        self.a_result_auto_tool_down_m10_radio = QRadioButton("-10")
        self.a_result_auto_tool_down_0_radio = QRadioButton("0")
        self.a_result_auto_tool_down_p10_radio = QRadioButton("10")
        self.a_result_auto_tool_down_p20_radio = QRadioButton("20")
        self.a_result_auto_tool_down_p30_radio = QRadioButton("30")
        self.a_result_auto_tool_down_p40_radio = QRadioButton("40")

        self.a_result_auto_tool_down_m40_radio.hide()
        self.a_result_auto_tool_down_m30_radio.hide()
        self.a_result_auto_tool_down_m20_radio.hide()
        self.a_result_auto_tool_down_m10_radio.hide()
        self.a_result_auto_tool_down_p10_radio.hide()
        self.a_result_auto_tool_down_p20_radio.hide()
        self.a_result_auto_tool_down_p30_radio.hide()
        self.a_result_auto_tool_down_p40_radio.hide()

        self.a_result_auto_tool_down_layout = QHBoxLayout()
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_m40_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_m30_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_m20_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_m10_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_0_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_p10_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_p20_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_p30_radio)
        self.a_result_auto_tool_down_layout.addWidget(self.a_result_auto_tool_down_p40_radio)

        self.a_result_auto_tool_down_widget.setLayout(self.a_result_auto_tool_down_layout)

                                    # Text
        self.a_result_text_down_textedit = QTextEdit()
        self.a_result_text_down_textedit.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_down_textedit.setFont(self.font)
        self.a_result_text_down_textedit.setFontPointSize(18)

        self.a_result_tool_text_down_layout = QVBoxLayout()
        self.a_result_tool_text_down_layout.addWidget(self.a_result_auto_tool_down_widget)
        self.a_result_tool_text_down_layout.addWidget(self.a_result_text_down_textedit)
        self.a_result_tool_text_down_widget.setLayout(self.a_result_tool_text_down_layout)

                            # Result layer2
        self.a_result_auto_layer2_layout = QVBoxLayout()
        self.a_result_auto_layer2_layout.addWidget(self.a_result_tool_text_up_widget)
        self.a_result_auto_layer2_layout.addWidget(self.a_result_tool_text_down_widget)

        self.a_result_auto_widget2.setLayout(self.a_result_auto_layer2_layout)

                            # Auto manual mode
                                # Layer1
                                    # Toolbar
        self.a_result_tool_manual_copy_button1 = QPushButton(lang.gettext("Copy"))
        self.a_result_tool_manual_copy_button1.setStatusTip(lang.gettext("Copy to Clipboard"))
        self.a_result_tool_manual_copy_button1.setFixedWidth(100)
        self.a_result_tool_manual_paste_button1 = QPushButton(lang.gettext("Paste"))
        self.a_result_tool_manual_paste_button1.setStatusTip(lang.gettext("Paste from Clipboard"))
        self.a_result_tool_manual_paste_button1.setFixedWidth(100)
        self.a_result_tool_manual_clean_button1 = QPushButton(lang.gettext("Clean"))
        self.a_result_tool_manual_clean_button1.setStatusTip(lang.gettext("Create a finished and cleaned version of the document"))
        self.a_result_tool_manual_clean_button1.setFixedWidth(100)
        self.a_result_tool_manual_docx_button1 = QPushButton(lang.gettext("(.docx)"))
        self.a_result_tool_manual_docx_button1.setStatusTip(lang.gettext("Create a Word document (.docx) on the Desktop"))
        self.a_result_tool_manual_docx_button1.setFixedWidth(100)

        self.a_result_tool_manual_group_layout1 = QHBoxLayout()
        self.a_result_tool_manual_group_layout1.addWidget(self.a_result_tool_manual_copy_button1)
        self.a_result_tool_manual_group_layout1.addWidget(self.a_result_tool_manual_clean_button1)
        self.a_result_tool_manual_group_layout1.addWidget(self.a_result_tool_manual_paste_button1)
        self.a_result_tool_manual_group_layout1.addWidget(self.a_result_tool_manual_docx_button1)
        self.a_result_tool_manual_group1 = QGroupBox()
        self.a_result_tool_manual_group1.setLayout(self.a_result_tool_manual_group_layout1)

                                    # QTextEdit
        self.a_result_text_manual_textedit1 = QTextEdit()
        self.a_result_text_manual_textedit1.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_manual_textedit1.setFont(self.font)
        self.a_result_text_manual_textedit1.setFontPointSize(18)

                                # Put together
        self.a_result_manual_layout1 = QVBoxLayout()
        self.a_result_manual_layout1.addWidget(self.a_result_tool_manual_group1)
        self.a_result_manual_layout1.addWidget(self.a_result_text_manual_textedit1)

        self.a_result_manual_widget1 = QWidget()
        self.a_result_manual_widget1.setLayout(self.a_result_manual_layout1)

                                # Layer2
                                    # Toolbar
        self.a_result_tool_manual_copy_button2 = QPushButton(lang.gettext("Copy"))
        self.a_result_tool_manual_copy_button2.setStatusTip(lang.gettext("Copy to Clipboard"))
        self.a_result_tool_manual_copy_button2.setFixedWidth(100)
        self.a_result_tool_manual_paste_button2 = QPushButton(lang.gettext("Paste"))
        self.a_result_tool_manual_paste_button2.setStatusTip(lang.gettext("Paste from Clipboard"))
        self.a_result_tool_manual_paste_button2.setFixedWidth(100)
        self.a_result_tool_manual_clean_button2 = QPushButton(lang.gettext("Clean"))
        self.a_result_tool_manual_clean_button2.setStatusTip(lang.gettext("Create a finished and cleaned version of the document"))
        self.a_result_tool_manual_clean_button2.setFixedWidth(100)
        self.a_result_tool_manual_docx_button2 = QPushButton(lang.gettext("(.docx)"))
        self.a_result_tool_manual_docx_button2.setStatusTip(lang.gettext("Create a Word document (.docx) on the Desktop"))
        self.a_result_tool_manual_docx_button2.setFixedWidth(100)

        self.a_result_tool_manual_group_layout2 = QHBoxLayout()
        self.a_result_tool_manual_group_layout2.addWidget(self.a_result_tool_manual_copy_button2)
        self.a_result_tool_manual_group_layout2.addWidget(self.a_result_tool_manual_clean_button2)
        self.a_result_tool_manual_group_layout2.addWidget(self.a_result_tool_manual_paste_button2)
        self.a_result_tool_manual_group_layout2.addWidget(self.a_result_tool_manual_docx_button2)
        self.a_result_tool_manual_group2 = QGroupBox()
        self.a_result_tool_manual_group2.setLayout(self.a_result_tool_manual_group_layout2)

                                    # QTextEdit
        self.a_result_text_manual_textedit2 = QTextEdit()
        self.a_result_text_manual_textedit2.setStatusTip(lang.gettext("The ocr result"))
        self.a_result_text_manual_textedit2.setFont(self.font)
        self.a_result_text_manual_textedit2.setFontPointSize(18)

                                # Put together
        self.a_result_manual_layout2 = QVBoxLayout()
        self.a_result_manual_layout2.addWidget(self.a_result_tool_manual_group2)
        self.a_result_manual_layout2.addWidget(self.a_result_text_manual_textedit2)

        self.a_result_manual_widget2 = QWidget()
        self.a_result_manual_widget2.setLayout(self.a_result_manual_layout2)

                            # Stacklayers
        self.a_result_widget1 = QWidget()

        self.a_result_stacklayout1 = QStackedLayout(self.a_result_widget1)
        self.a_result_stacklayout1.addWidget(self.a_result_auto_widget1)
        self.a_result_stacklayout1.addWidget(self.a_result_manual_widget1)
        self.a_result_stacklayout1.setCurrentWidget(self.a_result_manual_widget1)

        self.a_result_widget1.setLayout(self.a_result_stacklayout1)
        self.a_result_manual_widget1.hide()
        self.a_result_auto_widget1.hide()

        self.a_result_widget2 = QWidget()

        self.a_result_stacklayout2 = QStackedLayout(self.a_result_widget2)
        self.a_result_stacklayout2.addWidget(self.a_result_auto_widget2)
        self.a_result_stacklayout2.addWidget(self.a_result_manual_widget2)
        self.a_result_stacklayout2.setCurrentWidget(self.a_result_manual_widget2)

        self.a_result_widget2.setLayout(self.a_result_stacklayout1)
        self.a_result_manual_widget2.hide()
        self.a_result_auto_widget2.hide()

                    # Image-text layout and widget
        self.a_h_layout = QHBoxLayout()
        self.a_v_layout = QVBoxLayout()

        self.a_v_layout.addWidget(self.a_scan_image_label1)
        self.a_v_layout.addWidget(self.a_result_widget1)

        self.a_h_layout.addWidget(self.a_scan_image_label2)
        self.a_h_layout.addWidget(self.a_result_widget2)

        self.a_widget = QWidget()
        self.a_h_widget = QWidget()
        self.a_v_widget = QWidget()

        self.a_v_widget.setLayout(self.a_v_layout)
        self.a_h_widget.setLayout(self.a_h_layout)

        self.a_staklayout = QStackedLayout(self.a_widget)
        self.a_staklayout.addWidget(self.a_h_widget)
        self.a_staklayout.addWidget(self.a_v_widget)
        self.a_staklayout.setCurrentWidget(self.a_v_widget)

        self.a_widget.setLayout(self.a_staklayout)

                # Ocr page layout & widget
        self.auto_layout = QVBoxLayout()
        self.auto_layout.addWidget(self.a_option_widget)
        self.auto_layout.addWidget(self.a_widget)

        self.autopage_widget = QWidget()
        self.autopage_widget.setLayout(self.auto_layout)

                # Preprocess page
                    # Option
                        # Pecha - Book radiobuttons
        self.p_pecha_button = QRadioButton(lang.gettext("Pecha"))
        self.p_pecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.p_book_button = QRadioButton(lang.gettext("Book"))
        self.p_book_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.p_pecha_button.setCheckable(True)
        self.p_book_button.setCheckable(True)
        self.p_pecha_button.setChecked(True)

        self.p_pecha_book_layout = QVBoxLayout()
        self.p_pecha_book_layout.addWidget(self.p_pecha_button)
        self.p_pecha_book_layout.addWidget(self.p_book_button)

        self.p_pecha_book_group = QGroupBox()
        self.p_pecha_book_group.setLayout(self.p_pecha_book_layout)

                        # Label and the thickness value
        self.p_slabel = QLabel(lang.gettext("Thickness: "))
        self.p_slcd = QLCDNumber()
        self.p_slcd.setStatusTip(lang.gettext("The thickness value during the preprocess"))
        self.p_slcd.setSegmentStyle(QLCDNumber.Flat)
        self.p_slcd.setFixedWidth(40)

        self.p_slabel_slider_layout = QHBoxLayout()
        self.p_slabel_slider_layout.addWidget(self.p_slabel)
        self.p_slabel_slider_layout.addWidget(self.p_slcd)
        self.p_slabel_slider_layout.setAlignment(Qt.AlignCenter)

                        # Thickness slider
        self.p_slider = QSlider(Qt.Horizontal)
        self.p_slider.setRange(-40, 40)
        self.p_slider.setSingleStep(1)
        self.p_slider.setTickPosition(QSlider.TicksBelow)
        self.p_slider.setTickInterval(5)
        self.p_slider.setStatusTip(lang.gettext("Set the thickness of the scan image"))

        self.p_slider_layout = QVBoxLayout()
        self.p_slider_layout.addLayout(self.p_slabel_slider_layout)
        self.p_slider_layout.addWidget(self.p_slider)

        self.p_slider_group = QGroupBox()
        self.p_slider_group.setLayout(self.p_slider_layout)

                        # Run the Preprocess
        self.p_doublepage_checkbox = QCheckBox(lang.gettext("Double page"))
        self.p_doublepage_checkbox.setStatusTip(lang.gettext("The scan image is a double page"))
        self.p_run_button = QPushButton(lang.gettext("Run"))
        self.p_run_button.setStatusTip(lang.gettext("Run the preprocess"))

        self.p_doublepage_layout = QHBoxLayout()
        self.p_doublepage_layout.addWidget(self.p_doublepage_checkbox)

        self.p_doublepage_widget = QWidget()
        self.p_doublepage_widget.setLayout(self.p_doublepage_layout)
        self.p_doublepage_widget.hide()

        self.p_run_layout = QVBoxLayout()
        self.p_run_layout.addWidget(self.p_doublepage_widget)
        self.p_run_layout.addWidget(self.p_run_button)

        self.p_run_group = QGroupBox()
        self.p_run_group.setLayout(self.p_run_layout)

                    # Option layout & widget
        self.p_option_layout = QHBoxLayout()
        self.p_option_layout.addWidget(self.p_pecha_book_group)
        self.p_option_layout.addWidget(self.p_slider_group)
        self.p_option_layout.addWidget(self.p_run_group)

        self.p_option_widget = QWidget()
        self.p_option_widget.setFixedHeight(160)
        self.p_option_widget.setLayout(self.p_option_layout)

                    # Image
                        # Scan image widget
        self.p_scan_image_label1 = QLabel()
        self.p_scan_image_label2 = QLabel()
        self.p_scan_image_label1.setStatusTip(lang.gettext("The scan image"))
        self.p_scan_image_label2.setStatusTip(lang.gettext("The scan image"))

                        # Result image widget
        self.p_result_image_label1 = QLabel()
        self.p_result_image_label2 = QLabel()
        self.p_result_image_label1.setStatusTip(lang.gettext("The result 'scantailored' image"))
        self.p_result_image_label2.setStatusTip(lang.gettext("The result 'scantailored' image"))

                    # Image layout & widget
        self.p_h_layout = QHBoxLayout()
        self.p_v_layout = QVBoxLayout()

        self.p_v_layout.addWidget(self.p_scan_image_label1)
        self.p_v_layout.addWidget(self.p_result_image_label1)

        self.p_h_layout.addWidget(self.p_scan_image_label2)
        self.p_h_layout.addWidget(self.p_result_image_label2)

        self.p_widget = QWidget()
        self.p_v_widget = QWidget()
        self.p_h_widget = QWidget()

        self.p_v_widget.setLayout(self.p_v_layout)
        self.p_h_widget.setLayout(self.p_h_layout)

        self.p_staklayout = QStackedLayout(self.p_widget)
        self.p_staklayout.addWidget(self.p_v_widget)
        self.p_staklayout.addWidget(self.p_h_widget)
        self.p_staklayout.setCurrentWidget(self.p_v_widget)

        self.p_widget.setLayout(self.p_staklayout)

                # Preprocess page layout & widget
        self.prep_layout = QVBoxLayout()
        self.prep_layout.addWidget(self.p_option_widget)
        self.prep_layout.addWidget(self.p_widget)

        self.prep_widget = QWidget()
        self.prep_widget.setLayout(self.prep_layout)

                # Ocr page options
                    # Option
                        # Pecha - Book radiobuttons
        self.o_pecha_button = QRadioButton(lang.gettext("Pecha"))
        self.o_pecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.o_book_button = QRadioButton(lang.gettext("Book"))
        self.o_book_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.o_pecha_button.setCheckable(True)
        self.o_book_button.setCheckable(True)
        self.o_pecha_button.setChecked(True)

        self.o_pecha_book_layout = QVBoxLayout()
        self.o_pecha_book_layout.addWidget(self.o_pecha_button)
        self.o_pecha_book_layout.addWidget(self.o_book_button)

        self.o_pecha_book_group = QGroupBox()
        self.o_pecha_book_group.setLayout(self.o_pecha_book_layout)

                        # Low ink
        self.o_lowink_checkbox = QCheckBox(lang.gettext("Low ink"))
        self.o_lowink_checkbox.setStatusTip(lang.gettext("Check if the scan image is a bit of low quality"))

        self.o_lowink_layout = QVBoxLayout()
        self.o_lowink_layout.addWidget(self.o_lowink_checkbox)

        self.o_lowink_group = QGroupBox()
        self.o_lowink_group.setLayout(self.o_lowink_layout)

                        # Label and the dial value
        self.o_dialabel_label = QLabel(lang.gettext("Break width: "))
        self.o_dlcd = QLCDNumber()
        self.o_dlcd.setStatusTip(lang.gettext("The break-Width value"))
        self.o_dlcd.setSegmentStyle(QLCDNumber.Flat)
        self.o_dlcd.setFixedWidth(40)
        self.o_dlcd.display(lang.gettext("Off"))

        self.o_diallabel_dial_layout = QHBoxLayout()
        self.o_diallabel_dial_layout.addWidget(self.o_dialabel_label)
        self.o_diallabel_dial_layout.addWidget(self.o_dlcd)
        self.o_diallabel_dial_layout.setAlignment(Qt.AlignCenter)

                        # QDial
        self.o_dial = QDial()
        self.o_dial.setRange(0, 8)
        self.o_dial.setNotchesVisible(True)
        self.o_dial.setStatusTip(lang.gettext("To controls how horizontally-connected stacks will be segmented"))

        self.o_dial_layout = QHBoxLayout()
        self.o_dial_layout.addLayout(self.o_diallabel_dial_layout)
        self.o_dial_layout.addWidget(self.o_dial)

        self.o_dial_group = QGroupBox()
        self.o_dial_group.setLayout(self.o_dial_layout)

                        # Run the Ocr
        self.o_clearhr_checkbox = QCheckBox(lang.gettext("Clear HR"))
        self.o_clearhr_checkbox.setStatusTip(lang.gettext("The scan image is a double page"))
        self.o_run_button = QPushButton(lang.gettext("Run"))
        self.o_run_button.setStatusTip(lang.gettext("Run the ocr"))

        self.o_clearhr_layout = QHBoxLayout()
        self.o_clearhr_layout.addWidget(self.o_clearhr_checkbox)

        self.o_clearhr_widget = QWidget()
        self.o_clearhr_widget.setLayout(self.o_clearhr_layout)
        self.o_clearhr_widget.hide()

        self.o_run_layout = QVBoxLayout()
        self.o_run_layout.addWidget(self.o_clearhr_widget)
        self.o_run_layout.addWidget(self.o_run_button)

        self.o_run_group = QGroupBox()
        self.o_run_group.setLayout(self.o_run_layout)

                    # Option layout & widget
        self.o_option_layout = QHBoxLayout()
        self.o_option_layout.addWidget(self.o_pecha_book_group)
        self.o_option_layout.addWidget(self.o_lowink_group)
        self.o_option_layout.addWidget(self.o_dial_group)
        self.o_option_layout.addWidget(self.o_run_group)

        self.o_option_widget = QWidget()
        self.o_option_widget.setFixedHeight(160)
        self.o_option_widget.setLayout(self.o_option_layout)

                    # Image-text
                        # Scan image widget
        self.o_scan_image_label1 = QLabel()
        self.o_scan_image_label2 = QLabel()
        self.o_scan_image_label1.setStatusTip(lang.gettext("The scan image"))
        self.o_scan_image_label2.setStatusTip(lang.gettext("The scan image"))

                        # Result text widget
        self.o_textedit1 = QTextEdit()
        self.o_textedit2 = QTextEdit()
        self.o_textedit1.setStatusTip(lang.gettext("The ocr result"))
        self.o_textedit2.setStatusTip(lang.gettext("The ocr result"))
        self.o_textedit1.setFont(self.font)
        self.o_textedit2.setFont(self.font)
        self.o_textedit1.setFontPointSize(18)
        self.o_textedit2.setFontPointSize(18)
        self.o_textedit1.hide()
        self.o_textedit2.hide()

                    # Image-text layout and widget
        self.o_h_layout = QHBoxLayout()
        self.o_v_layout = QVBoxLayout()

        self.o_v_layout.addWidget(self.o_scan_image_label1)
        self.o_v_layout.addWidget(self.o_textedit1)

        self.o_h_layout.addWidget(self.o_scan_image_label2)
        self.o_h_layout.addWidget(self.o_textedit2)

        self.o_widget = QWidget()
        self.o_v_widget = QWidget()
        self.o_h_widget = QWidget()

        self.o_v_widget.setLayout(self.o_v_layout)
        self.o_h_widget.setLayout(self.o_h_layout)

        self.o_staklayout = QStackedLayout(self.o_widget)
        self.o_staklayout.addWidget(self.o_v_widget)
        self.o_staklayout.addWidget(self.o_h_widget)
        self.o_staklayout.setCurrentWidget(self.o_v_widget)

        self.o_widget.setLayout(self.o_staklayout)

                # Ocr page layout & widget
        self.ocr_layout = QVBoxLayout()
        self.ocr_layout.addWidget(self.o_option_widget)
        self.ocr_layout.addWidget(self.o_widget)

        self.ocr_widget = QWidget()
        self.ocr_widget.setLayout(self.ocr_layout)

            # Joining all the pages together
        self.page_widget = QWidget()
        self.page_staklayout = QStackedLayout(self.page_widget)
        self.page_staklayout.addWidget(self.autopage_widget)
        self.page_staklayout.addWidget(self.prep_widget)
        self.page_staklayout.addWidget(self.ocr_widget)
        self.page_staklayout.setCurrentWidget(self.prep_widget)

        # Showing the default page on screen
        self.setCentralWidget(self.page_widget)

        # Waiting progress dialog
        self.progress = QProgressDialog(None, Qt.WindowTitleHint)
        self.progress.setWindowFlags(self.progress.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.progress.setWindowTitle(lang.gettext("Docker process"))
        self.progress.setCancelButton(None)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setRange(0, 0)
        self.progress.cancel()

        # Links between signals and slots
            # Menu
        self.new_subaction.triggered.connect(self.restart)
        self.open_file_subaction.triggered.connect(self.openScanImage)
        self.open_dir_subaction.triggered.connect(self.openScanDirImage)
        self.exit_subaction.triggered.connect(self.close)
        self.lang_subactiongroup.triggered.connect(self.lang)
            # Auto mode
        self.auto_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.autopage_widget))
        self.a_option_manual_slider.valueChanged.connect(self.a_option_manual_sliderlcd.display)
        self.a_option_auto_tomanual_button.released.connect(self.autoManual)
        self.a_option_manual_toauto_button.released.connect(self.autoAuto)
        self.a_option_dial.valueChanged.connect(lambda x: self.a_option_diallcd.display(x / 2) if x else self.a_option_diallcd.display("Off"))
        self.a_option_book_button.toggled.connect(self.pechabook)
        self.a_option_double_page_check.toggled.connect(self.double)
        self.a_option_run_button.released.connect(self.autoRun)

        self.a_result_auto_tool_left_m40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "-40", x))
        self.a_result_auto_tool_left_m30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "-30", x))
        self.a_result_auto_tool_left_m20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "-20", x))
        self.a_result_auto_tool_left_m10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "-10", x))
        self.a_result_auto_tool_left_0_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "0", x))
        self.a_result_auto_tool_left_p10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "10", x))
        self.a_result_auto_tool_left_p20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "20", x))
        self.a_result_auto_tool_left_p30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "30", x))
        self.a_result_auto_tool_left_p40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_left_textedit, "40", x))

        self.a_result_auto_tool_right_m40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "-40", x))
        self.a_result_auto_tool_right_m30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "-30", x))
        self.a_result_auto_tool_right_m20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "-20", x))
        self.a_result_auto_tool_right_m10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "-10", x))
        self.a_result_auto_tool_right_0_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "0", x))
        self.a_result_auto_tool_right_p10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "10", x))
        self.a_result_auto_tool_right_p20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "20", x))
        self.a_result_auto_tool_right_p30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "30", x))
        self.a_result_auto_tool_right_p40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_right_textedit, "40", x))

        self.a_result_auto_tool_up_m40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "-40", x))
        self.a_result_auto_tool_up_m30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "-30", x))
        self.a_result_auto_tool_up_m20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "-20", x))
        self.a_result_auto_tool_up_m10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "-10", x))
        self.a_result_auto_tool_up_0_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "0", x))
        self.a_result_auto_tool_up_p10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "10", x))
        self.a_result_auto_tool_up_p20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "20", x))
        self.a_result_auto_tool_up_p30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "30", x))
        self.a_result_auto_tool_up_p40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_up_textedit, "40", x))

        self.a_result_auto_tool_down_m40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "-40", x))
        self.a_result_auto_tool_down_m30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "-30", x))
        self.a_result_auto_tool_down_m20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "-20", x))
        self.a_result_auto_tool_down_m10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "-10", x))
        self.a_result_auto_tool_down_0_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "0", x))
        self.a_result_auto_tool_down_p10_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "10", x))
        self.a_result_auto_tool_down_p20_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "20", x))
        self.a_result_auto_tool_down_p30_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "30", x))
        self.a_result_auto_tool_down_p40_radio.toggled.connect(lambda x: self.comparison(self.a_result_text_down_textedit, "40", x))

        self.a_result_tool_manual_copy_button1.released.connect(self.copy)
        self.a_result_tool_manual_copy_button2.released.connect(self.copy)
        self.a_result_tool_manual_clean_button1.released.connect(self.clean)
        self.a_result_tool_manual_clean_button2.released.connect(self.clean)
        self.a_result_tool_manual_paste_button1.released.connect(self.paste)
        self.a_result_tool_manual_paste_button2.released.connect(self.paste)
        self.a_result_tool_manual_docx_button1.released.connect(self.docx)
        self.a_result_tool_manual_docx_button2.released.connect(self.docx)

            # Preprocess mode
        self.prep_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.prep_widget))
        self.p_slider.valueChanged.connect(self.p_slcd.display)
        self.p_book_button.toggled.connect(self.pechabook)
        self.p_doublepage_checkbox.toggled.connect(self.double)
        self.p_run_button.released.connect(self.preprocessRun)
            # Ocr mode
        self.ocr_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.ocr_widget))
        self.o_dial.valueChanged.connect(lambda x: self.o_dlcd.display(x / 2) if x else self.o_dlcd.display("Off"))
        self.o_book_button.toggled.connect(self.pechabook)
        self.o_run_button.released.connect(self.ocrRun)
            # Docker
        docker.docker_process.finished.connect(self.processFinished)

    def autoManual(self):
        self.a_option_manual_auto_switch_layout.setCurrentWidget(self.a_option_manual_slider_toauto_widget)
        self.a_result_stacklayout1.setCurrentWidget(self.a_result_manual_widget1)
        self.a_result_stacklayout2.setCurrentWidget(self.a_result_manual_widget2)

        if self.a_result_text_manual_textedit1.toPlainText() == "":
            self.a_result_manual_widget1.hide()
            self.a_result_manual_widget2.hide()

    def autoAuto(self):
        self.a_option_manual_auto_switch_layout.setCurrentWidget(self.a_option_auto_choice_tomanual_widget)
        self.a_result_stacklayout1.setCurrentWidget(self.a_result_auto_widget1)
        self.a_result_stacklayout2.setCurrentWidget(self.a_result_auto_widget2)

        if self.a_result_text_left_textedit.toPlainText() == "":
            self.a_result_auto_widget1.hide()
            self.a_result_auto_widget2.hide()

    def copy(self):
        data = self.a_result_text_manual_textedit1.toPlainText()
        QApplication.clipboard().setText(data)

    def clean(self):
        data = self.a_result_text_manual_textedit1.toPlainText()
        data = sub(r"(OCR text\n)|(\n.*?.tif\n)|(་)\n", r"\3", data)
        data = sub(r"([ག།])\n", r"\1 ", data)
        data = sub(r"\n\n", "", data)
        data = sub(r"(༄|.༅)", r"\n\1", data)
        self.o_textedit1.setText(data)
        self.o_textedit2.setText(data)
        self.a_result_text_manual_textedit1.setText(data)
        self.a_result_text_manual_textedit2.setText(data)

    def paste(self):
        data = QApplication.clipboard().text()
        self.o_textedit1.setText(data)
        self.o_textedit2.setText(data)
        self.a_result_text_manual_textedit1.setText(data)
        self.a_result_text_manual_textedit2.setText(data)

    def docx(self):
        data = self.a_result_text_manual_textedit1.toPlainText()
        word_file = docx.Document()
        word_file.add_paragraph(data)
        word_file.save(os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop', 'namsel-ocr.docx'))
        del word_file

    def comparison(self, pos, button, e):
        if e:
            self.scan_image_name_temp = button + "_ocr_output.txt"
            with open(self.scan_image_name_temp, "r", encoding="utf-8") as file:
                data = file.read()
            pos.setText(data)

    def pechabook(self, e):
        if e:
            if not self.p_doublepage_checkbox.isChecked() and not self.a_option_double_page_check.isChecked():
                self.p_staklayout.setCurrentWidget(self.p_h_widget)

                if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
                    self.a_result_stacklayout1.setCurrentWidget(self.a_result_auto_widget1)
                else:
                    self.a_result_stacklayout1.setCurrentWidget(self.a_result_manual_widget1)
                self.a_staklayout.setCurrentWidget(self.a_h_widget)

            if self.petat == "Result" and self.p_doublepage_checkbox.isChecked():
                self.p_staklayout.setCurrentWidget(self.p_v_widget)
            else:
                self.o_staklayout.setCurrentWidget(self.o_h_widget)

            self.p_doublepage_widget.show()
            self.o_clearhr_widget.show()
            self.a_option_double_page_clearhr_widget.show()
            self.p_book_button.setChecked(True)
            self.o_book_button.setChecked(True)
            self.a_option_book_button.setChecked(True)
        else:
            self.p_staklayout.setCurrentWidget(self.p_v_widget)
            self.o_staklayout.setCurrentWidget(self.o_v_widget)

            if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
                self.a_result_stacklayout2.setCurrentWidget(self.a_result_auto_widget2)
            else:
                self.a_result_stacklayout2.setCurrentWidget(self.a_result_manual_widget2)
            self.a_staklayout.setCurrentWidget(self.a_v_widget)

            self.p_doublepage_widget.hide()
            self.o_clearhr_widget.hide()
            self.a_option_double_page_clearhr_widget.hide()
            self.p_pecha_button.setChecked(True)
            self.o_pecha_button.setChecked(True)
            self.a_option_pecha_button.setChecked(True)

    def double(self, e):
        if e:
            self.p_staklayout.setCurrentWidget(self.p_v_widget)
            self.o_staklayout.setCurrentWidget(self.o_v_widget)

            if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
                self.a_result_stacklayout2.setCurrentWidget(self.a_result_auto_widget2)
            else:
                self.a_result_stacklayout2.setCurrentWidget(self.a_result_manual_widget2)
            self.a_staklayout.setCurrentWidget(self.a_v_widget)

            self.p_doublepage_checkbox.setChecked(True)
            self.a_option_double_page_check.setChecked(True)
        else:
            self.p_staklayout.setCurrentWidget(self.p_h_widget)
            self.o_staklayout.setCurrentWidget(self.o_h_widget)

            if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
                self.a_result_stacklayout1.setCurrentWidget(self.a_result_auto_widget1)
            else:
                self.a_result_stacklayout1.setCurrentWidget(self.a_result_manual_widget1)
            self.a_staklayout.setCurrentWidget(self.a_h_widget)

            self.p_doublepage_checkbox.setChecked(False)
            self.a_option_double_page_check.setChecked(False)

    def openScanImage(self, folder="", multi=True):
        if self.petat == "Scan":
            self.scan_image_name_temp = self.scan_image_name

        self.dialog_etat = False
        if not folder: folder = "/"

        if multi:
            self.scan_image_name, _ = QFileDialog.getOpenFileNames(self, lang.gettext("Open the source scan image..."),\
                                                              folder, lang.gettext("Image files (*.tif)"))
        else:
            self.scan_image_name, _ = QFileDialog.getOpenFileName(self, lang.gettext("Open the source scan image..."), \
                                                                   folder, lang.gettext("Image files (*.tif)"))
        if self.scan_image_name:
            if multi:
                self.scan_image_name1 = self.scan_image_name[0]
            else:
                self.scan_image_name1 = self.scan_image_name

            self.dialog_etat = True

            if self.petat == "Result":
                self.p_result_image_label1.clear()
                self.p_result_image_label2.clear()
                self.delOutDir()

            if self.oetat == "Ocr":
                self.o_textedit1.hide()
                self.o_textedit2.hide()
                self.o_textedit1.clear()
                self.o_textedit2.clear()
                self.a_result_manual_widget1.hide()
                self.a_result_manual_widget2.hide()
                self.a_result_text_left_textedit.clear()
                self.a_result_text_right_textedit.clear()
                self.a_result_text_up_textedit.clear()
                self.a_result_text_down_textedit.clear()
                self.a_result_auto_widget1.hide()
                self.a_result_auto_widget2.hide()
                self.a_result_text_manual_textedit1.clear()
                self.a_result_text_manual_textedit2.clear()
                self.delOutDir()
                self.delFiles()

            self.psimage = QPixmap(self.scan_image_name1)
            self.p_scan_image_label1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.p_scan_image_label2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.o_scan_image_label1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.o_scan_image_label2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.a_scan_image_label1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.a_scan_image_label2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))

            self.petat = "Scan"

        elif self.petat == "Scan":
            self.scan_image_name = self.scan_image_name_temp

    def openScanDirImage(self):
        if self.pvolume:
            self.scan_folder_name_temp = self.scan_folder_name
        self.scan_folder_name = QFileDialog.getExistingDirectory(self, lang.gettext(
            "Open a directory containing the scan images of a volume..."), "")
        if self.scan_folder_name:
            self.pvolume = True
            self.openScanImage(self.scan_folder_name)
        elif self.pvolume:
            self.scan_folder_name = self.scan_folder_name_temp

    def preprocessRun(self):
        if self.petat == "" or self.petat == "Result":
            self.openScanImage()

        if self.petat == "Scan":
            if self.pvolume == False:
                for f in self.scan_image_name:
                    copy(f, work_directory)
            else:
                for f in os.listdir(self.scan_folder_name):
                    if f.endswith(".tif"):
                        while True:
                            ack = copy(os.path.join(self.scan_folder_name, f), work_directory)
                            if ack.find(f): break

            if self.p_slider.value():
                self.arg["threshold"] = self.p_slider.value()
            else:
                self.arg["threshold"] = 0
            if self.p_doublepage_checkbox.isChecked():
                self.arg["layout"] = "double"

            docker.etat = "Preprocess"
            docker.preprocess(self.arg)

            self.scan_image_filename = QFileInfo(self.scan_image_name[0]).fileName()
            nb_files = len(self.scan_image_name)

            if self.pvolume:
                txt = self.scan_folder_name + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                self.pvolume = False
            elif nb_files > 1:
                txt = str(nb_files) + " image files\n\n" + "Thickness: " + str(self.arg["threshold"])
            else:
                txt = self.scan_image_filename + "\n\n" + "Thickness: " + str(self.arg["threshold"])
            self.wait(txt)

    def ocrRun(self):
        if self.petat == "" or self.oetat == "Ocr":
            self.openScanImage()

        if self.dialog_etat:
            if self.petat == "Scan":
                for f in self.scan_image_name:
                    copy(f, work_directory)

            if self.o_book_button.isChecked():
                self.arg["page_type"] = "book"
                self.arg["line_break_method"] = "line_cut"
                if self.o_clearhr_checkbox.isChecked(): self.arg["clear_hr"] = True
            if self.o_lowink_checkbox.isChecked(): self.arg["low_ink"] = True
            if self.o_dial.value(): self.arg["break_width"] = self.o_dial.value() / 2

            docker.etat = "Ocr"
            docker.ocr(self.arg)
            self.wait()

    def autoRun(self):
        if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
            if self.aetat == "Ocr" or (self.aetat == "" and self.petat != "Scan"):
                self.openScanImage(multi=False)

            if self.dialog_etat and self.aetat != "Result":
                if len(self.athreshold) == 1:
                    if self.a_option_auto_choice_m40_check.isChecked():
                        self.athreshold.append(-40)
                        self.a_result_auto_tool_left_m40_radio.show()
                        self.a_result_auto_tool_right_m40_radio.show()
                        self.a_result_auto_tool_up_m40_radio.show()
                        self.a_result_auto_tool_down_m40_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_m40_radio
                        self.atext2_down = self.a_result_auto_tool_down_m40_radio

                    if self.a_option_auto_choice_m30_check.isChecked():
                        self.athreshold.append(-30)
                        self.a_result_auto_tool_left_m30_radio.show()
                        self.a_result_auto_tool_right_m30_radio.show()
                        self.a_result_auto_tool_up_m30_radio.show()
                        self.a_result_auto_tool_down_m30_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_m30_radio
                        self.atext2_down = self.a_result_auto_tool_down_m30_radio

                    if self.a_option_auto_choice_m20_check.isChecked():
                        self.athreshold.append(-20)
                        self.a_result_auto_tool_left_m20_radio.show()
                        self.a_result_auto_tool_right_m20_radio.show()
                        self.a_result_auto_tool_up_m20_radio.show()
                        self.a_result_auto_tool_down_m20_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_m20_radio
                        self.atext2_down = self.a_result_auto_tool_down_m20_radio

                    if self.a_option_auto_choice_m10_check.isChecked():
                        self.athreshold.append(-10)
                        self.a_result_auto_tool_left_m10_radio.show()
                        self.a_result_auto_tool_right_m10_radio.show()
                        self.a_result_auto_tool_up_m10_radio.show()
                        self.a_result_auto_tool_down_m10_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_m10_radio
                        self.atext2_down = self.a_result_auto_tool_down_m10_radio

                    if self.a_option_auto_choice_p10_check.isChecked():
                        self.athreshold.append(10)
                        self.a_result_auto_tool_left_p10_radio.show()
                        self.a_result_auto_tool_right_p10_radio.show()
                        self.a_result_auto_tool_up_p10_radio.show()
                        self.a_result_auto_tool_down_p10_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_p10_radio
                        self.atext2_down = self.a_result_auto_tool_down_p10_radio

                    if self.a_option_auto_choice_p20_check.isChecked():
                        self.athreshold.append(20)
                        self.a_result_auto_tool_left_p20_radio.show()
                        self.a_result_auto_tool_right_p20_radio.show()
                        self.a_result_auto_tool_up_p20_radio.show()
                        self.a_result_auto_tool_down_p20_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_p20_radio
                        self.atext2_down = self.a_result_auto_tool_down_p20_radio

                    if self.a_option_auto_choice_p30_check.isChecked():
                        self.athreshold.append(30)
                        self.a_result_auto_tool_left_p30_radio.show()
                        self.a_result_auto_tool_right_p30_radio.show()
                        self.a_result_auto_tool_up_p30_radio.show()
                        self.a_result_auto_tool_down_p30_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_p30_radio
                        self.atext2_down = self.a_result_auto_tool_down_p30_radio

                    if self.a_option_auto_choice_p40_check.isChecked():
                        self.athreshold.append(40)
                        self.a_result_auto_tool_left_p40_radio.show()
                        self.a_result_auto_tool_right_p40_radio.show()
                        self.a_result_auto_tool_up_p40_radio.show()
                        self.a_result_auto_tool_down_p40_radio.show()
                        self.atext2_right = self.a_result_auto_tool_right_p40_radio
                        self.atext2_down = self.a_result_auto_tool_down_p40_radio

                    if len(self.athreshold) == 1:
                        self.a_option_manual_auto_switch_layout.setCurrentWidget(self.a_option_manual_slider_toauto_widget)
                        self.autoRun()
                        return

                if self.petat == "Scan":
                    self.scan_image_name_temp = QFileInfo(self.scan_image_name).fileName()
                    self.scan_image_filename = str(self.athreshold[self.aloop]) + "_" + self.scan_image_name_temp
                    copy(self.scan_image_name, os.path.join(work_directory, self.scan_image_filename))

                    if self.a_option_double_page_check.isChecked(): self.arg["layout"] = "double"
                    self.arg["threshold"] = self.athreshold[self.aloop]

                    self.aetat = "Scan"

                    docker.etat = "AutoPreprocess"
                    docker.preprocess(self.arg)
                    self.wait(self.scan_image_name_temp + "\n\n" + "Thickness: " + str(self.arg["threshold"]))
        else:
            if self.aetat == "Ocr" or (self.aetat == "" and self.petat != "Scan"):
                self.openScanImage()

            if self.dialog_etat and self.aetat != "Result":
                if self.petat == "Scan":
                    if self.pvolume == False:
                        for f in self.scan_image_name:
                            copy(f, work_directory)
                    else:
                        for f in os.listdir(self.scan_folder_name):
                            if f.endswith(".tif"):
                                while True:
                                    ack = copy(os.path.join(self.scan_folder_name, f), work_directory)
                                    if ack.find(f): break

                    if self.a_option_manual_slider.value():
                        self.arg["threshold"] = self.a_option_manual_slider.value()
                    else:
                        self.arg["threshold"] = 0
                    if self.a_option_double_page_check.isChecked():
                        self.arg["layout"] = "double"

                    self.aetat = "Scan"

                    docker.etat = "AutoPreprocess"
                    docker.preprocess(self.arg)

                    self.scan_image_filename = QFileInfo(self.scan_image_name[0]).fileName()
                    nb_files = len(self.scan_image_name)

                    if self.pvolume:
                        txt = self.scan_folder_name + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                        self.pvolume = False
                    elif nb_files > 1:
                        txt = str(nb_files) + " image files\n\n" + "Thickness: " + str(self.arg["threshold"])
                    else:
                        txt = self.scan_image_filename + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                    self.wait(txt)

        if self.aetat == "Result":
            if self.a_option_book_button.isChecked():
                self.arg["page_type"] = "book"
                self.arg["line_break_method"] = "line_cut"
                if self.a_option_clearhr_check.isChecked(): self.arg["clear_hr"] = True
            if self.a_option_lowink_check.isChecked(): self.arg["low_ink"] = True
            if self.a_option_dial.value(): self.arg["break_width"] = self.a_option_dial.value() / 2

            docker.etat = "AutoOcr"
            docker.ocr(self.arg)
            self.wait()

    def wait(self, text=""):
        if docker.etat == "Preprocess":
            label = lang.gettext("Preprocess is running...")
        elif docker.etat == "Ocr":
            label = lang.gettext("Ocr is running...")
        elif docker.etat == "AutoPreprocess":
            label = lang.gettext("Auto preprocess is running...")
        elif docker.etat == "AutoOcr":
            label = lang.gettext("Auto Ocr is running...")

        if text: label += "\n\n"+text

        self.progress.setLabelText(label)
        self.progress.show()

    def processFinished(self):
        if docker.etat == "Preprocess":
            if os.path.isdir(os.path.join(work_directory, "out")) and os.path.isfile(os.path.join(work_directory, "out", self.scan_image_filename)):
                self.primage = QPixmap(os.path.join(".", "out", self.scan_image_filename))
                self.p_result_image_label1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.p_result_image_label2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.o_scan_image_label1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.o_scan_image_label2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.delFiles()

                self.petat = "Result"

                if self.oetat == "Ocr":
                    self.o_textedit1.hide()
                    self.o_textedit2.hide()
                    self.o_textedit1.clear()
                    self.o_textedit2.clear()
                    self.oetat = ""

                if self.aetat == "Ocr":
                    self.a_result_auto_widget1.hide()
                    self.a_result_auto_widget2.hide()
                    self.a_result_text_manual_textedit1.clear()
                    self.a_result_text_manual_textedit2.clear()
                    self.aetat = ""

                self.a_scan_image_label1.clear()
                self.a_scan_image_label2.clear()

        elif docker.etat == "Ocr":
            self.copyFile2Qtext()
            self.oetat = "Ocr"
            self.aetat = "Ocr"

        elif docker.etat == "AutoPreprocess":
            if os.path.isdir(os.path.join(work_directory, "out")) and os.path.isfile(os.path.join(work_directory, "out", self.scan_image_filename)):
                os.remove(self.scan_image_filename)

            self.aetat = "Result"
            docker.endProcess()
            self.autoRun()
            return

        elif docker.etat == "AutoOcr":
            if self.a_option_manual_auto_switch_layout.currentWidget() == self.a_option_auto_choice_tomanual_widget:
                self.copyOutput()

                if self.aloop == len(self.athreshold)-1:
                    self.aloop = 0
                    self.aetat = "Ocr"
                    self.copyFile2QtextAuto()
                else:
                    self.aloop += 1
                    self.aetat = "Scan"
                    docker.endProcess()
                    self.autoRun()
                    return
            else:
                self.copyFile2Qtext()
                self.aetat = "Ocr"
                self.oetat = "Ocr"

        docker.endProcess()
        self.progress.cancel()
        self.arg = {"threshold": "", "layout": "",
                    "page_type": "pecha", "line_break_method": "line_cluster", \
                    "clear_hr": "", "low_ink": "", "break_width": ""}

    def copyFile2Qtext(self):
        with open("ocr_output.txt", "r", encoding="utf-8") as file:
            data = file.read()
        self.o_textedit1.setText(data)
        self.o_textedit2.setText(data)
        self.o_textedit1.show()
        self.o_textedit2.show()
        self.a_result_text_manual_textedit1.setText(data)
        self.a_result_text_manual_textedit2.setText(data)
        self.a_result_manual_widget1.show()
        self.a_result_manual_widget2.show()

    def copyOutput(self):
        copy("ocr_output.txt", str(self.arg["threshold"]) + "_ocr_output.txt")
        self.delOutDir()

    def copyFile2QtextAuto(self):
        with open("0_ocr_output.txt", "r", encoding="utf-8") as file:
            data = file.read()
        self.a_result_text_left_textedit.setText(data)
        self.a_result_text_up_textedit.setText(data)
        self.a_result_auto_tool_left_0_radio.setChecked(True)
        self.a_result_auto_tool_up_0_radio.setChecked(True)

        if len(self.athreshold) > 1:
            with open(str(self.arg["threshold"]) + "_ocr_output.txt", "r", encoding="utf-8") as file:
                data = file.read()
            self.a_result_text_right_textedit.setText(data)
            self.a_result_text_down_textedit.setText(data)
            self.atext2_right.setChecked(True)
            self.atext2_down.setChecked(True)

        self.a_result_auto_widget1.show()
        self.a_result_auto_widget2.show()

    def lang(self, e):
        global lang
        answer = QMessageBox.question(self,
                lang.gettext("Message"), lang.gettext("Namsel Ocr need to Restart to apply the changes..."),
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            lang = languages[e.iconText()]
            qApp.exit(2)

    def restart(self):
        self.delFiles()
        self.delOutDir()
        qApp.exit(1)

    def delFiles(self):
        for f in os.listdir(work_directory):
            if not os.path.isdir(f):
                os.remove(f)

    def delOutDir(self):
        if os.path.isdir(os.path.join(work_directory, "out")):
            rmtree(os.path.join(work_directory, "out"))

def killEnvironment():
    docker.stop()

    os.chdir("/")
    if os.path.isdir(work_directory):
        rmtree(work_directory)

if __name__ == "__main__":
    while True:
        setEnvironment()
        app = QApplication(sys.argv)

        namsel_ocr = NamselOcr()
        namsel_ocr.show()

        rcode = app.exec_()
        del app, namsel_ocr
        killEnvironment()

        if not rcode: break

