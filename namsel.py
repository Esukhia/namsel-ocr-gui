from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from shutil import copy, rmtree
from tempfile import gettempdir
import os, sys

import gettext

languages = {
    "bo":gettext.translation("namsel-ocr-gui", localedir="locales", languages=["bo"]),
    "en":gettext.translation("namsel-ocr-gui", localedir="locales", languages=["en"]),
    "fr":gettext.translation("namsel-ocr-gui", localedir="locales", languages=["fr"]),
    "zh_CN":gettext.translation("namsel-ocr-gui", localedir="locales", languages=["zhs"]),
    "zh_TW":gettext.translation("namsel-ocr-gui", localedir="locales", languages=["zht"]),
}
lang = languages["en"]
work_directory = gettempdir() + "/namsel"

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
        self.docker_process = QProcess()
        self.docker_preprocess = QProcess()
        self.docker_ocr = QProcess()
        self.docker_preprocess_auto = QProcess()
        self.docker_ocr_auto = QProcess()

        if "\\" in work_directory:
            docker_namsel_path = "////" + work_directory.replace("\\", "/").replace(":/", "/")
        self.docker_process.start("docker run -itd --name "+namsel_ocr_container+" -v "\
                                  +docker_namsel_path+":/home/namsel-ocr/data "\
                                  +namsel_ocr_image+" bash")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print(lang.gettext("\nDocker Namsel Ocr is now running!\n"))

    def preprocess(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print(lang.gettext("\nPreprocess is running..."))
        #print(arg)
        self.docker_preprocess.start("docker exec namsel-ocr ./namsel-ocr preprocess"+arg)

    def ocr(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print(lang.gettext("\nOcr is running..."))
        #print(arg)
        self.docker_ocr.start("docker exec namsel-ocr ./namsel-ocr recognize-volume --format text"+arg)

    def preprocessAuto(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print(lang.gettext("\nPreprocess is running..."))
        #print(arg)
        self.docker_preprocess_auto.start("docker exec namsel-ocr ./namsel-ocr preprocess"+arg)

    def ocrAuto(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print(lang.gettext("\nOcr is running..."))
        #print(arg)
        self.docker_ocr_auto.start("docker exec namsel-ocr ./namsel-ocr recognize-volume --format text"+arg)

    def stop(self):
        print(lang.gettext("\nStopping the container..."))
        self.docker_process.start("docker stop namsel-ocr")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print(lang.gettext("The container has been stopped!\n"))

    def kill(self):
        print(lang.gettext("\nKilling the container..."))
        self.docker_process.start("docker rm -f namsel-ocr")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print(lang.gettext("The container has been killed!"))

class NamselOcr(QMainWindow):
    global docker

    def __init__(self, p_arg={"threshold":"", "layout":""},\
                 o_arg={"page_type":"pecha", "line_break_method":"line_cluster",\
                        "clear_hr":"", "low_ink":"", "break_width":""},\
                 *args, **kwargs):
        super(NamselOcr, self).__init__(*args, **kwargs)

        self.petat = self.oetat = self.aetat = ""
        self.pvolume = False
        self.p_arg = p_arg
        self.o_arg = o_arg

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
        self.new_subaction.setStatusTip(lang.gettext("Open a new windows"))
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
        self.auto_subaction.setStatusTip(lang.gettext("open the auto mode windows"))
        self.prep_subaction = QAction(lang.gettext("Preprocess mode"), self)
        self.prep_subaction.setStatusTip(lang.gettext("open the preprocess mode windows"))
        self.ocr_subaction = QAction(lang.gettext("Ocr mode"), self)
        self.ocr_subaction.setStatusTip(lang.gettext("open the ocr mode windows"))
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
        self.aoption_layout.addWidget(self.adial_group)
        self.aoption_layout.addWidget(self.arun_group)

        self.aoption_widget = QWidget()
        self.aoption_widget.setFixedHeight(130)
        self.aoption_widget.setLayout(self.aoption_layout)

                    # Image-text
                        # Scan image widget
        self.ascan_image_layer1 = QLabel()
        self.ascan_image_layer2 = QLabel()
        self.ascan_image_layer1.setStatusTip(lang.gettext("The scan image"))
        self.ascan_image_layer2.setStatusTip(lang.gettext("The scan image"))

                        # Result text widget
        self.atext_layer1 = QTextEdit()
        self.atext_layer2 = QTextEdit()
        self.atext_layer1.setStatusTip(lang.gettext("The ocr result"))
        self.atext_layer2.setStatusTip(lang.gettext("The ocr result"))
        self.atext_layer1.setFont(self.font)
        self.atext_layer2.setFont(self.font)
        self.atext_layer1.setFontPointSize(18)
        self.atext_layer2.setFontPointSize(18)
        self.atext_layer1.hide()
        self.atext_layer2.hide()

                    # Image-text layout and widget
        self.aimagetext_hlayout = QHBoxLayout()
        self.aimagetext_vlayout = QVBoxLayout()

        self.aimagetext_vlayout.addWidget(self.ascan_image_layer1)
        self.aimagetext_vlayout.addWidget(self.atext_layer1)

        self.aimagetext_hlayout.addWidget(self.ascan_image_layer2)
        self.aimagetext_hlayout.addWidget(self.atext_layer2)

        self.aimagetext_widget = QWidget()
        self.aimagetext_vwidget = QWidget()
        self.aimagetext_hwidget = QWidget()

        self.aimagetext_vwidget.setLayout(self.aimagetext_vlayout)
        self.aimagetext_hwidget.setLayout(self.aimagetext_hlayout)

        self.aimagetext_staklayout = QStackedLayout(self.aimagetext_widget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_vwidget)
        self.aimagetext_staklayout.addWidget(self.aimagetext_hwidget)
        self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_vwidget)

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

        # Volume Yes/No dialog
        self.pvolume_dialogbuttonbox = QDialogButtonBox()
        self.pvolume_dialogbuttonbox.addButton(lang.gettext("&Yes"), QDialogButtonBox.YesRole)
        self.pvolume_dialogbuttonbox.addButton(lang.gettext("&No"), QDialogButtonBox.NoRole)
        self.pvolume_dialogbuttonbox.setWindowTitle(lang.gettext("Preprocess all the volume images?"))
        self.pvolume_dialogbuttonbox.setFixedSize(self.x_wsize / 2, self.y_wsize / 6)
        self.pvolume_dialogbuttonbox.setCenterButtons(True)
        self.pvolume_dialogbuttonbox.setWindowModality(Qt.ApplicationModal)

        # Restart to Change the language
        self.restart_dialogbuttonbox = QDialogButtonBox()
        self.restart_dialogbuttonbox.addButton(lang.gettext("&Yes"), QDialogButtonBox.YesRole)
        self.restart_dialogbuttonbox.addButton(lang.gettext("&No"), QDialogButtonBox.NoRole)
        self.restart_dialogbuttonbox.setWindowTitle(lang.gettext("Namsel Ocr need to Restart to apply the changes..."))
        self.restart_dialogbuttonbox.setFixedSize(self.x_wsize / 2, self.y_wsize / 6)
        self.restart_dialogbuttonbox.setCenterButtons(True)
        self.restart_dialogbuttonbox.setWindowModality(Qt.ApplicationModal)

        # Links between signals and slots
            # Menu
        self.new_subaction.triggered.connect(self.init)
        self.exit_subaction.triggered.connect(self.close)
        self.lang_subactiongroup.triggered.connect(self.lang)
        self.restart_dialogbuttonbox.clicked.connect(self.lang)
        #self.help_subaction.triggered.connect(self.test)
        # self.about_subaction.triggered.connect(self.ready)
            # Mode auto
        # Preprocess
        self.auto_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.autopage_widget))
        self.adial.valueChanged.connect(lambda x: self.alcd.display(x / 2) if x else self.alcd.display("Off"))
        self.abook_button.toggled.connect(self.abook)
        self.arun_button.released.connect(self.autoRun)
            # Preprocess
        self.prep_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.preprocesspage_widget))
        self.pslider.valueChanged.connect(self.plcd.display)
        self.pbook_button.toggled.connect(self.pbook)
        self.pdouble_page.toggled.connect(self.pdouble)
        self.open_file_subaction.triggered.connect(self.openScanImage)
        self.open_dir_subaction.triggered.connect(self.openScanDirImage)
        self.pvolume_dialogbuttonbox.clicked.connect(lambda x: self.preprocessRun(x.text() == lang.gettext("&Yes")))
        self.prun_button.released.connect(self.preprocessRun)
            # Ocr
        self.ocr_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.ocrpage_widget))
        self.odial.valueChanged.connect(lambda x: self.olcd.display(x/2) if x else self.olcd.display("Off"))
        self.obook_button.toggled.connect(self.obook)
        self.orun_button.released.connect(self.ocrRun)
                # Docker
        docker.docker_preprocess.finished.connect(self.preprocessFinished)
        docker.docker_ocr.finished.connect(self.ocrFinished)
        docker.docker_preprocess_auto.finished.connect(self.autoFinished)
        docker.docker_ocr_auto.finished.connect(self.autoFinished)

    def init(self):
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

    def lang(self, e):
        global lang
        if self.restart_dialogbuttonbox.isHidden():
            self.lang_temp = languages[e.iconText()]
            self.restart_dialogbuttonbox.show()
            return
        elif e.text() == lang.gettext("&Yes"):
            lang = self.lang_temp
            qApp.exit(2)
        else:
            self.restart_dialogbuttonbox.hide()
            return

    def pbook(self, e):
        if e:
            if not self.pdouble_page.isChecked():
                self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)
            self.pd_widget.show()
            self.obook_button.setChecked(True)
            self.abook_button.setChecked(True)
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
            self.pd_widget.hide()
            self.opecha_button.setChecked(True)
            self.apecha_button.setChecked(True)

    def pdouble(self, e):
        if e:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)

    def obook(self, e):
        if e:
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_hwidget)
            self.od_widget.show()
            self.pbook_button.setChecked(True)
            self.abook_button.setChecked(True)
        else:
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_vwidget)
            self.od_widget.hide()
            self.ppecha_button.setChecked(True)
            self.apecha_button.setChecked(True)

    def abook(self, e):
        if e:
            self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_hwidget)
            self.adc_widget.show()
            self.pbook_button.setChecked(True)
            self.obook_button.setChecked(True)
        else:
            self.aimagetext_staklayout.setCurrentWidget(self.aimagetext_vwidget)
            self.adc_widget.hide()
            self.ppecha_button.setChecked(True)
            self.opecha_button.setChecked(True)

    def wait(self, label):
        self.progress.setLabelText(label)
        self.progress.show()

    def openScanImage(self, folder=""):
        if not folder: folder = ""

        self.scan_image_name, _ = QFileDialog.getOpenFileName(self, lang.gettext("Open the source scan image..."),\
                                                              folder, lang.gettext("Image files (*.tif)"))
        if self.scan_image_name:
            if self.petat == "Result":
                self.presult_image_layer1.clear()
                self.presult_image_layer2.clear()
                self.del_out_dir()

            if self.aetat == "Ocr":
                self.atext_layer1.hide()
                self.atext_layer2.hide()
                self.atext_layer1.clear()
                self.atext_layer2.clear()
                self.del_out_dir()
                os.remove(os.path.join(work_directory, "ocr_output.txt"))
            if self.oetat == "Ocr":
                self.otext_layer1.hide()
                self.otext_layer2.hide()
                self.otext_layer1.clear()
                self.otext_layer2.clear()
                self.del_files()
            self.psimage = QPixmap(self.scan_image_name)
            self.pscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.pscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.ascan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.ascan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.petat = "Scan"

    def openScanDirImage(self):
        self.scan_folder_name = QFileDialog.getExistingDirectory(self, lang.gettext(
            "Open a directory containing the scan images of a volume..."), "")
        if self.scan_folder_name:
            self.pvolume = True
            self.openScanImage(self.scan_folder_name)

    def volume(self, e):
        if e.text() == "&Yes":
            self.preprocess(True)
        else:
            self.preprocess()

    def preprocessRun(self, all=""):
        if self.petat == "" or self.petat == "Result":
            self.openScanImage()

        elif self.petat == "Scan":
            if self.pvolume:
                self.pvolume = False
                self.pvolume_dialogbuttonbox.show()
                return
            elif self.pvolume_dialogbuttonbox.isVisible():
                self.pvolume_dialogbuttonbox.hide()

            self.wait(lang.gettext("Preprocess is running..."))

            if not all:
                copy(self.scan_image_name, work_directory)
            else:
                for f in os.listdir(self.scan_folder_name):
                    if f.endswith(".tif"):
                        while True:
                            ack = copy(os.path.join(self.scan_folder_name, f), work_directory)
                            if ack.find(f): break

            if self.pslider.value(): self.p_arg["threshold"] = self.pslider.value()
            if self.pdouble_page.isChecked(): self.p_arg["layout"] = "double"

            docker.preprocess(self.p_arg)

    def preprocessFinished(self):
        self.scan_image_filename = QFileInfo(self.scan_image_name).fileName()
        if os.path.isdir("./out") and os.path.isfile("./" + self.scan_image_filename):
            os.chdir("./out")
            self.primage = QPixmap(self.scan_image_filename)
            self.presult_image_layer1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.presult_image_layer2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            os.chdir(work_directory)
            self.del_files()

            self.p_arg = {"threshold": "", "layout": ""}
            self.petat = "Result"

        docker.docker_preprocess.close()
        print(lang.gettext("...is now finished!"))
        self.progress.cancel()

    def ocrRun(self, o_arg=[]):
        if self.petat == "" or self.oetat == "Ocr":
            self.openScanImage()

        if self.petat == "Scan":
            copy(self.scan_image_name, work_directory)

        if self.obook_button.isChecked():
            self.o_arg["page_type"] = "book"
            self.o_arg["line_break_method"] = "line_cut"
            if self.oclearhr.isChecked(): self.o_arg["clear_hr"] = True
        if self.olowink.isChecked(): self.o_arg["low_ink"] = True
        if self.odial.value(): self.o_arg["break_width"] = self.odial.value()/2

        self.wait(lang.gettext("Ocr is running..."))

        docker.ocr(self.o_arg)

    def ocrFinished(self):
        self.o_arg = {"page_type":"pecha", "line_break_method":"line_cluster",\
                      "clear_hr":"", "low_ink":"", "break_width":""}
        self.oetat = "Ocr"
        docker.docker_ocr.close()
        print(lang.gettext("...is now finished!"))
        self.copyFile2Qtext("ocr_output.txt")
        self.otext_layer1.show()
        self.otext_layer2.show()
        self.progress.cancel()

    def autoRun(self, o_arg=[]):
        if self.aetat == "Ocr" or (self.aetat != "Scan" and self.petat != "Scan"):
            self.openScanImage()

        if self.aetat != "Result":
            if self.petat == "Scan":
                copy(self.scan_image_name, work_directory)

            if self.adouble_page.isChecked(): self.p_arg["layout"] = "double"

            self.wait(lang.gettext("Autoprocess is running..."))
            self.aetat = "Scan"

            docker.preprocessAuto(self.p_arg)
        else:
            if self.abook_button.isChecked():
                self.o_arg["page_type"] = "book"
                self.o_arg["line_break_method"] = "line_cut"
                if self.aclearhr.isChecked(): self.o_arg["clear_hr"] = True
            if self.alowink.isChecked(): self.o_arg["low_ink"] = True
            if self.adial.value(): self.o_arg["break_width"] = self.adial.value() / 2

            docker.ocrAuto(self.o_arg)


    def autoFinished(self):
        if self.aetat == "Scan":
            self.scan_image_filename = QFileInfo(self.scan_image_name).fileName()
            if os.path.isdir("./out") and os.path.isfile("./" + self.scan_image_filename):
                self.del_files()

                self.p_arg = {"threshold": "", "layout": ""}

            docker.docker_preprocess_auto.close()
            print(lang.gettext("...is now finished!"))

            self.aetat = "Result"
            self.autoRun()

        elif self.aetat == "Result":
            self.o_arg = {"page_type": "pecha", "line_break_method": "line_cluster", \
                          "clear_hr": "", "low_ink": "", "break_width": ""}
            self.aetat = "Ocr"
            docker.docker_ocr_auto.close()
            print(lang.gettext("...is now finished!"))
            self.copyFile2QtextAuto("ocr_output.txt")
            self.atext_layer1.show()
            self.atext_layer2.show()
            self.progress.cancel()
























    def copyFile2Qtext(self, f):
        with open(f, "r", encoding="utf-8") as file:
            data = file.read()
        self.otext_layer1.setText(data)
        self.otext_layer2.setText(data)

    def copyFile2QtextAuto(self, f):
        with open(f, "r", encoding="utf-8") as file:
            data = file.read()
        self.atext_layer1.setText(data)
        self.atext_layer2.setText(data)

def killEnvironment():
    global docker, work_directory

    docker.stop()
    docker.kill()

    os.chdir("/")
    if os.path.isdir(work_directory):
        rmtree(work_directory)

if __name__ == "__main__":
    setEnvironment()

    while True:
        app = QApplication(sys.argv)

        namsel_ocr = NamselOcr()
        namsel_ocr.show()

        rcode = app.exec_()
        if not rcode: break
        else:
            del app, namsel_ocr

    killEnvironment()