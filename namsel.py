from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from shutil import copyfile, rmtree
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

        if "\\" in work_directory:
            docker_namsel_path = "////" + work_directory.replace("\\", "/").replace(":/", "/")
        self.docker_process.start("docker run -itd --name "+namsel_ocr_container+" -v "\
                                  +docker_namsel_path+":/home/namsel-ocr/data "\
                                  +namsel_ocr_image+" bash")
        self.docker_process.waitForFinished()
        self.docker_process.close()
        print("\nThe container Namsel Ocr is now running!\n")

    def preprocess(self, arg=[]):
        arg = " ".join(arg)
        print("\nPreprocess is running...")
        self.docker_preprocess.start("docker exec namsel-ocr ./preprocess "+arg)

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

    def __init__(self, p_arg=[], *args, **kwargs):
        super(NamselOcr, self).__init__(*args, **kwargs)

        self.etat = 0
        self.p_arg = p_arg

        # Title
        self.setWindowTitle("Namsel Ocr")

        # Set the statusbar on
        self.setStatusBar(QStatusBar(self))

        # Size : 70 % of the screen
        self.dw = QDesktopWidget()
        self.x_wsize = self.dw.width() * 0.5
        self.y_wsize = self.dw.height() * 0.5
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
                # Option
                        # Pecha - Book radiobuttons
        self.ppecha_button = QRadioButton("Pecha")
        self.ppecha_button.setStatusTip("The scan image is a pecha")
        self.pbook_button = QRadioButton("Book")
        self.pbook_button.setStatusTip("The scan image is a book")
        self.ppecha_button.setCheckable(True)
        self.pbook_button.setCheckable(True)
        self.ppecha_button.setChecked(True)

        """ppecha_button = QPushButton("Pecha")
        pbook_button = QPushButton("Book")
        
        ppecha_book_button_group = QButtonGroup()
        ppecha_book_button_group.addButton(ppecha_button)
        ppecha_book_button_group.addButton(pbook_button)
        ppecha_book_button_group.setExclusive(True)"""

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

                        # Run
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
                    # Option layout
        self.option_layout = QHBoxLayout()
        self.option_layout.addWidget(self.ppecha_book_group)
        self.option_layout.addWidget(self.pslider_group)
        self.option_layout.addWidget(self.prun_group)
                    # Option widget
        self.option_widget = QWidget()
        self.option_widget.setFixedHeight(100)
        self.option_widget.setLayout(self.option_layout)

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

                # Image layout
        self.image_hlayout = QHBoxLayout()
        self.image_vlayout = QVBoxLayout()

        self.image_vlayout.addWidget(self.pscan_image_layer1)
        self.image_vlayout.addWidget(self.presult_image_layer1)

        self.image_hlayout.addWidget(self.pscan_image_layer2)
        self.image_hlayout.addWidget(self.presult_image_layer2)

        self.image_widget = QWidget()
        self.image_vwidget = QWidget()
        self.image_hwidget = QWidget()

        self.image_vwidget.setLayout(self.image_vlayout)
        self.image_hwidget.setLayout(self.image_hlayout)

        self.image_staklayout = QStackedLayout(self.image_widget)
        self.image_staklayout.addWidget(self.image_vwidget)
        self.image_staklayout.addWidget(self.image_hwidget)
        self.image_staklayout.setCurrentWidget(self.image_vwidget)

        self.image_widget.setLayout(self.image_staklayout)

            # Page widget
        self.prep_layout = QVBoxLayout()
        self.prep_layout.addWidget(self.option_widget)
        self.prep_layout.addWidget(self.image_widget)

        self.page_widget = QWidget()
        self.page_widget.setLayout(self.prep_layout)

        # Rendering the page
        self.setCentralWidget(self.page_widget)

        # Waiting progress dialog
        self.progress = QProgressDialog(None, Qt.WindowTitleHint)
        self.progress.setWindowFlags(self.progress.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.progress.setCancelButton(None)
        self.progress.setWindowModality(Qt.ApplicationModal)
        self.progress.setLabelText("Processing...")
        self.progress.setRange(0, 0)
        self.progress.cancel()

                        # Links between signals and slots
        self.pslider.valueChanged.connect(self.plcd.display)
        self.pbook_button.toggled.connect(self.pbook)
        self.pdouble_page.toggled.connect(self.pdouble)
        self.open_file_subaction.triggered.connect(self.openScanImage)
        self.open_dir_subaction.triggered.connect(self.openScanDirImage)
        self.prun_button.released.connect(self.preprocessRun)

        self.new_subaction.triggered.connect(self.init)
        self.exit_subaction.triggered.connect(self.close)
        #self.help_subaction.triggered.connect(self.wait)
        #self.about_subaction.triggered.connect(self.ready)

        docker.docker_preprocess.finished.connect(self.preprocess_finished)

    def pbook(self, x):
        if x:
            if not self.pdouble_page.isChecked():
                self.image_staklayout.setCurrentWidget(self.image_hwidget)
            self.pdouble_page.show()
        else:
            self.image_staklayout.setCurrentWidget(self.image_vwidget)
            self.pdouble_page.hide()

    def pdouble(self, x):
        if x:
            self.image_staklayout.setCurrentWidget(self.image_vwidget)
        else:
            self.image_staklayout.setCurrentWidget(self.image_hwidget)

    def init(self):
        self.etat = 0
        self.p_arg.clear()
        self.ppecha_button.setChecked(True)
        self.pslider.setValue(0)
        self.pdouble_page.setChecked(False)

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
        self.scan_image_name, _ = QFileDialog.getOpenFileName(self, "Open the source scan image...", folder, "Image files (*.tif)")
        if self.scan_image_name:
            if self.etat == "Result":
                self.presult_image_layer1.clear()
                self.presult_image_layer2.clear()
                self.del_out_dir()
            self.psimage = QPixmap(self.scan_image_name)
            self.pscan_image_layer1.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.pscan_image_layer2.setPixmap(self.psimage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.etat = "Scan"

    def openScanDirImage(self):
        self.scan_folder_name = QFileDialog.getExistingDirectory(self, "Open a directory containing the scan images of a volume...", "")
        if self.scan_folder_name:
            self.openScanImage(self.scan_folder_name)

    def preprocessRun(self):
        if self.etat == "Scan":
            self.scan_image_filename = QFileInfo(self.scan_image_name).fileName()
            copyfile(self.scan_image_name, self.scan_image_filename)

            self.p_arg.append(str(self.pslider.value()))
            if self.pdouble_page.isChecked():
                self.p_arg.append("1")
            self.wait()
            docker.preprocess(self.p_arg)
        else:
            self.openScanImage()

    def preprocess_finished(self):
        if os.path.isdir("./out") and os.path.isfile("./" + self.scan_image_filename):
            os.chdir("./out")
            self.primage = QPixmap(self.scan_image_filename)
            self.presult_image_layer1.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            self.presult_image_layer2.setPixmap(self.primage.scaled(self.x_wsize, self.y_wsize, Qt.KeepAspectRatio))
            os.chdir(work_directory)
            self.del_files()

            self.p_arg.clear()
            self.etat = "Result"

        docker.docker_preprocess.close()
        print("...is now finished!")

        self.progress.cancel()

    def wait(self):
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