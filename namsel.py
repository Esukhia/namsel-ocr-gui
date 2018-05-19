from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from shutil import copy, rmtree
from tempfile import gettempdir
import os, sys

work_directory = gettempdir() + "/namsel"

def setEnvironment():
    global work_directory, docker

    if os.path.isdir(work_directory):
        rmtree(work_directory)
    os.mkdir(work_directory)
    os.chdir(work_directory)

    docker = Docker("thubtenrigzin/docker-namsel-ocr:latest", "namsel-ocr")

class Docker(object):
    global namsel_ocr, work_directory

    def __init__(self, namsel_ocr_image, namsel_ocr_container):
        self.docker_process = QProcess()
        self.docker_preprocess = QProcess()
        self.docker_ocr = QProcess()

        if "\\" in work_directory:
            docker_namsel_path = "////" + work_directory.replace("\\", "/").replace(":/", "/")
        self.docker_process.start("docker run -itd --name "+namsel_ocr_container+" -v "\
                                  +docker_namsel_path+":/home/namsel-ocr/data "\
                                  +namsel_ocr_image+" bash")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print("\nDocker Namsel Ocr is now running!\n")

    def preprocess(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print("\nPreprocess is running...")
        #print(arg)
        self.docker_preprocess.start("docker exec namsel-ocr ./namsel-ocr preprocess"+arg)

    def ocr(self, arg={}):
        arg = " "+" ".join(["--"+k+" "+str(v) for k, v in arg.items() if v])
        print("\nOcr is running...")
        #print(arg)
        self.docker_ocr.start("docker exec namsel-ocr ./namsel-ocr recognize-volume --format text"+arg)

    def stop(self):
        print("\nStopping the container...")
        self.docker_process.start("docker stop namsel-ocr")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print("The container has been stopped!\n")

    def kill(self):
        print("\nKilling the container...")
        self.docker_process.start("docker rm -f namsel-ocr")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print("The container has been killed!")

class NamselOcr(QMainWindow):
    global docker, work_directory

    def __init__(self, p_arg={"threshold":"", "layout":""},\
                 o_arg={"page_type":"pecha", "line_break_method":"line_cluster",\
                        "clear_hr":"", "low_ink":"", "break_width":""},\
                 *args, **kwargs):
        super(NamselOcr, self).__init__(*args, **kwargs)

        self.petat = self.oetat = ""
        self.prun_etat = self.pvolume = False
        self.p_arg = p_arg
        self.o_arg = o_arg

        # Title
        self.setWindowTitle("Namsel Ocr")

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
        self.file_menu = self.menu.addMenu("&File")
        self.new_subaction = QAction("New", self)
        self.new_subaction.setStatusTip("Open a new windows")
        self.open_file_subaction = QAction("open an image...", self)
        self.open_file_subaction.setStatusTip("Open a scan image file")
        self.open_dir_subaction = QAction("Select a directory...", self)
        self.open_dir_subaction.setStatusTip("Select a directory containing the images of a volume")
        self.exit_subaction = QAction("Exit", self)
        self.exit_subaction.setStatusTip("Exit Namsel OCR")
        self.file_menu.addAction(self.new_subaction)
        self.file_menu.addAction(self.open_file_subaction)
        self.file_menu.addAction(self.open_dir_subaction)
        self.file_menu.addAction(self.exit_subaction)
            # Edit
        self.edit_menu = self.menu.addMenu("&Edit")
        self.pref_subaction = QAction("Preferences...", self)
        self.pref_subaction.setStatusTip("Preprocess and Ocr settings...")
        self.edit_menu.addAction(self.pref_subaction)
            # Options
        self.option_menu = self.menu.addMenu("&Option")
                # Modes
        self.mode_subactiongroup = QActionGroup(self)
        self.prep_subaction = QAction("Preprocess mode", self)
        self.prep_subaction.setStatusTip("open the preprocess mode windows")
        self.ocr_subaction = QAction("Ocr mode", self)
        self.ocr_subaction.setStatusTip("open the ocr mode windows")
        self.prep_subaction.setCheckable(True)
        self.ocr_subaction.setCheckable(True)
        self.mode_subactiongroup.addAction(self.prep_subaction)
        self.mode_subactiongroup.addAction(self.ocr_subaction)
        self.prep_subaction.setChecked(True)
        self.option_menu.addActions(self.mode_subactiongroup.actions())
        self.option_menu.addSeparator()
                # Language
        self.lang_submenu = self.option_menu.addMenu("&Language")
        self.lang_subactiongroup = QActionGroup(self)
                    #Tibetan
        self.bo_lang_subaction = QAction("བོད་ཡིག", self)
        self.font = QFont()
        self.font.setFamily('Microsoft Himalaya')
        self.bo_lang_subaction.setFont(self.font)
                    # Other languages
        self.en_lang_subaction = QAction("English", self)
        self.es_lang_subaction = QAction("Español", self)
        self.fr_lang_subaction = QAction("Français", self)
        self.zhs_lang_subaction = QAction("简体字", self)
        self.zht_lang_subaction = QAction("繁體字", self)
        self.bo_lang_subaction.setCheckable(True)
        self.en_lang_subaction.setCheckable(True)
        self.es_lang_subaction.setCheckable(True)
        self.fr_lang_subaction.setCheckable(True)
        self.zhs_lang_subaction.setCheckable(True)
        self.zht_lang_subaction.setCheckable(True)
        self.lang_subactiongroup.addAction(self.bo_lang_subaction)
        self.lang_subactiongroup.addAction(self.en_lang_subaction)
        self.lang_subactiongroup.addAction(self.fr_lang_subaction)
        self.lang_subactiongroup.addAction(self.zhs_lang_subaction)
        self.lang_subactiongroup.addAction(self.zht_lang_subaction)
        self.en_lang_subaction.setChecked(True)
        self.lang_submenu.addActions(self.lang_subactiongroup.actions())
            # ?
        self.help_menu = self.menu.addMenu("&?")
        self.about_subaction = QAction("About...", self)
        self.about_subaction.setStatusTip("Version & credits of Namsel Ocr")
        self.help_menu.addAction(self.about_subaction)
        self.help_subaction = QAction("help...", self)
        self.help_subaction.setStatusTip("Some useful helps")
        self.help_menu.addAction(self.help_subaction)


        # Page
            # Preprocess & Ocr page
                # Preprocess page
                    # Option
                        # Pecha - Book radiobuttons
        self.ppecha_button = QRadioButton("Pecha")
        self.ppecha_button.setStatusTip("The scan image is a pecha")
        self.pbook_button = QRadioButton("Book")
        self.pbook_button.setStatusTip("The scan image is a book")
        self.ppecha_button.setCheckable(True)
        self.pbook_button.setCheckable(True)
        self.ppecha_button.setChecked(True)

        self.ppecha_book_layout = QVBoxLayout()
        self.ppecha_book_layout.addWidget(self.ppecha_button)
        self.ppecha_book_layout.addWidget(self.pbook_button)

        self.ppecha_book_group = QGroupBox()
        self.ppecha_book_group.setLayout(self.ppecha_book_layout)

                        # Label and the thickness value
        self.psliderlabel_val = QLabel("Thickness: ")
        self.plcd = QLCDNumber()
        self.plcd.setStatusTip("The thickness value during the preprocess")
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
        self.pslider.setStatusTip("Set the thickness of the scan image")

        self.pslider_layout = QVBoxLayout()
        self.pslider_layout.addLayout(self.pslider_label_num_layout)
        self.pslider_layout.addWidget(self.pslider)

        self.pslider_group = QGroupBox()
        self.pslider_group.setLayout(self.pslider_layout)

                        # Run the Preprocess
        self.pdouble_page = QCheckBox("Double page")
        self.pdouble_page.setStatusTip("The scan image is a double page")
        self.pdouble_page.setVisible(False)
        self.prun_button = QPushButton("Run")
        self.prun_button.setStatusTip("Run the preprocess")

        self.prun_layout = QVBoxLayout()
        self.prun_layout.addWidget(self.pdouble_page)
        self.prun_layout.addWidget(self.prun_button)

        self.prun_group = QGroupBox()
        self.prun_group.setLayout(self.prun_layout)

                    # Option layout & widget
        self.poption_layout = QHBoxLayout()
        self.poption_layout.addWidget(self.ppecha_book_group)
        self.poption_layout.addWidget(self.pslider_group)
        self.poption_layout.addWidget(self.prun_group)

        self.poption_widget = QWidget()
        self.poption_widget.setFixedHeight(100)
        self.poption_widget.setLayout(self.poption_layout)

                    # Image
                        # Scan image widget
        self.pscan_image_layer1 = QLabel()
        self.pscan_image_layer2 = QLabel()
        self.pscan_image_layer1.setStatusTip("The scan image")
        self.pscan_image_layer2.setStatusTip("The scan image")

                        # Result image widget
        self.presult_image_layer1 = QLabel()
        self.presult_image_layer2 = QLabel()
        self.presult_image_layer1.setStatusTip("The result 'scantailored' image")
        self.presult_image_layer2.setStatusTip("The result 'scantailored' image")

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
        self.opecha_button = QRadioButton("Pecha")
        self.opecha_button.setStatusTip("The scan image is a pecha")
        self.obook_button = QRadioButton("Book")
        self.obook_button.setStatusTip("The scan image is a book")
        self.opecha_button.setCheckable(True)
        self.obook_button.setCheckable(True)
        self.opecha_button.setChecked(True)

        self.opecha_book_layout = QVBoxLayout()
        self.opecha_book_layout.addWidget(self.opecha_button)
        self.opecha_book_layout.addWidget(self.obook_button)

        self.opecha_book_group = QGroupBox()
        self.opecha_book_group.setLayout(self.opecha_book_layout)

                        # Low ink
        self.olowink = QCheckBox("Low ink")
        self.olowink.setStatusTip("Check if the scan image is a bit of low quality")

        self.olowink_layout = QVBoxLayout()
        self.olowink_layout.addWidget(self.olowink)

        self.olowink_group = QGroupBox()
        self.olowink_group.setLayout(self.olowink_layout)

                        # Label and the dial value
        self.odialabel_val = QLabel("Break width: ")
        self.olcd = QLCDNumber()
        self.olcd.setStatusTip("The break-Width value")
        self.olcd.setSegmentStyle(QLCDNumber.Flat)
        self.olcd.setFixedWidth(40)
        self.olcd.display("Off")

        self.odial_label_num_layout = QHBoxLayout()
        self.odial_label_num_layout.addWidget(self.odialabel_val)
        self.odial_label_num_layout.addWidget(self.olcd)
        self.odial_label_num_layout.setAlignment(Qt.AlignCenter)

                        # QDial
        self.odial = QDial()
        self.odial.setRange(0, 8)
        self.odial.setNotchesVisible(True)
        self.odial.setStatusTip("To controls how horizontally-connected stacks will be segmented")

        self.odial_layout = QHBoxLayout()
        self.odial_layout.addLayout(self.odial_label_num_layout)
        self.odial_layout.addWidget(self.odial)

        self.odial_group = QGroupBox()
        self.odial_group.setLayout(self.odial_layout)


                        # Run the Ocr
        self.oclearhr = QCheckBox("Clear HR")
        self.oclearhr.setStatusTip("The scan image is a double page")
        self.oclearhr.setVisible(False)
        self.orun_button = QPushButton("Run")
        self.orun_button.setStatusTip("Run the ocr")

        self.orun_layout = QVBoxLayout()
        self.orun_layout.addWidget(self.oclearhr)
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
        self.ooption_widget.setFixedHeight(100)
        self.ooption_widget.setLayout(self.ooption_layout)

                    # Image-text
                        # Scan image widget
        self.oscan_image_layer1 = QLabel()
        self.oscan_image_layer2 = QLabel()
        self.oscan_image_layer1.setStatusTip("The scan image")
        self.oscan_image_layer2.setStatusTip("The scan image")

                        # Result text widget
        self.otext_layer1 = QTextEdit()
        self.otext_layer2 = QTextEdit()
        self.otext_layer1.setStatusTip("The ocr result")
        self.otext_layer2.setStatusTip("The ocr result")
        self.otext_layer1.setFont(self.font)
        self.otext_layer2.setFont(self.font)
        self.otext_layer1.setFontPointSize(18)
        self.otext_layer2.setFontPointSize(18)

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
        self.page_staklayout.addWidget(self.preprocesspage_widget)
        self.page_staklayout.addWidget(self.ocrpage_widget)
        self.page_staklayout.setCurrentWidget(self.preprocesspage_widget)

        # Showing the default page on screen
        self.setCentralWidget(self.page_widget)


        # Waiting progress dialog
        self.progress = QProgressDialog(None, Qt.WindowTitleHint)
        self.progress.setWindowFlags(self.progress.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.progress.setWindowTitle("Docker process")
        self.progress.setCancelButton(None)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setRange(0, 0)
        self.progress.cancel()

        # Volume Yes/No dialog
        self.pvolume_dialogbuttonbox = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.pvolume_dialogbuttonbox.setWindowTitle("Preprocess all the volume images?")
        self.pvolume_dialogbuttonbox.setFixedSize(self.x_wsize / 2, self.y_wsize / 6)
        self.pvolume_dialogbuttonbox.setCenterButtons(True)
        self.pvolume_dialogbuttonbox.setWindowModality(Qt.ApplicationModal)

        # Links between signals and slots
            # Menu
        self.new_subaction.triggered.connect(self.init)
        self.exit_subaction.triggered.connect(self.close)
        #self.help_subaction.triggered.connect(self.test)
        # self.about_subaction.triggered.connect(self.ready)
            # Preprocess
        self.pslider.valueChanged.connect(self.plcd.display)
        self.pbook_button.toggled.connect(self.pbook)
        self.pdouble_page.toggled.connect(self.pdouble)
        self.open_file_subaction.triggered.connect(self.openScanImage)
        self.open_dir_subaction.triggered.connect(self.openScanDirImage)
        self.pvolume_dialogbuttonbox.accepted.connect(lambda: self.preprocessRun(True))
        self.pvolume_dialogbuttonbox.rejected.connect(self.preprocessRun)
        self.prun_button.released.connect(self.preprocessRun)
            # Ocr
        self.odial.valueChanged.connect(lambda x: self.olcd.display(x/2) if x else self.olcd.display("Off"))
        self.prep_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.preprocesspage_widget))
        self.ocr_subaction.triggered.connect(lambda: self.page_staklayout.setCurrentWidget(self.ocrpage_widget))
        self.obook_button.toggled.connect(self.obook)
        self.orun_button.released.connect(self.ocrRun)
                # Docker
        docker.docker_preprocess.finished.connect(self.preprocessFinished)
        docker.docker_ocr.finished.connect(self.ocrFinished)

    def pbook(self, x):
        if x:
            if not self.pdouble_page.isChecked():
                self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)
            self.pdouble_page.show()
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
            self.pdouble_page.hide()

    def pdouble(self, x):
        if x:
            self.pimage_staklayout.setCurrentWidget(self.pimage_vwidget)
        else:
            self.pimage_staklayout.setCurrentWidget(self.pimage_hwidget)

    def obook(self, x):
        if x:
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_hwidget)
            self.oclearhr.show()
        else:
            self.oimagetext_staklayout.setCurrentWidget(self.oimagetext_vwidget)
            self.oclearhr.hide()

    def init(self):
        self.petat = self.oetat = ""
        self.prun_etat = self.pvolume = False
        self.p_arg= {"threshold":"", "layout":""}
        self.o_arg = {"page_type":"pecha", "line_break_method":"line_cluster",\
                      "clear_hr":"", "low_ink":"", "break_width":""}
        self.ppecha_button.setChecked(True)
        self.opecha_button.setChecked(True)
        self.pslider.setValue(0)
        self.pdouble_page.setChecked(False)
        self.olowink.setChecked(False)
        self.odial.setValue(0)
        self.oclearhr.setChecked(False)
        self.otext_layer1.clear()
        self.otext_layer2.clear()

        try:
            if self.scan_image_name:
                del self.scan_image_name
                self.pscan_image_layer1.clear()
                self.pscan_image_layer2.clear()
                del self.psimage
            if self.scan_image_filename:
                del self.scan_image_filename
                self.presult_image_layer1.clear()
                self.presult_image_layer2.clear()
                self.oscan_image_layer1.clear()
                self.oscan_image_layer2.clear()
                del self.primage
        except: pass

        try:
            if self.scan_folder_name:
                del self.scan_folder_name
        except: pass

        self.del_files()
        self.del_out_dir()

    def del_files(self):
        for f in os.listdir(work_directory):
            if not os.path.isdir(f):
                os.remove(f)

    def del_out_dir(self):
        if os.path.isdir(work_directory + "/out"):
            rmtree(work_directory + "/out")

    def openScanImage(self, folder=""):
        if not folder: folder = ""
        self.scan_image_name, _ = QFileDialog.getOpenFileName(self, "Open the source scan image...",\
                                                              folder, "Image files (*.tif)")
        if self.scan_image_name:
            if self.petat == "Result":
                self.presult_image_layer1.clear()
                self.presult_image_layer2.clear()
                self.del_out_dir()
            self.psimage = QPixmap(self.scan_image_name)
            self.pscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.pscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.oscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.petat = "Scan"
            if self.prun_etat == True:
                self.preprocessRun()
                self.prun_etat = False

    def openScanDirImage(self):
        self.scan_folder_name =\
            QFileDialog.getExistingDirectory(self, "Open a directory containing the scan images of a volume...", "")
        if self.scan_folder_name:
            self.pvolume = True
            self.openScanImage(self.scan_folder_name)

    def preprocessRun(self, all=""):
        if self.petat == "Scan":
            if self.pvolume:
                self.pvolume = False
                self.pvolume_dialogbuttonbox.show()
                return
            elif self.pvolume_dialogbuttonbox.isVisible():
                self.pvolume_dialogbuttonbox.hide()

            self.wait("Preprocess is running...")

            if not all:
                copy(self.scan_image_name, work_directory)
            else:
                for f in os.listdir(self.scan_folder_name):
                    if f.endswith(".tif"):
                        while True:
                            ack = copy(self.scan_folder_name+"/"+f, work_directory)
                            if ack.find(f): break

            if self.pslider.value(): self.p_arg["threshold"] = self.pslider.value()
            if self.pdouble_page.isChecked(): self.p_arg["layout"] = "double"

            docker.preprocess(self.p_arg)
        else:
            self.prun_etat = True
            self.openScanImage()

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
        print("...is now finished!")
        self.progress.cancel()

    def ocrRun(self, o_arg=[]):
        if self.obook_button.isChecked():
            self.o_arg["page_type"] = "book"
            self.o_arg["line_break_method"] = "line_cut"
            if self.oclearhr.isChecked(): self.o_arg["clear_hr"] = True
        if self.olowink.isChecked(): self.o_arg["low_ink"] = True
        if self.odial.value(): self.o_arg["break_width"] = self.odial.value()/2

        self.wait("Ocr is running...")
        docker.ocr(self.o_arg)

    def ocrFinished(self):
        self.o_arg = {"page_type":"pecha", "line_break_method":"line_cluster",\
                      "clear_hr":"", "low_ink":"", "break_width":""}
        self.oetat = "Ocr"
        docker.docker_ocr.close()
        print("...is now finished!")
        self.copyFile2Qtext("ocr_output.txt")
        self.progress.cancel()

    def copyFile2Qtext(self, f):
        with open(f, "r", encoding="utf-8") as file:
            data = file.read()
        self.otext_layer1.setText(data)
        self.otext_layer2.setText(data)

    def wait(self, label):
        self.progress.setLabelText(label)
        self.progress.show()

def killEnvironment():
    global docker, work_directory

    docker.stop()
    docker.kill()

    os.chdir("/")
    if os.path.isdir(work_directory):
        rmtree(work_directory)

setEnvironment()

app = QApplication(sys.argv)

namsel_ocr = NamselOcr()
namsel_ocr.show()

app.exec_()

killEnvironment()