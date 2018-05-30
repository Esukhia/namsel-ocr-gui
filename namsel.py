from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from shutil import copy, rmtree
from tempfile import gettempdir
import os, sys

import gettext

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
        self.apecha_button = QRadioButton(lang.gettext("Pecha"))
        self.apecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.abook_button = QRadioButton(lang.gettext("Book"))
        self.abook_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.apecha_button.setCheckable(True)
        self.abook_button.setCheckable(True)
        self.apecha_button.setChecked(True)

        self.apecha_book_layout = QVBoxLayout()
        self.apecha_book_layout.addWidget(self.apecha_button)
        self.apecha_book_layout.addWidget(self.abook_button)

        self.apecha_book_group = QGroupBox()
        self.apecha_book_group.setLayout(self.apecha_book_layout)

                        # Low ink
        self.alowink = QCheckBox(lang.gettext("Low ink"))
        self.alowink.setStatusTip(lang.gettext("Check if the scan image is a bit of low quality"))

        self.alowink_layout = QVBoxLayout()
        self.alowink_layout.addWidget(self.alowink)

        self.alowink_group = QGroupBox()
        self.alowink_group.setLayout(self.alowink_layout)

                        # Choice
        self.achoice_m40 = QCheckBox(lang.gettext("-40"))
        self.achoice_m30 = QCheckBox(lang.gettext("-30"))
        self.achoice_m20 = QCheckBox(lang.gettext("-20"))
        self.achoice_m10 = QCheckBox(lang.gettext("-10"))
        self.achoice_0 = QCheckBox(lang.gettext("0"))
        self.achoice_p10 = QCheckBox(lang.gettext("+10"))
        self.achoice_p20 = QCheckBox(lang.gettext("+20"))
        self.achoice_p30 = QCheckBox(lang.gettext("+30"))
        self.achoice_p40 = QCheckBox(lang.gettext("+40"))

        self.achoice_m40.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -40"))
        self.achoice_m30.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -30"))
        self.achoice_m20.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -20"))
        self.achoice_m10.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to -10"))
        self.achoice_0.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 0"))
        self.achoice_p10.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 10"))
        self.achoice_p20.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 20"))
        self.achoice_p30.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 30"))
        self.achoice_p40.setStatusTip(lang.gettext("Preprocessing setting the 'thickness' value to 40"))

        self.achoice_0.setDisabled(True)
        self.achoice_0.setChecked(True)

        self.achoice_layout = QHBoxLayout()
        self.achoice_layout.addWidget(self.achoice_m40)
        self.achoice_layout.addWidget(self.achoice_m30)
        self.achoice_layout.addWidget(self.achoice_m20)
        self.achoice_layout.addWidget(self.achoice_m10)
        self.achoice_layout.addWidget(self.achoice_0)
        self.achoice_layout.addWidget(self.achoice_p10)
        self.achoice_layout.addWidget(self.achoice_p20)
        self.achoice_layout.addWidget(self.achoice_p30)
        self.achoice_layout.addWidget(self.achoice_p40)




        self.achoice_group = QGroupBox()
        self.achoice_group.setFixedHeight(120)
        self.achoice_group.setLayout(self.achoice_layout)



        self.amanual_button1 = QPushButton("Manual")
        self.amanual_button1.setFixedWidth(100)
        self.amanual_button2 = QPushButton("Auto")
        self.amanual_button2.setFixedWidth(100)
        self.amanual_layer1 = QVBoxLayout()
        self.amanual_layer2 = QVBoxLayout()





        self.amanual_place = QWidget()
        self.amanual_place1 = QWidget()
        self.amanual_place2 = QWidget()

        self.amanual_layer1.addWidget(self.achoice_group)
        self.amanual_layer1.addWidget(self.amanual_button1, 0, Qt.AlignCenter)
        self.amanual_layer1.setContentsMargins(0,0,0,0)
        self.amanual_place1.setLayout(self.amanual_layer1)





        self.asliderlabel_val = QLabel(lang.gettext("Thickness: "))
        self.aslcd = QLCDNumber()
        self.aslcd.setStatusTip(lang.gettext("The thickness value during the preprocess"))
        self.aslcd.setSegmentStyle(QLCDNumber.Flat)
        self.aslcd.setFixedWidth(40)

        self.aslider = QSlider(Qt.Horizontal)
        self.aslider.setRange(-40, 40)
        self.aslider.setSingleStep(1)
        self.aslider.setTickPosition(QSlider.TicksBelow)
        self.aslider.setTickInterval(5)
        self.aslider.setStatusTip(lang.gettext("Set the thickness of the scan image"))

        



        self.aslider_label_place = QWidget()
        self.aslider_label_layout = QHBoxLayout()
        self.aslider_label_layout.addWidget(self.asliderlabel_val)
        self.aslider_label_layout.addWidget(self.aslcd)
        self.aslider_label_layout.setAlignment(Qt.AlignCenter)
        self.aslider_label_place.setLayout(self.aslider_label_layout)

        self.aslider_place = QWidget()
        self.aslider_layout = QVBoxLayout()
        self.aslider_layout.addWidget(self.aslider_label_place)
        self.aslider_layout.addWidget(self.aslider)
        self.aslider_place.setLayout(self.aslider_layout)





        self.amanual_slider_group = QGroupBox()
        self.amanual_slider_group.setFixedHeight(120)
        self.amanual_slider_group.setLayout(self.aslider_layout)







        self.amanual_layer2.addWidget(self.amanual_slider_group)
        self.amanual_layer2.addWidget(self.amanual_button2, 0, Qt.AlignCenter)
        self.amanual_layer2.setContentsMargins(0, 0, 0, 0)
        self.amanual_place2.setLayout(self.amanual_layer2)






        self.aswitch_layer = QStackedLayout(self.amanual_place)
        self.aswitch_layer.addWidget(self.amanual_place1)
        self.aswitch_layer.addWidget(self.amanual_place2)

        self.aswitch_layer.setCurrentWidget(self.amanual_place2)





                        # Label and the dial value
        self.adialabel_val = QLabel(lang.gettext("Break width: "))
        self.alcd = QLCDNumber()
        self.alcd.setStatusTip(lang.gettext("The break-Width value"))
        self.alcd.setSegmentStyle(QLCDNumber.Flat)
        self.alcd.setFixedWidth(40)
        self.alcd.display(lang.gettext("Off"))

        self.adial_label_num_layout = QHBoxLayout()
        self.adial_label_num_layout.addWidget(self.adialabel_val)
        self.adial_label_num_layout.addWidget(self.alcd)
        self.adial_label_num_layout.setAlignment(Qt.AlignCenter)

                        # QDial
        self.adial = QDial()
        self.adial.setRange(0, 8)
        self.adial.setNotchesVisible(True)
        self.adial.setStatusTip(lang.gettext("To controls how horizontally-connected stacks will be segmented"))

        self.adial_layout = QHBoxLayout()
        self.adial_layout.addLayout(self.adial_label_num_layout)
        self.adial_layout.addWidget(self.adial)

        self.adial_group = QGroupBox()
        self.adial_group.setLayout(self.adial_layout)

                        # Run the Auto mode
        self.adouble_page = QCheckBox(lang.gettext("Double page"))
        self.adouble_page.setStatusTip(lang.gettext("The scan image is a double page"))

        self.aclearhr = QCheckBox(lang.gettext("Clear HR"))
        self.aclearhr.setStatusTip(lang.gettext("The scan image is a double page"))

        self.arun_button = QPushButton(lang.gettext("Run"))
        self.arun_button.setStatusTip(lang.gettext("Run the ocr"))

        self.adc_layout = QHBoxLayout()
        self.adc_layout.addWidget(self.adouble_page)
        self.adc_layout.addWidget(self.aclearhr)

        self.adc_widget = QWidget()
        self.adc_widget.setLayout(self.adc_layout)
        self.adc_widget.hide()

        self.arun_layout = QVBoxLayout()
        self.arun_layout.addWidget(self.adc_widget)
        self.arun_layout.addWidget(self.arun_button)

        self.arun_group = QGroupBox()
        self.arun_group.setLayout(self.arun_layout)

                    # Option layout & widget
        self.aoption_layout = QHBoxLayout()
        self.aoption_layout.addWidget(self.apecha_book_group)
        self.aoption_layout.addWidget(self.alowink_group)
        self.aoption_layout.addWidget(self.amanual_place)
        self.aoption_layout.addWidget(self.adial_group)
        self.aoption_layout.addWidget(self.arun_group)

        self.aoption_widget = QWidget()
        self.aoption_widget.setFixedHeight(200)
        self.aoption_widget.setLayout(self.aoption_layout)

                    # Image-text
                        # Scan image widget
        self.ascan_image_layer1 = QLabel()
        self.ascan_image_layer2 = QLabel()
        self.ascan_image_layer1.setStatusTip(lang.gettext("The scan image"))
        self.ascan_image_layer2.setStatusTip(lang.gettext("The scan image"))

                        # Result text widget
        self.azone_layer1 = QWidget()
        self.azone_layer2 = QWidget()
        self.azone_layer1.hide()
        self.azone_layer2.hide()

                                # Left
        self.atooltext_left_layer1 = QWidget()
                                    # Toolbar for file comparison
        self.atool_text_left_files_layer1 = QWidget()

        self.atool_text_left_files_m40_layer1 = QRadioButton("-40")
        self.atool_text_left_files_m30_layer1 = QRadioButton("-30")
        self.atool_text_left_files_m20_layer1 = QRadioButton("-20")
        self.atool_text_left_files_m10_layer1 = QRadioButton("-10")
        self.atool_text_left_files_0_layer1 = QRadioButton("0")
        self.atool_text_left_files_p10_layer1 = QRadioButton("10")
        self.atool_text_left_files_p20_layer1 = QRadioButton("20")
        self.atool_text_left_files_p30_layer1 = QRadioButton("30")
        self.atool_text_left_files_p40_layer1 = QRadioButton("40")

        self.atool_text_left_files_m40_layer1.hide()
        self.atool_text_left_files_m30_layer1.hide()
        self.atool_text_left_files_m20_layer1.hide()
        self.atool_text_left_files_m10_layer1.hide()
        self.atool_text_left_files_p10_layer1.hide()
        self.atool_text_left_files_p20_layer1.hide()
        self.atool_text_left_files_p30_layer1.hide()
        self.atool_text_left_files_p40_layer1.hide()

        self.atool_text_left_files_layer1_layout = QHBoxLayout()
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_m40_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_m30_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_m20_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_m10_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_0_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_p10_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_p20_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_p30_layer1)
        self.atool_text_left_files_layer1_layout.addWidget(self.atool_text_left_files_p40_layer1)

        self.atool_text_left_files_layer1.setLayout(self.atool_text_left_files_layer1_layout)

                                    # Text
        self.atext_left_layer1 = QTextEdit()
        self.atext_left_layer1.setStatusTip(lang.gettext("The ocr result"))
        self.atext_left_layer1.setFont(self.font)
        self.atext_left_layer1.setFontPointSize(18)

        self.atooltext_left_layer1_layout = QVBoxLayout()
        self.atooltext_left_layer1_layout.addWidget(self.atool_text_left_files_layer1)
        self.atooltext_left_layer1_layout.addWidget(self.atext_left_layer1)
        self.atooltext_left_layer1.setLayout(self.atooltext_left_layer1_layout)

                                # Right
        self.atooltext_right_layer1 = QWidget()
                                    # Toolbar for file comparison
        self.atool_text_right_files_layer1 = QWidget()

        self.atool_text_right_files_m40_layer1 = QRadioButton("-40")
        self.atool_text_right_files_m30_layer1 = QRadioButton("-30")
        self.atool_text_right_files_m20_layer1 = QRadioButton("-20")
        self.atool_text_right_files_m10_layer1 = QRadioButton("-10")
        self.atool_text_right_files_0_layer1 = QRadioButton("0")
        self.atool_text_right_files_p10_layer1 = QRadioButton("10")
        self.atool_text_right_files_p20_layer1 = QRadioButton("20")
        self.atool_text_right_files_p30_layer1 = QRadioButton("30")
        self.atool_text_right_files_p40_layer1 = QRadioButton("40")

        self.atool_text_right_files_m40_layer1.hide()
        self.atool_text_right_files_m30_layer1.hide()
        self.atool_text_right_files_m20_layer1.hide()
        self.atool_text_right_files_m10_layer1.hide()
        self.atool_text_right_files_p10_layer1.hide()
        self.atool_text_right_files_p20_layer1.hide()
        self.atool_text_right_files_p30_layer1.hide()
        self.atool_text_right_files_p40_layer1.hide()

        self.atool_text_right_files_layer1_layout = QHBoxLayout()
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_m40_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_m30_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_m20_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_m10_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_0_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_p10_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_p20_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_p30_layer1)
        self.atool_text_right_files_layer1_layout.addWidget(self.atool_text_right_files_p40_layer1)

        self.atool_text_right_files_layer1.setLayout(self.atool_text_right_files_layer1_layout)

                                   # Text
        self.atext_right_layer1 = QTextEdit()
        self.atext_right_layer1.setStatusTip(lang.gettext("The ocr result"))
        self.atext_right_layer1.setFont(self.font)
        self.atext_right_layer1.setFontPointSize(18)

        self.atooltext_right_layer1_layout = QVBoxLayout()
        self.atooltext_right_layer1_layout.addWidget(self.atool_text_right_files_layer1)
        self.atooltext_right_layer1_layout.addWidget(self.atext_right_layer1)
        self.atooltext_right_layer1.setLayout(self.atooltext_right_layer1_layout)

                            # Result layer1
        self.atooltext_layer1_layout = QHBoxLayout()
        self.atooltext_layer1_layout.addWidget(self.atooltext_left_layer1)
        self.atooltext_layer1_layout.addWidget(self.atooltext_right_layer1)

        self.azone_layer1.setLayout(self.atooltext_layer1_layout)

                                # Up
        self.atooltext_up_layer2 = QWidget()
                                    # Toolbar for file comparison
        self.atool_text_up_files_layer2 = QWidget()

        self.atool_text_up_files_m40_layer2 = QRadioButton("-40")
        self.atool_text_up_files_m30_layer2 = QRadioButton("-30")
        self.atool_text_up_files_m20_layer2 = QRadioButton("-20")
        self.atool_text_up_files_m10_layer2 = QRadioButton("-10")
        self.atool_text_up_files_0_layer2 = QRadioButton("0")
        self.atool_text_up_files_p10_layer2 = QRadioButton("10")
        self.atool_text_up_files_p20_layer2 = QRadioButton("20")
        self.atool_text_up_files_p30_layer2 = QRadioButton("30")
        self.atool_text_up_files_p40_layer2 = QRadioButton("40")

        self.atool_text_up_files_m40_layer2.hide()
        self.atool_text_up_files_m30_layer2.hide()
        self.atool_text_up_files_m20_layer2.hide()
        self.atool_text_up_files_m10_layer2.hide()
        self.atool_text_up_files_p10_layer2.hide()
        self.atool_text_up_files_p20_layer2.hide()
        self.atool_text_up_files_p30_layer2.hide()
        self.atool_text_up_files_p40_layer2.hide()

        self.atool_text_up_files_layer2_layout = QHBoxLayout()
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_m40_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_m30_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_m20_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_m10_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_0_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_p10_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_p20_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_p30_layer2)
        self.atool_text_up_files_layer2_layout.addWidget(self.atool_text_up_files_p40_layer2)

        self.atool_text_up_files_layer2.setLayout(self.atool_text_up_files_layer2_layout)

                                    # Text
        self.atext_up_layer2 = QTextEdit()
        self.atext_up_layer2.setStatusTip(lang.gettext("The ocr result"))
        self.atext_up_layer2.setFont(self.font)
        self.atext_up_layer2.setFontPointSize(18)

        self.atooltext_up_layer2_layout = QVBoxLayout()
        self.atooltext_up_layer2_layout.addWidget(self.atool_text_up_files_layer2)
        self.atooltext_up_layer2_layout.addWidget(self.atext_up_layer2)
        self.atooltext_up_layer2.setLayout(self.atooltext_up_layer2_layout)

                                # Down
        self.atooltext_down_layer2 = QWidget()
                                    # Toolbar for file comparison
        self.atool_text_down_files_layer2 = QWidget()

        self.atool_text_down_files_m40_layer2 = QRadioButton("-40")
        self.atool_text_down_files_m30_layer2 = QRadioButton("-30")
        self.atool_text_down_files_m20_layer2 = QRadioButton("-20")
        self.atool_text_down_files_m10_layer2 = QRadioButton("-10")
        self.atool_text_down_files_0_layer2 = QRadioButton("0")
        self.atool_text_down_files_p10_layer2 = QRadioButton("10")
        self.atool_text_down_files_p20_layer2 = QRadioButton("20")
        self.atool_text_down_files_p30_layer2 = QRadioButton("30")
        self.atool_text_down_files_p40_layer2 = QRadioButton("40")

        self.atool_text_down_files_m40_layer2.hide()
        self.atool_text_down_files_m30_layer2.hide()
        self.atool_text_down_files_m20_layer2.hide()
        self.atool_text_down_files_m10_layer2.hide()
        self.atool_text_down_files_p10_layer2.hide()
        self.atool_text_down_files_p20_layer2.hide()
        self.atool_text_down_files_p30_layer2.hide()
        self.atool_text_down_files_p40_layer2.hide()

        self.atool_text_down_files_layer2_layout = QHBoxLayout()
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_m40_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_m30_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_m20_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_m10_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_0_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_p10_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_p20_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_p30_layer2)
        self.atool_text_down_files_layer2_layout.addWidget(self.atool_text_down_files_p40_layer2)

        self.atool_text_down_files_layer2.setLayout(self.atool_text_down_files_layer2_layout)

                                    # Text
        self.atext_down_layer2 = QTextEdit()
        self.atext_down_layer2.setStatusTip(lang.gettext("The ocr result"))
        self.atext_down_layer2.setFont(self.font)
        self.atext_down_layer2.setFontPointSize(18)

        self.atooltext_down_layer2_layout = QVBoxLayout()
        self.atooltext_down_layer2_layout.addWidget(self.atool_text_down_files_layer2)
        self.atooltext_down_layer2_layout.addWidget(self.atext_down_layer2)
        self.atooltext_down_layer2.setLayout(self.atooltext_down_layer2_layout)


        self.atext_alayer1 = QTextEdit()
        self.atext_alayer1.setStatusTip(lang.gettext("The ocr result"))
        self.atext_alayer1.setFont(self.font)
        self.atext_alayer1.setFontPointSize(18)
        self.atext_alayer1.hide()

        self.atext_alayer2 = QTextEdit()
        self.atext_alayer2.setStatusTip(lang.gettext("The ocr result"))
        self.atext_alayer2.setFont(self.font)
        self.atext_alayer2.setFontPointSize(18)
        self.atext_alayer2.hide()

        # Result layer
        self.atooltext_layer2_layout = QVBoxLayout()
        self.atooltext_layer2_layout.addWidget(self.atooltext_up_layer2)
        self.atooltext_layer2_layout.addWidget(self.atooltext_down_layer2)

        self.azone_layer2.setLayout(self.atooltext_layer2_layout)

                    # Image-text layout and widget
        self.aimagetext_hlayout = QHBoxLayout()
        self.aimagetext_vlayout = QVBoxLayout()
        self.aimagetext_ahlayout = QHBoxLayout()
        self.aimagetext_avlayout = QVBoxLayout()

        self.aimagetext_vlayout.addWidget(self.ascan_image_layer1)
        self.aimagetext_vlayout.addWidget(self.azone_layer1)

        self.aimagetext_hlayout.addWidget(self.ascan_image_layer2)
        self.aimagetext_hlayout.addWidget(self.azone_layer2)

        self.aimagetext_avlayout.addWidget(self.ascan_image_layer1)
        self.aimagetext_avlayout.addWidget(self.atext_alayer1)

        self.aimagetext_ahlayout.addWidget(self.ascan_image_layer2)
        self.aimagetext_ahlayout.addWidget(self.atext_alayer2)

        self.aimagetext_widget = QWidget()
        self.aimagetext_vwidget = QWidget()
        self.aimagetext_hwidget = QWidget()
        self.aimagetext_ahwidget = QWidget()
        self.aimagetext_avwidget = QWidget()

        self.aimagetext_vwidget.setLayout(self.aimagetext_vlayout)
        self.aimagetext_hwidget.setLayout(self.aimagetext_hlayout)

        self.aimagetext_avwidget.setLayout(self.aimagetext_avlayout)
        self.aimagetext_ahwidget.setLayout(self.aimagetext_ahlayout)

        self.aimagetext_staklayout = QStackedLayout(self.aimagetext_widget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_vwidget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_hwidget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_ahwidget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_avwidget)
        self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_avwidget)

        self.aimagetext_widget.setLayout(self.aimagetext_staklayout)

                # Ocr page layout & widget
        self.auto_layout = QVBoxLayout()
        self.auto_layout.addWidget(self.aoption_widget)
        self.auto_layout.addWidget(self.aimagetext_widget)

        self.autopage_widget = QWidget()
        self.autopage_widget.setLayout(self.auto_layout)

                # Preprocess page
                    # Option
                        # Pecha - Book radiobuttons
        self.ppecha_button = QRadioButton(lang.gettext("Pecha"))
        self.ppecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.pbook_button = QRadioButton(lang.gettext("Book"))
        self.pbook_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.ppecha_button.setCheckable(True)
        self.pbook_button.setCheckable(True)
        self.ppecha_button.setChecked(True)

        self.ppecha_book_layout = QVBoxLayout()
        self.ppecha_book_layout.addWidget(self.ppecha_button)
        self.ppecha_book_layout.addWidget(self.pbook_button)

        self.ppecha_book_group = QGroupBox()
        self.ppecha_book_group.setLayout(self.ppecha_book_layout)

                        # Label and the thickness value
        self.psliderlabel_val = QLabel(lang.gettext("Thickness: "))
        self.plcd = QLCDNumber()
        self.plcd.setStatusTip(lang.gettext("The thickness value during the preprocess"))
        self.plcd.setSegmentStyle(QLCDNumber.Flat)
        self.plcd.setFixedWidth(40)

        self.pslider_label_num_layout = QHBoxLayout()
        self.pslider_label_num_layout.addWidget(self.psliderlabel_val)
        self.pslider_label_num_layout.addWidget(self.plcd)
        self.pslider_label_num_layout.setAlignment(Qt.AlignCenter)

                        # Thickness slider
        self.pslider = QSlider(Qt.Horizontal)
        self.pslider.setRange(-40, 40)
        self.pslider.setSingleStep(1)
        self.pslider.setTickPosition(QSlider.TicksBelow)
        self.pslider.setTickInterval(5)
        self.pslider.setStatusTip(lang.gettext("Set the thickness of the scan image"))

        self.pslider_layout = QVBoxLayout()
        self.pslider_layout.addLayout(self.pslider_label_num_layout)
        self.pslider_layout.addWidget(self.pslider)

        self.pslider_group = QGroupBox()
        self.pslider_group.setLayout(self.pslider_layout)

                        # Run the Preprocess
        self.pdouble_page = QCheckBox(lang.gettext("Double page"))
        self.pdouble_page.setStatusTip(lang.gettext("The scan image is a double page"))
        self.prun_button = QPushButton(lang.gettext("Run"))
        self.prun_button.setStatusTip(lang.gettext("Run the preprocess"))

        self.pd_layout = QHBoxLayout()
        self.pd_layout.addWidget(self.pdouble_page)

        self.pd_widget = QWidget()
        self.pd_widget.setLayout(self.pd_layout)
        self.pd_widget.hide()

        self.prun_layout = QVBoxLayout()
        self.prun_layout.addWidget(self.pd_widget)
        self.prun_layout.addWidget(self.prun_button)

        self.prun_group = QGroupBox()
        self.prun_group.setLayout(self.prun_layout)

                    # Option layout & widget
        self.poption_layout = QHBoxLayout()
        self.poption_layout.addWidget(self.ppecha_book_group)
        self.poption_layout.addWidget(self.pslider_group)
        self.poption_layout.addWidget(self.prun_group)

        self.poption_widget = QWidget()
        self.poption_widget.setFixedHeight(130)
        self.poption_widget.setLayout(self.poption_layout)

                    # Image
                        # Scan image widget
        self.pscan_image_layer1 = QLabel()
        self.pscan_image_layer2 = QLabel()
        self.pscan_image_layer1.setStatusTip(lang.gettext("The scan image"))
        self.pscan_image_layer2.setStatusTip(lang.gettext("The scan image"))

                        # Result image widget
        self.presult_image_layer1 = QLabel()
        self.presult_image_layer2 = QLabel()
        self.presult_image_layer1.setStatusTip(lang.gettext("The result 'scantailored' image"))
        self.presult_image_layer2.setStatusTip(lang.gettext("The result 'scantailored' image"))

                    # Image layout & widget
        self.pimage_hlayout = QHBoxLayout()
        self.pimage_vlayout = QVBoxLayout()

        self.pimage_vlayout.addWidget(self.pscan_image_layer1)
        self.pimage_vlayout.addWidget(self.presult_image_layer1)

        self.pimage_hlayout.addWidget(self.pscan_image_layer2)
        self.pimage_hlayout.addWidget(self.presult_image_layer2)

        self.pimage_widget = QWidget()
        self.pimage_vwidget = QWidget()
        self.pimage_hwidget = QWidget()

        self.pimage_vwidget.setLayout(self.pimage_vlayout)
        self.pimage_hwidget.setLayout(self.pimage_hlayout)

        self.pimage_staklayout = QStackedLayout(self.pimage_widget)
        self.pimage_staklayout.addWidget(self.pimage_vwidget)
        self.pimage_staklayout.addWidget(self.pimage_hwidget)
        self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)

        self.pimage_widget.setLayout(self.pimage_staklayout)

                # Preprocess page layout & widget
        self.prep_layout = QVBoxLayout()
        self.prep_layout.addWidget(self.poption_widget)
        self.prep_layout.addWidget(self.pimage_widget)

        self.preprocesspage_widget = QWidget()
        self.preprocesspage_widget.setLayout(self.prep_layout)

                # Ocr page options
                    # Option
                        # Pecha - Book radiobuttons
        self.opecha_button = QRadioButton(lang.gettext("Pecha"))
        self.opecha_button.setStatusTip(lang.gettext("The scan image is a pecha"))
        self.obook_button = QRadioButton(lang.gettext("Book"))
        self.obook_button.setStatusTip(lang.gettext("The scan image is a book"))
        self.opecha_button.setCheckable(True)
        self.obook_button.setCheckable(True)
        self.opecha_button.setChecked(True)

        self.opecha_book_layout = QVBoxLayout()
        self.opecha_book_layout.addWidget(self.opecha_button)
        self.opecha_book_layout.addWidget(self.obook_button)

        self.opecha_book_group = QGroupBox()
        self.opecha_book_group.setLayout(self.opecha_book_layout)

                        # Low ink
        self.olowink = QCheckBox(lang.gettext("Low ink"))
        self.olowink.setStatusTip(lang.gettext("Check if the scan image is a bit of low quality"))

        self.olowink_layout = QVBoxLayout()
        self.olowink_layout.addWidget(self.olowink)

        self.olowink_group = QGroupBox()
        self.olowink_group.setLayout(self.olowink_layout)

                        # Label and the dial value
        self.odialabel_val = QLabel(lang.gettext("Break width: "))
        self.olcd = QLCDNumber()
        self.olcd.setStatusTip(lang.gettext("The break-Width value"))
        self.olcd.setSegmentStyle(QLCDNumber.Flat)
        self.olcd.setFixedWidth(40)
        self.olcd.display(lang.gettext("Off"))

        self.odial_label_num_layout = QHBoxLayout()
        self.odial_label_num_layout.addWidget(self.odialabel_val)
        self.odial_label_num_layout.addWidget(self.olcd)
        self.odial_label_num_layout.setAlignment(Qt.AlignCenter)

                        # QDial
        self.odial = QDial()
        self.odial.setRange(0, 8)
        self.odial.setNotchesVisible(True)
        self.odial.setStatusTip(lang.gettext("To controls how horizontally-connected stacks will be segmented"))

        self.odial_layout = QHBoxLayout()
        self.odial_layout.addLayout(self.odial_label_num_layout)
        self.odial_layout.addWidget(self.odial)

        self.odial_group = QGroupBox()
        self.odial_group.setLayout(self.odial_layout)

                        # Run the Ocr
        self.oclearhr = QCheckBox(lang.gettext("Clear HR"))
        self.oclearhr.setStatusTip(lang.gettext("The scan image is a double page"))
        self.orun_button = QPushButton(lang.gettext("Run"))
        self.orun_button.setStatusTip(lang.gettext("Run the ocr"))

        self.od_layout = QHBoxLayout()
        self.od_layout.addWidget(self.oclearhr)

        self.od_widget = QWidget()
        self.od_widget.setLayout(self.od_layout)
        self.od_widget.hide()

        self.orun_layout = QVBoxLayout()
        self.orun_layout.addWidget(self.od_widget)
        self.orun_layout.addWidget(self.orun_button)

        self.orun_group = QGroupBox()
        self.orun_group.setLayout(self.orun_layout)

                    # Option layout & widget
        self.ooption_layout = QHBoxLayout()
        self.ooption_layout.addWidget(self.opecha_book_group)
        self.ooption_layout.addWidget(self.olowink_group)
        self.ooption_layout.addWidget(self.odial_group)
        self.ooption_layout.addWidget(self.orun_group)

        self.ooption_widget = QWidget()
        self.ooption_widget.setFixedHeight(130)
        self.ooption_widget.setLayout(self.ooption_layout)

                    # Image-text
                        # Scan image widget
        self.oscan_image_layer1 = QLabel()
        self.oscan_image_layer2 = QLabel()
        self.oscan_image_layer1.setStatusTip(lang.gettext("The scan image"))
        self.oscan_image_layer2.setStatusTip(lang.gettext("The scan image"))

                        # Result text widget
        self.otext_layer1 = QTextEdit()
        self.otext_layer2 = QTextEdit()
        self.otext_layer1.setStatusTip(lang.gettext("The ocr result"))
        self.otext_layer2.setStatusTip(lang.gettext("The ocr result"))
        self.otext_layer1.setFont(self.font)
        self.otext_layer2.setFont(self.font)
        self.otext_layer1.setFontPointSize(18)
        self.otext_layer2.setFontPointSize(18)
        self.otext_layer1.hide()
        self.otext_layer2.hide()

                    # Image-text layout and widget
        self.oimagetext_hlayout = QHBoxLayout()
        self.oimagetext_vlayout = QVBoxLayout()

        self.oimagetext_vlayout.addWidget(self.oscan_image_layer1)
        self.oimagetext_vlayout.addWidget(self.otext_layer1)

        self.oimagetext_hlayout.addWidget(self.oscan_image_layer2)
        self.oimagetext_hlayout.addWidget(self.otext_layer2)

        self.oimagetext_widget = QWidget()
        self.oimagetext_vwidget = QWidget()
        self.oimagetext_hwidget = QWidget()

        self.oimagetext_vwidget.setLayout(self.oimagetext_vlayout)
        self.oimagetext_hwidget.setLayout(self.oimagetext_hlayout)

        self.oimagetext_staklayout = QStackedLayout(self.oimagetext_widget)
        self.oimagetext_staklayout.addWidget(self.oimagetext_vwidget)
        self.oimagetext_staklayout.addWidget(self.oimagetext_hwidget)
        self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_vwidget)

        self.oimagetext_widget.setLayout(self.oimagetext_staklayout)

                # Ocr page layout & widget
        self.ocr_layout = QVBoxLayout()
        self.ocr_layout.addWidget(self.ooption_widget)
        self.ocr_layout.addWidget(self.oimagetext_widget)

        self.ocrpage_widget = QWidget()
        self.ocrpage_widget.setLayout(self.ocr_layout)

            # Joining all the pages together
        self.page_widget = QWidget()
        self.page_staklayout = QStackedLayout(self.page_widget)
        self.page_staklayout.addWidget(self.autopage_widget)
        self.page_staklayout.addWidget(self.preprocesspage_widget)
        self.page_staklayout.addWidget(self.ocrpage_widget)
        self.page_staklayout.setCurrentWidget(self.preprocesspage_widget)

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
        self.aslider.valueChanged.connect(self.aslcd.display)
        self.amanual_button1.released.connect(self.autoManual)
        self.amanual_button2.released.connect(self.autoAuto)
        self.adial.valueChanged.connect(lambda x: self.alcd.display(x / 2) if x else self.alcd.display("Off"))
        self.abook_button.toggled.connect(self.pechabook)
        self.adouble_page.toggled.connect(self.double)
        self.arun_button.released.connect(self.autoRun)

        self.atool_text_left_files_m40_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "-40", x))
        self.atool_text_left_files_m30_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "-30", x))
        self.atool_text_left_files_m20_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "-20", x))
        self.atool_text_left_files_m10_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "-10", x))
        self.atool_text_left_files_0_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "0", x))
        self.atool_text_left_files_p10_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "10", x))
        self.atool_text_left_files_p20_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "20", x))
        self.atool_text_left_files_p30_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "30", x))
        self.atool_text_left_files_p40_layer1.toggled.connect(lambda x: self.comparison(self.atext_left_layer1, "40", x))

        self.atool_text_right_files_m40_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "-40", x))
        self.atool_text_right_files_m30_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "-30", x))
        self.atool_text_right_files_m20_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "-20", x))
        self.atool_text_right_files_m10_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "-10", x))
        self.atool_text_right_files_0_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "0", x))
        self.atool_text_right_files_p10_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "10", x))
        self.atool_text_right_files_p20_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "20", x))
        self.atool_text_right_files_p30_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "30", x))
        self.atool_text_right_files_p40_layer1.toggled.connect(lambda x: self.comparison(self.atext_right_layer1, "40", x))

        self.atool_text_up_files_m40_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "-40", x))
        self.atool_text_up_files_m30_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "-30", x))
        self.atool_text_up_files_m20_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "-20", x))
        self.atool_text_up_files_m10_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "-10", x))
        self.atool_text_up_files_0_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "0", x))
        self.atool_text_up_files_p10_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "10", x))
        self.atool_text_up_files_p20_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "20", x))
        self.atool_text_up_files_p30_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "30", x))
        self.atool_text_up_files_p40_layer2.toggled.connect(lambda x: self.comparison(self.atext_up_layer2, "40", x))

        self.atool_text_down_files_m40_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "-40", x))
        self.atool_text_down_files_m30_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "-30", x))
        self.atool_text_down_files_m20_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "-20", x))
        self.atool_text_down_files_m10_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "-10", x))
        self.atool_text_down_files_0_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "0", x))
        self.atool_text_down_files_p10_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "10", x))
        self.atool_text_down_files_p20_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "20", x))
        self.atool_text_down_files_p30_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "30", x))
        self.atool_text_down_files_p40_layer2.toggled.connect(lambda x: self.comparison(self.atext_down_layer2, "40", x))

            # Preprocess mode
        self.prep_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.preprocesspage_widget))
        self.pslider.valueChanged.connect(self.plcd.display)
        self.pbook_button.toggled.connect(self.pechabook)
        self.pdouble_page.toggled.connect(self.double)
        self.prun_button.released.connect(self.preprocessRun)
            # Ocr mode
        self.ocr_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.ocrpage_widget))
        self.odial.valueChanged.connect(lambda x: self.olcd.display(x/2) if x else self.olcd.display("Off"))
        self.obook_button.toggled.connect(self.pechabook)
        self.orun_button.released.connect(self.ocrRun)
            # Docker
        docker.docker_process.finished.connect(self.processFinished)

    def autoManual(self):
        self.aswitch_layer.setCurrentWidget(self.amanual_place2)

    def autoAuto(self):
        self.aswitch_layer.setCurrentWidget(self.amanual_place1)

    def comparison(self, pos, button, e):
        if e:
            self.scan_image_name_temp = button + "_ocr_output.txt"
            with open(self.scan_image_name_temp, "r", encoding="utf-8") as file:
                data = file.read()
            pos.setText(data)

    def pechabook(self, e):
        if e:
            if not self.pdouble_page.isChecked() and not self.adouble_page.isChecked():
                self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)

                if self.aswitch_layer.currentWidget() == self.amanual_place1:
                    self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_hwidget)
                else:
                    self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_ahwidget)

            if self.petat == "Result" and self.pdouble_page.isChecked():
                self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
            else:
                self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_hwidget)

            self.pd_widget.show()
            self.od_widget.show()
            self.adc_widget.show()
            self.pbook_button.setChecked(True)
            self.obook_button.setChecked(True)
            self.abook_button.setChecked(True)
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_vwidget)

            if self.aswitch_layer.currentWidget() == self.amanual_place1:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_vwidget)
            else:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_avwidget)

            self.pd_widget.hide()
            self.od_widget.hide()
            self.adc_widget.hide()
            self.ppecha_button.setChecked(True)
            self.opecha_button.setChecked(True)
            self.apecha_button.setChecked(True)

    def double(self, e):
        if e:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_vwidget)

            if self.aswitch_layer.currentWidget() == self.amanual_place1:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_vwidget)
            else:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_avwidget)

            self.pdouble_page.setChecked(True)
            self.adouble_page.setChecked(True)
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_hwidget)

            if self.aswitch_layer.currentWidget() == self.amanual_place1:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_hwidget)
            else:
                self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_ahwidget)

            self.pdouble_page.setChecked(False)
            self.adouble_page.setChecked(False)

    def openScanImage(self, folder=""):
        if self.petat == "Scan":
            self.scan_image_name_temp = self.scan_image_name

        self.dialog_etat = False
        if not folder: folder = "/"

        self.scan_image_name, _ = QFileDialog.getOpenFileName(self, lang.gettext("Open the source scan image..."),\
                                                              folder, lang.gettext("Image files (*.tif)"))
        if self.scan_image_name:
            self.dialog_etat = True

            if self.petat == "Result":
                self.presult_image_layer1.clear()
                self.presult_image_layer2.clear()
                self.del_out_dir()

            if self.oetat == "Ocr":
                self.otext_layer1.hide()
                self.otext_layer2.hide()
                self.otext_layer1.clear()
                self.otext_layer2.clear()
                self.atext_left_layer1.hide()
                self.atext_right_layer1.hide()
                self.atext_up_layer2.hide()
                self.atext_down_layer2.hide()
                self.atext_left_layer1.clear()
                self.atext_right_layer1.clear()
                self.atext_up_layer2.clear()
                self.atext_down_layer2.clear()
                self.atext_alayer1.hide()
                self.atext_alayer2.hide()
                self.atext_alayer1.clear()
                self.atext_alayer2.clear()
                self.del_out_dir()
                self.del_files()

            self.psimage = QPixmap(self.scan_image_name)
            self.pscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.pscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.ascan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.ascan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))

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
            if self.pvolume:
                answer = QMessageBox.question(self,
                            lang.gettext("Message"), lang.gettext("Preprocess all the volume images?"),
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer == QMessageBox.Yes:
                    pass
                elif answer == QMessageBox.No:
                    self.pvolume = False
                else: return

            if self.pvolume == False:
                copy(self.scan_image_name, work_directory)
            else:
                for f in os.listdir(self.scan_folder_name):
                    if f.endswith(".tif"):
                        while True:
                            ack = copy(os.path.join(self.scan_folder_name, f), work_directory)
                            if ack.find(f): break

            if self.pslider.value():
                self.arg["threshold"] = self.pslider.value()
            else:
                self.arg["threshold"] = 0
            if self.pdouble_page.isChecked():
                self.arg["layout"] = "double"

            docker.etat = "Preprocess"
            docker.preprocess(self.arg)

            self.scan_image_filename = QFileInfo(self.scan_image_name).fileName()

            if self.pvolume:
                txt = self.scan_folder_name + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                self.pvolume = False
            else:
                txt = self.scan_image_filename + "\n\n" + "Thickness: " + str(self.arg["threshold"])
            self.wait(txt)

    def ocrRun(self):
        if self.petat == "" or self.oetat == "Ocr":
            self.openScanImage()

        if self.dialog_etat:
            if self.petat == "Scan":
                copy(self.scan_image_name, work_directory)

            if self.obook_button.isChecked():
                self.arg["page_type"] = "book"
                self.arg["line_break_method"] = "line_cut"
                if self.oclearhr.isChecked(): self.arg["clear_hr"] = True
            if self.olowink.isChecked(): self.arg["low_ink"] = True
            if self.odial.value(): self.arg["break_width"] = self.odial.value()/2

            docker.etat = "Ocr"
            docker.ocr(self.arg)
            self.wait()

    def autoRun(self):
        if self.aetat == "Ocr" or self.aetat == "" and self.petat != "Scan":
            self.openScanImage()


        if self.dialog_etat and self.aetat != "Result":
            if self.aswitch_layer.currentWidget() == self.amanual_place1:
                if len(self.athreshold) == 1:
                    if self.achoice_m40.isChecked():
                        self.athreshold.append(-40)
                        self.atool_text_left_files_m40_layer1.show()
                        self.atool_text_right_files_m40_layer1.show()
                        self.atool_text_up_files_m40_layer2.show()
                        self.atool_text_down_files_m40_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_m40_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_m40_layer2

                    if self.achoice_m30.isChecked():
                        self.athreshold.append(-30)
                        self.atool_text_left_files_m30_layer1.show()
                        self.atool_text_right_files_m30_layer1.show()
                        self.atool_text_up_files_m30_layer2.show()
                        self.atool_text_down_files_m30_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_m30_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_m30_layer2

                    if self.achoice_m20.isChecked():
                        self.athreshold.append(-20)
                        self.atool_text_left_files_m20_layer1.show()
                        self.atool_text_right_files_m20_layer1.show()
                        self.atool_text_up_files_m20_layer2.show()
                        self.atool_text_down_files_m20_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_m20_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_m20_layer2

                    if self.achoice_m10.isChecked():
                        self.athreshold.append(-10)
                        self.atool_text_left_files_m10_layer1.show()
                        self.atool_text_right_files_m10_layer1.show()
                        self.atool_text_up_files_m10_layer2.show()
                        self.atool_text_down_files_m10_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_m10_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_m10_layer2

                    if self.achoice_p10.isChecked():
                        self.athreshold.append(10)
                        self.atool_text_left_files_p10_layer1.show()
                        self.atool_text_right_files_p10_layer1.show()
                        self.atool_text_up_files_p10_layer2.show()
                        self.atool_text_down_files_p10_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_p10_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_p10_layer2

                    if self.achoice_p20.isChecked():
                        self.athreshold.append(20)
                        self.atool_text_left_files_p20_layer1.show()
                        self.atool_text_right_files_p20_layer1.show()
                        self.atool_text_up_files_p20_layer2.show()
                        self.atool_text_down_files_p20_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_p20_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_p20_layer2

                    if self.achoice_p30.isChecked():
                        self.athreshold.append(30)
                        self.atool_text_left_files_p30_layer1.show()
                        self.atool_text_right_files_p30_layer1.show()
                        self.atool_text_up_files_p30_layer2.show()
                        self.atool_text_down_files_p30_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_p30_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_p30_layer2

                    if self.achoice_p40.isChecked():
                        self.athreshold.append(40)
                        self.atool_text_left_files_p40_layer1.show()
                        self.atool_text_right_files_p40_layer1.show()
                        self.atool_text_up_files_p40_layer2.show()
                        self.atool_text_down_files_p40_layer2.show()
                        self.atext2_right_layer1 = self.atool_text_right_files_p40_layer1
                        self.atext2_down_layer2 = self.atool_text_down_files_p40_layer2

                if self.petat == "Scan":
                    self.scan_image_name_temp = QFileInfo(self.scan_image_name).fileName()
                    self.scan_image_filename = str(self.athreshold[self.aloop]) + "_" + self.scan_image_name_temp
                    copy(self.scan_image_name, os.path.join(work_directory, self.scan_image_filename))

                    if self.adouble_page.isChecked(): self.arg["layout"] = "double"
                    self.arg["threshold"] = self.athreshold[self.aloop]

                    self.aetat = "Scan"

                    docker.etat = "AutoPreprocess"
                    docker.preprocess(self.arg)
                    self.wait(self.scan_image_name_temp + "\n\n" + "Thickness: " + str(self.arg["threshold"]))
            else:
                if self.petat == "Scan":
                    if self.pvolume:
                        answer = QMessageBox.question(self,
                                                      lang.gettext("Message"),
                                                      lang.gettext("Preprocess all the volume images?"),
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if answer == QMessageBox.Yes:
                            pass
                        elif answer == QMessageBox.No:
                            self.pvolume = False
                        else:
                            return

                    if self.pvolume == False:
                        copy(self.scan_image_name, work_directory)
                    else:
                        for f in os.listdir(self.scan_folder_name):
                            if f.endswith(".tif"):
                                while True:
                                    ack = copy(os.path.join(self.scan_folder_name, f), work_directory)
                                    if ack.find(f): break

                    if self.aslider.value():
                        self.arg["threshold"] = self.aslider.value()
                    else:
                        self.arg["threshold"] = 0
                    if self.adouble_page.isChecked():
                        self.arg["layout"] = "double"

                    self.aetat = "Scan"

                    docker.etat = "AutoPreprocess"
                    docker.preprocess(self.arg)
                    self.scan_image_filename = QFileInfo(self.scan_image_name).fileName()

                    if self.pvolume:
                        txt = self.scan_folder_name + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                        self.pvolume = False
                    else:
                        txt = self.scan_image_filename + "\n\n" + "Thickness: " + str(self.arg["threshold"])
                    self.wait(txt)

        elif self.aetat == "Result":
            if self.abook_button.isChecked():
                self.arg["page_type"] = "book"
                self.arg["line_break_method"] = "line_cut"
                if self.aclearhr.isChecked(): self.arg["clear_hr"] = True
            if self.alowink.isChecked(): self.arg["low_ink"] = True
            if self.adial.value(): self.arg["break_width"] = self.adial.value() / 2

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
                self.presult_image_layer1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.presult_image_layer2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.oscan_image_layer1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.oscan_image_layer2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
                self.del_files()

                self.petat = "Result"

                if self.oetat == "Ocr":
                    self.otext_layer1.hide()
                    self.otext_layer2.hide()
                    self.otext_layer1.clear()
                    self.otext_layer2.clear()
                    self.oetat = ""

                if self.aetat == "Ocr":
                    self.atext_alayer1.hide()
                    self.atext_alayer2.hide()
                    self.atext_alayer1.clear()
                    self.atext_alayer2.clear()
                    self.aetat = ""

                self.ascan_image_layer1.clear()
                self.ascan_image_layer2.clear()

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
            if self.aswitch_layer.currentWidget() == self.amanual_place1:
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
        self.otext_layer1.setText(data)
        self.otext_layer2.setText(data)
        self.otext_layer1.show()
        self.otext_layer2.show()
        self.atext_alayer1.setText(data)
        self.atext_alayer2.setText(data)
        self.atext_alayer1.show()
        self.atext_alayer2.show()

    def copyOutput(self):
        copy("ocr_output.txt", str(self.arg["threshold"]) + "_ocr_output.txt")
        self.del_out_dir()

    def copyFile2QtextAuto(self):
        with open("0_ocr_output.txt", "r", encoding="utf-8") as file:
            data = file.read()
        self.atext_left_layer1.setText(data)
        self.atext_up_layer2.setText(data)
        self.atool_text_left_files_0_layer1.setChecked(True)
        self.atool_text_up_files_0_layer2.setChecked(True)

        if len(self.athreshold) > 1:
            with open(str(self.arg["threshold"]) + "_ocr_output.txt", "r", encoding="utf-8") as file:
                data = file.read()
            self.atext_right_layer1.setText(data)
            self.atext_down_layer2.setText(data)
            self.atext2_right_layer1.setChecked(True)
            self.atext2_down_layer2.setChecked(True)

        self.azone_layer1.show()
        self.azone_layer2.show()

    def lang(self, e):
        global lang
        answer = QMessageBox.question(self,
                lang.gettext("Message"), lang.gettext("Namsel Ocr need to Restart to apply the changes..."),
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            lang = languages[e.iconText()]
            qApp.exit(2)

    def restart(self):
        self.del_files()
        self.del_out_dir()
        qApp.exit(1)

    def del_files(self):
        for f in os.listdir(work_directory):
            if not os.path.isdir(f):
                os.remove(f)

    def del_out_dir(self):
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

